"""
Cartesia Text-to-Speech Integration
Provides realistic voice synthesis for AI responses
"""

import os
import io
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CartesiaClient:
    """Client for Cartesia TTS API"""
    
    def __init__(self):
        self.api_key = os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            logger.warning("CARTESIA_API_KEY not set - TTS will not work!")
            self.client = None
        else:
            try:
                from cartesia import Cartesia
                self.client = Cartesia(api_key=self.api_key)
            except ImportError:
                logger.error("cartesia package not installed")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize Cartesia: {e}")
                self.client = None
        
        # Voice configuration
        self.voice_id = os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091")
        self.model_id = "sonic-2"
        self.sample_rate = 16000
        
        logger.info("CartesiaClient initialized")
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Convert raw PCM bytes to WAV format with proper header"""
        data_size = len(pcm_data)
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)
        
        wav_buffer = io.BytesIO()
        # RIFF header
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', 36 + data_size))  # file size - 8
        wav_buffer.write(b'WAVE')
        # fmt chunk
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<I', 16))  # chunk size
        wav_buffer.write(struct.pack('<H', 1))   # PCM format
        wav_buffer.write(struct.pack('<H', channels))
        wav_buffer.write(struct.pack('<I', sample_rate))
        wav_buffer.write(struct.pack('<I', byte_rate))
        wav_buffer.write(struct.pack('<H', block_align))
        wav_buffer.write(struct.pack('<H', bits_per_sample))
        # data chunk
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', data_size))
        wav_buffer.write(pcm_data)
        
        return wav_buffer.getvalue()
    
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize text to speech
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (uses default if not provided)
            
        Returns:
            Audio bytes (WAV format) or None on error
        """
        if not self.client:
            logger.error("Cannot synthesize - Cartesia client not available")
            return None
        
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return None
        
        try:
            logger.info(f"Synthesizing: {text[:50]}...")
            
            target_voice = voice_id or self.voice_id
            
            # Generate audio - collect PCM bytes
            pcm_data = bytearray()
            
            output = self.client.tts.bytes(
                model_id=self.model_id,
                transcript=text,
                voice_id=target_voice,
                output_format={
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": self.sample_rate,
                },
            )
            
            # Handle response - could be bytes directly or iterable of chunks
            if isinstance(output, bytes):
                pcm_data.extend(output)
            elif hasattr(output, '__iter__'):
                for chunk in output:
                    if isinstance(chunk, bytes):
                        pcm_data.extend(chunk)
                    elif isinstance(chunk, dict) and "audio" in chunk:
                        pcm_data.extend(chunk["audio"])
            
            if len(pcm_data) == 0:
                logger.warning("No audio data generated from Cartesia")
                return None
            
            # Convert raw PCM to WAV so browser can play it
            wav_data = self._pcm_to_wav(bytes(pcm_data), self.sample_rate)
            
            logger.info(f"Generated {len(wav_data)} bytes of WAV audio")
            return wav_data
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {str(e)}")
            # Don't print full traceback to avoid log spam, just the error is enough usually
            return None
    
    async def test_connection(self) -> bool:
        """Test Cartesia API connection"""
        try:
            test_audio = await self.synthesize("Hello, this is a test.")
            return test_audio is not None and len(test_audio) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def list_voices(self) -> list:
        """Get available voices from Cartesia"""
        if not self.client:
            logger.error("Cannot list voices - no API key")
            return []
        
        try:
            voices = self.client.voices.list()
            return [{"id": v.id, "name": v.name, "description": v.description} for v in voices]
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []
