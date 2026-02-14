from fastapi import WebSocket
import json
import logging
import base64
import asyncio
from datetime import datetime

# Import AI agents
from agents.voice_agent import VoiceAgent
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
SILENCE_TIMEOUT_SECONDS = 15

# Transcript buffer delay: wait this long before processing accumulated transcripts
TRANSCRIPT_BUFFER_DELAY = 2.0  # 2 seconds


async def process_transcript_buffer(websocket, voice_agent, cartesia, buffer_list):
    """
    Process accumulated transcripts after a delay.
    This allows multiple speech segments to be combined into one turn.
    """
    if not buffer_list:
        return
    
    # Combine all buffered transcripts
    combined_transcript = " ".join(buffer_list)
    logger.info(f"Processing buffered transcript: {combined_transcript}")
    
    # ===== AI Agent Processing =====
    try:
        response = await voice_agent.process_turn(combined_transcript)
    except Exception as e:
        logger.error(f"Agent processing failed: {e}")
        response = "I'm sorry, I couldn't process that. Could you try again?"
    
    logger.info(f"Agent response: {response[:100]}")
    
    # Send text response
    await websocket.send_json({
        "type": "agent_response",
        "text": response,
        "timestamp": datetime.now().isoformat()
    })
    
    # ===== Text-to-Speech =====
    try:
        audio_bytes = await cartesia.synthesize(response)
        
        if audio_bytes and len(audio_bytes) > 0:
            audio_base64_out = base64.b64encode(audio_bytes).decode('utf-8')
            await websocket.send_json({
                "type": "audio_response",
                "audio": audio_base64_out,
                "format": "wav",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.debug(f"TTS synthesis skipped or failed: {e}")


async def handle_voice_stream(websocket: WebSocket, session_id: str):
    """
    Main WebSocket handler for voice streaming
    
    Flow:
    1. Browser captures microphone audio as WebM chunks
    2. Audio is sent via WebSocket as base64
    3. Deepgram STT converts audio to text  
    4. VoiceAgent dual-layer (Qwen orchestrator + LLaMA responder) generates response
    5. Cartesia TTS converts response to audio
    6. Audio is sent back to browser for playback
    
    Auto-ends session after 6 seconds of silence (no audio detected).
    """
    
    # Initialize voice agent for this session
    voice_agent = VoiceAgent(session_id)
    ollama_client = OllamaClient()
    deepgram = get_deepgram()
    cartesia = get_cartesia()
    
    logger.info(f"Starting voice stream for session: {session_id}")
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "WebSocket connection established"
    })
    
    
    # Track consecutive empty transcript chunks for silence detection
    last_speech_time = asyncio.get_event_loop().time()
    
    # Transcript buffering: accumulate transcripts for 2s before processing
    transcript_buffer = []
    last_transcript_time = None
    transcript_task = None  # Task that will process buffer after delay
    
    try:
        while True:
            # Wait for next message with a timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=SILENCE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                # No data received for SILENCE_TIMEOUT_SECONDS
                logger.info(f"Silence timeout ({SILENCE_TIMEOUT_SECONDS}s) — auto-ending session {session_id}")
                await websocket.send_json({
                    "type": "session_timeout",
                    "message": f"No audio detected for {SILENCE_TIMEOUT_SECONDS} seconds. Session ended automatically.",
                    "reason": "silence_timeout"
                })
                break
            
            message = json.loads(data)
            
            message_type = message.get("type")
            logger.info(f"Received message type: {message_type}")
            
            if message_type == "audio_chunk":
                # ===== STEP 1: Decode audio from browser =====
                audio_base64 = message.get("data", "")
                
                if not audio_base64:
                    logger.warning("Empty audio chunk received")
                    continue
                
                try:
                    audio_data = base64.b64decode(audio_base64)
                except Exception as e:
                    logger.error(f"Failed to decode base64 audio: {e}")
                    continue
                
                # Skip tiny chunks (likely silence or headers only)
                if len(audio_data) < 500:
                    logger.debug(f"Audio chunk too small ({len(audio_data)} bytes), skipping")
                    continue
                
                logger.info(f"Processing audio chunk: {len(audio_data)} bytes")
                
                # Send processing indicator
                await websocket.send_json({
                    "type": "status",
                    "text": "Processing audio..."
                })
                
                # ===== STEP 2: Speech-to-Text with Deepgram =====
                # Send WebM directly - Deepgram supports it natively!
                transcript = await deepgram.transcribe(audio_data, mime_type="audio/webm")
                
                if not transcript:
                    logger.info("No speech detected in audio chunk")
                    # Check if silence has exceeded the timeout
                    elapsed_silence = asyncio.get_event_loop().time() - last_speech_time
                    if elapsed_silence >= SILENCE_TIMEOUT_SECONDS:
                        logger.info(f"No speech for {elapsed_silence:.1f}s — auto-ending session {session_id}")
                        await websocket.send_json({
                            "type": "session_timeout",
                            "message": f"No speech detected for {SILENCE_TIMEOUT_SECONDS} seconds. Session ended automatically.",
                            "reason": "silence_timeout"
                        })
                        break
                    continue
                
                # Speech detected — reset silence timer
                last_speech_time = asyncio.get_event_loop().time()
                
                logger.info(f"Transcript: {transcript}")
                
                # Send transcript to frontend
                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript,
                    "is_final": True
                })
                
                # ===== STEP 3: Dual-Layer AI Agent Processing =====
                # Qwen orchestrator classifies intent -> LLaMA responder generates reply
                try:
                    response = await voice_agent.process_turn(transcript)
                except Exception as e:
                    logger.error(f"Agent processing failed: {e}")
                    response = "I'm sorry, I couldn't process that. Could you try again?"
                
                logger.info(f"Agent response: {response[:100]}")
                
                # Send text response immediately
                await websocket.send_json({
                    "type": "agent_response",
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # ===== STEP 4: Text-to-Speech with Cartesia =====
                try:
                    audio_bytes = await cartesia.synthesize(response)
                    
                    if audio_bytes and len(audio_bytes) > 0:
                        audio_base64_out = base64.b64encode(audio_bytes).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_response",
                            "audio": audio_base64_out,
                            "format": "wav",
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.info(f"Sent {len(audio_bytes)} bytes of TTS audio")
                    else:
                        logger.warning("No audio generated from TTS")
                except Exception as e:
                    logger.error(f"TTS failed: {e}")
                    # Text response already sent, just log the TTS error
                
            elif message_type == "text_message":
                # Handle text-only messages (for testing without audio)
                text = message.get("text", "")
                logger.info(f"Received text message: {text}")
                
                # Process through voice agent for consistency
                try:
                    response = await voice_agent.process_turn(text)
                except Exception:
                    response = await ollama_client.generate_response(
                        prompt=text,
                        model="llama3.2:1b"
                    )
                
                await websocket.send_json({
                    "type": "agent_response",
                    "text": response,
                    "timestamp": datetime.now().isoformat()
                })
                
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
                logger.info(f"Received agent config: {config.get('name')}")
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in voice stream handler: {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Only try to send error if connection is still open
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Stream error: {error_msg}"
            })
        except Exception:
            # Connection likely already closed or broken
            logger.warning(f"Could not send error message to client: client disconnected")


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
