from fastapi import WebSocket
import json
import logging
import base64
import asyncio
from datetime import datetime
import os
import sys

# Setup Django ORM for direct DB access
django_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../django_app'))
sys.path.insert(0, django_app_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    from agents.models import ConversationLog, ConversationSession
    from asgiref.sync import sync_to_async
    DJANGO_AVAILABLE = True
except Exception as e:
    logging.error(f"Failed to setup Django ORM: {e}")
    DJANGO_AVAILABLE = False

# Import AI agents
# FIX: Namespace collision between 'fastapi_app/agents' and 'django_app/agents'
# We must load the local VoiceAgent explicitly before modifying sys.path for Django
import importlib.util
voice_agent_path = os.path.join(os.path.dirname(__file__), 'agents', 'voice_agent.py')
spec = importlib.util.spec_from_file_location("voice_agent_module", voice_agent_path)
voice_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice_agent_module)
VoiceAgent = voice_agent_module.VoiceAgent

# from agents.voice_agent import VoiceAgent  # conflicting import
from integrations.ollama_client import OllamaClient
from integrations.deepgram_client import DeepgramClient
from integrations.cartesia_client import CartesiaClient

logger = logging.getLogger(__name__)

# Initialize shared clients once (not per-request)
_deepgram_client = None
_cartesia_client = None


def get_deepgram():
    global _deepgram_client
    if _deepgram_client is None:
        _deepgram_client = DeepgramClient()
    return _deepgram_client


def get_cartesia():
    global _cartesia_client
    if _cartesia_client is None:
        _cartesia_client = CartesiaClient()
    return _cartesia_client


# Silence timeout: auto-end session if no data for this many seconds
SILENCE_TIMEOUT_SECONDS = 15  # 15s timeout AFTER agent finishes speaking

# Transcript buffer delay: wait this long before processing accumulated transcripts
TRANSCRIPT_BUFFER_DELAY = 2.0  # 2 seconds


async def save_log_async(session_id, speaker, text, intent=None, latency=None):
    """Save conversation log to database asynchronously"""
    if not DJANGO_AVAILABLE:
        logger.warning("Django not available, skipping log save")
        return
        
    try:
        # We need to wrap DB operations in sync_to_async
        @sync_to_async
        def _create_log():
            try:
                # Debugging log
                # logger.info(f"Saving log for session {session_id}, speaker: {speaker}")
                
                session = ConversationSession.objects.get(id=session_id)
                ConversationLog.objects.create(
                    session=session,
                    speaker=speaker,
                    transcript=text,
                    intent=intent,
                    latency_ms=latency
                )
                
                # Update total turns
                session.total_turns += 1
                session.save()
            except ConversationSession.DoesNotExist:
                logger.error(f"Session {session_id} not found in DB - cannot log.")
            except Exception as e:
                logger.error(f"DB Log Error (Inside Sync): {e}", exc_info=True)
                
        await _create_log()
    except Exception as e:
        logger.error(f"Failed to save log (Async wrapper): {e}", exc_info=True)


