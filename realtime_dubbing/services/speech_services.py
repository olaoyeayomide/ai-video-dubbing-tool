import asyncio
import aiohttp
import json
from typing import Optional, AsyncGenerator
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import SpeechRecognitionResult, TranslationResult
from config.settings import settings
from services.whisper_speech_service import WhisperSpeechService, WhisperTranslateService
import logging

logger = logging.getLogger(__name__)

# Use Whisper services as the primary speech recognition services
class SpeechService:
    """Main speech recognition service using OpenAI Whisper."""
    
    def __init__(self):
        self.whisper_service = WhisperSpeechService()
        logger.info("Initialized SpeechService with OpenAI Whisper")
    
    async def recognize_streaming(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[SpeechRecognitionResult, None]:
        """Perform streaming speech recognition."""
        async for result in self.whisper_service.recognize_streaming(audio_generator):
            yield result
    
    async def recognize_audio_chunk(self, audio_data: np.ndarray, language_code: str = "auto") -> SpeechRecognitionResult:
        """Recognize speech from a single audio chunk."""
        return await self.whisper_service.recognize_audio_chunk(audio_data, language_code)


class TranslationService:
    """Main translation service using OpenAI."""
    
    def __init__(self):
        self.whisper_translate_service = WhisperTranslateService()
        logger.info("Initialized TranslationService with OpenAI")
    
    async def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> TranslationResult:
        """Translate text to target language."""
        return await self.whisper_translate_service.translate_text(text, target_language, source_language)
    
    async def batch_translate(self, texts: list[str], target_language: str, source_language: Optional[str] = None) -> list[TranslationResult]:
        """Translate multiple texts in batch for efficiency."""
        return await self.whisper_translate_service.batch_translate(texts, target_language, source_language)


# Legacy class names for backward compatibility
GoogleSpeechService = SpeechService
GoogleTranslateService = TranslationService