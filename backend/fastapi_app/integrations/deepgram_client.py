"""
Deepgram Speech-to-Text Integration
Provides real-time transcription for voice input
"""

import os
import logging
import asyncio
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class DeepgramClient:
    """Client for Deepgram STT API"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            logger.warning("DEEPGRAM_API_KEY not set - STT will not work!")
        
        self.base_url = "https://api.deepgram.com/v1"
        self.model = "nova-2"  # Latest Deepgram model
        
        logger.info("DeepgramClient initialized")
    
    async def transcribe(self, audio_data: bytes, mime_type: str = "audio/webm", language: str = "en") -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of audio (audio/webm, audio/wav, etc.)
            language: Language code (default: en)
            
        Returns:
            Transcribed text
        """
        if not self.api_key:
            logger.error("Cannot transcribe - no API key")
            return "[STT Error: No API key]"
        
        # Auto-detect audio format from header bytes
        header = audio_data[:4] if len(audio_data) >= 4 else b''
        logger.info(f"Audio data: {len(audio_data)} bytes, first 20 bytes: {audio_data[:20].hex()}")
        
        if header[:4] == b'\x1a\x45\xdf\xa3':  # EBML header = WebM/Matroska
            detected_type = "audio/webm"
        elif header[:4] == b'RIFF':
            detected_type = "audio/wav"
        elif header[:4] == b'OggS':
            detected_type = "audio/ogg"
        elif len(header) >= 3 and (header[:3] == b'ID3' or header[0:2] == b'\xff\xfb'):
            detected_type = "audio/mp3"
        else:
            detected_type = mime_type  # fallback to provided
            logger.warning(f"Unknown audio format, header: {header.hex()}, using {mime_type}")
        
        logger.info(f"Detected audio format: {detected_type}")
        
        url = f"{self.base_url}/listen"
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": detected_type
        }
        
        params = {
            "model": self.model,
            "language": language,
            "punctuate": "true",
            "smart_format": "true"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    params=params,
                    content=audio_data
                )
                
                if response.status_code != 200:
                    logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                    return ""
                
                result = response.json()
                
                # Extract transcript from response
                transcript = (
                    result.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                
                if not transcript:
                    logger.warning("Empty transcript from Deepgram")
                    return ""
                
                logger.info(f"Transcribed: {transcript}")
                return transcript
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Deepgram API error: {e.response.status_code} - {e.response.text}")
            return ""
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return ""
    
    async def transcribe_streaming(self, audio_stream):
        """
        Stream audio for real-time transcription
        
        TODO: Implement WebSocket-based streaming for lower latency
        This would use Deepgram's streaming API for real-time results
        """
        logger.warning("Streaming transcription not yet implemented")
        pass