async def process_transcript_buffer(websocket, voice_agent, cartesia, buffer_list, activity_state):
    """
    Process accumulated transcripts after a delay.
    This allows multiple speech segments to be combined into one turn.
    """
    if not buffer_list:
        return
    
    # Combine all buffered transcripts
    combined_transcript = " ".join(buffer_list)
    logger.info(f"Processing buffered transcript: {combined_transcript}")
    
    # Save USER log
    await save_log_async(voice_agent.session_id, 'user', combined_transcript)
    
    # Mark activity start
    activity_state['last_active'] = asyncio.get_event_loop().time()
    
    # ===== AI Agent Processing =====
    process_start = asyncio.get_event_loop().time()
    try:
        # Check for cancellation before expensive call
        # (This task might be cancelled if user interrupts)
        response = await voice_agent.process_turn(combined_transcript)
    except asyncio.CancelledError:
        logger.info("Agent processing cancelled (user interruption)")
        raise
    except Exception as e:
        logger.error(f"Agent processing failed: {e}", exc_info=True)
        response = "I'm sorry, I couldn't process that. Could you try again?"
    
    process_end = asyncio.get_event_loop().time()
    latency_ms = int((process_end - process_start) * 1000)
    
    logger.info(f"Agent response: {response[:100]}")
    
    # Save AGENT log
    await save_log_async(voice_agent.session_id, 'agent', response, latency=latency_ms)
    
    # Send text response
    try:
        await websocket.send_json({
            "type": "agent_response",
            "text": response,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
         logger.warning(f"Failed to send text response: {e}")
    
    # Mark activity after text response
    activity_state['last_active'] = asyncio.get_event_loop().time()
    
    # ===== Text-to-Speech =====
    try:
        # FIX: Use voice_id from agent config
        voice_id = voice_agent.agent_config.get('voice_id')
        logger.info(f"Synthesizing with voice_id: {voice_id}")
        
        # This is blocking, but if task is cancelled, it will stop
        audio_bytes = await cartesia.synthesize(response, voice_id=voice_id)
        
        if audio_bytes and len(audio_bytes) > 0:
            audio_base64_out = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({
                "type": "audio_response",
                "audio": audio_base64_out,
                "format": "wav",
                "timestamp": datetime.now().isoformat()
            })
            
            # ESTIMATE DURATION to delay timeout
            # Cartesia Sonic usually 16kHz or 24kHz, 16-bit mono.
            # Conservative estimate: 32000 bytes/sec (16kHz).
            # If we assume 32kB/s, we get a longer duration which is safer (prevents early timeout).
            estimated_duration_sec = len(audio_bytes) / 32000.0
            
            # Mark activity as "now + duration" so timeout counts from AFTER speech
            activity_state['last_active'] = asyncio.get_event_loop().time() + estimated_duration_sec
            logger.info(f"Sent {len(audio_bytes)} bytes of audio. Extending timeout by {estimated_duration_sec:.2f}s")
            
    except asyncio.CancelledError:
        logger.info("TTS synthesis cancelled (user interruption)")
        raise
    except Exception as e:
        logger.debug(f"TTS synthesis skipped or failed: {e}")


async def handle_voice_stream(websocket: WebSocket, session_id: str):
    """
    Main WebSocket handler for voice streaming
    """
    
    # Initialize voice agent for this session
    voice_agent = VoiceAgent(session_id)
    deepgram = get_deepgram()
    cartesia = get_cartesia()
    
    logger.info(f"Starting voice stream for session: {session_id}")
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "WebSocket connection established"
    })
    
    # Track activity for smart silence detection
    activity_state = {
        'last_active': asyncio.get_event_loop().time()
    }
    
    # Transcript buffering
    transcript_buffer = []
    last_transcript_time = None
    
    # Track the active processing task for Barge-in (cancellation)
    processing_task = None
    transcript_wait_task = None
    
    try:
        while True:
            # POLL for messages with short timeout (1.0s)
            # This allows checking silence timeout frequently even if no data comes
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=1.0 
                )
                # Data received -> Reset silence timer
                activity_state['last_active'] = asyncio.get_event_loop().time()
                
            except asyncio.TimeoutError:
                # Check for silence timeout
                elapsed_since_active = asyncio.get_event_loop().time() - activity_state['last_active']
                if elapsed_since_active > SILENCE_TIMEOUT_SECONDS:
                    logger.info(f"Silence timeout ({SILENCE_TIMEOUT_SECONDS}s) — ending session {session_id}")
                    await websocket.send_json({
                        "type": "session_timeout",
                        "message": "Session ended due to inactivity.",
                        "reason": "silence_timeout"
                    })
                    break
                # IDLE -> continue waiting
                continue
            
            # --- Message Handling ---
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue
                
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                audio_base64 = message.get("data", "")
                if not audio_base64 or len(audio_base64) < 100:
                    continue
                
                try:
                    audio_data = base64.b64decode(audio_base64)
                except Exception:
                    continue

                # BARGE-IN: If user sends audio, CANCEL any agent speaking/thinking
                # But we only want to cancel if it's actual speech? 
                # For responsiveness, we can cancel on audio, 
                # OR we wait for VAD/Transcript. 
                # Currently we rely on Deepgram to detect speech (transcript).
                # To be safe, we wait for transcript.
                
                # ... OR we can trust the frontend VAD? 
                # Let's cancel on Valid Transcript below.
                
                # Transcribe
                transcript = await deepgram.transcribe(audio_data, mime_type="audio/webm")
                
                if not transcript:
                    continue

                # VALID SPEECH DETECTED -> INTERRUPT AGENT
                if processing_task and not processing_task.done():
                    logger.info("User interrupted! Cancelling agent response.")
                    processing_task.cancel()
                    processing_task = None
                    # Also clear any pending buffer
                    transcript_buffer.clear()
                    if transcript_wait_task and not transcript_wait_task.done():
                        transcript_wait_task.cancel()
                    
                    # Notify frontend to stop playing audio (if supported)
                    await websocket.send_json({"type": "interrupt"})

                # Activity detected
                activity_state['last_active'] = asyncio.get_event_loop().time()
                
                # Send transcript update
                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript,
                    "is_final": True
                })
                
                # Add to buffer
                transcript_buffer.append(transcript)
                last_transcript_time = asyncio.get_event_loop().time()
                
                # Schedule processing (debounce)
                if transcript_wait_task and not transcript_wait_task.done():
                    transcript_wait_task.cancel()
                
                async def delayed_process_trigger():
                    await asyncio.sleep(TRANSCRIPT_BUFFER_DELAY)
                    if not transcript_buffer:
                        return
                        
                    # Process buffer
                    buffer_copy = transcript_buffer.copy()
                    transcript_buffer.clear()
                    
                    # Start the heavy processing task
                    # We store it in `processing_task` so we can cancel it next time
                    nonlocal processing_task
                    processing_task = asyncio.create_task(
                        process_transcript_buffer(websocket, voice_agent, cartesia, buffer_copy, activity_state)
                    )
                
                transcript_wait_task = asyncio.create_task(delayed_process_trigger())
                
            elif message_type == "text_message":
                text = message.get("text", "")
                await save_log_async(session_id, 'user', text)
                
                # Text also interrupts agent? Yes.
                if processing_task and not processing_task.done():
                    processing_task.cancel()
                
                # Direct process
                response = await voice_agent.process_turn(text)
                await save_log_async(session_id, 'agent', response)
                
                await websocket.send_json({
                    "type": "agent_response",
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                })
                activity_state['last_active'] = asyncio.get_event_loop().time()
                
            elif message_type == "end_stream":
                logger.info(f"Ending stream for session: {session_id}")
                await websocket.send_json({
                    "type": "stream_ended",
                    "message": "Stream ended successfully"
                })
                break
                
            elif message_type == "config":
                # Receive agent configuration from frontend
                config = message.get("config", {})
                voice_agent.update_config(config)
                logger.info(f"Received agent config with voice_id: {config.get('voice_id')}")
                
            else:
                pass
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in voice stream handler: {error_msg}")
        
        # Only try to send error if connection is still open
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Stream error: {error_msg}"
            })
        except Exception:
            pass


async def synthesize_and_send_audio(websocket: WebSocket, text: str):
    """
    Synthesize TTS and send audio to client
    """
    try:
        cartesia = get_cartesia()
        audio_bytes = await cartesia.synthesize(text)
        
        if audio_bytes:
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({
                "type": "audio_response",
                "audio": audio_base64,
                "format": "wav",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Failed to synthesize audio: {e}")
