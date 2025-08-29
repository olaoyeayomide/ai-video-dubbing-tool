import asyncio
import io
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional, AsyncGenerator, Dict, Any, List
import whisper
from pyannote.audio import Pipeline
from pyannote.core import Segment
import logging
import torch
import sys
import os
import concurrent.futures
import functools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import SpeechRecognitionResult, TranslationResult
from config.settings import settings

logger = logging.getLogger(__name__)

class WhisperSpeechService:
    """Local OpenAI Whisper Speech-to-Text service (completely free) with speaker diarization."""
    
    def __init__(self):
        # Initialize local Whisper model
        self.model = None
        self.model_name = getattr(settings, 'whisper_model', 'base')  # Default to 'base' model
        self.diarization_pipeline = None
        self._init_whisper_model()
        self._init_diarization()
        
        # Create executor for CPU-intensive tasks
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        # Buffer for streaming audio
        self.audio_buffer = []
        self.sample_rate = settings.sample_rate
        
    def _init_whisper_model(self):
        """Initialize local Whisper model."""
        try:
            # Load the local Whisper model
            # Available models: tiny, base, small, medium, large
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Local Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Could not load Whisper model: {e}")
            # Fallback to base model
            try:
                logger.info("Trying fallback to base model...")
                self.model = whisper.load_model("base")
                logger.info("Fallback Whisper model loaded successfully")
            except Exception as fallback_e:
                logger.error(f"Could not load fallback model: {fallback_e}")
                raise Exception("Failed to initialize Whisper model")
    
    def _init_diarization(self):
        """Initialize speaker diarization pipeline."""
        try:
            # Initialize pyannote speaker diarization pipeline
            self.diarization_pipeline = Pipeline.from_pretrained(
                settings.diarization_model,
                use_auth_token=None  # You might need a Hugging Face token for some models
            )
            
            # Set device (GPU if available)
            if torch.cuda.is_available():
                self.diarization_pipeline = self.diarization_pipeline.to(torch.device("cuda"))
            
            logger.info("Speaker diarization pipeline initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize speaker diarization: {e}")
            self.diarization_pipeline = None
    
    async def recognize_streaming(self, audio_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[SpeechRecognitionResult, None]:
        """Perform streaming speech recognition with buffering."""
        buffer_duration = 5.0  # Process every 5 seconds of audio
        buffer_samples = int(buffer_duration * self.sample_rate)
        
        try:
            async for audio_chunk in audio_generator:
                # Convert bytes to numpy array
                audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                self.audio_buffer.extend(audio_data)
                
                # Process when buffer reaches target size
                if len(self.audio_buffer) >= buffer_samples:
                    # Get audio for processing
                    audio_for_processing = np.array(self.audio_buffer[:buffer_samples])
                    
                    # Remove processed audio from buffer (keep some overlap)
                    overlap_samples = int(1.0 * self.sample_rate)  # 1 second overlap
                    self.audio_buffer = self.audio_buffer[buffer_samples - overlap_samples:]
                    
                    # Process this chunk
                    try:
                        result = await self.recognize_audio_chunk(audio_for_processing)
                        if result.text.strip():  # Only yield non-empty results
                            yield result
                    except Exception as e:
                        logger.error(f"Error processing audio chunk: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Streaming recognition error: {e}")
            raise
    
    async def recognize_audio_chunk(self, audio_data: np.ndarray, language_code: str = "auto") -> SpeechRecognitionResult:
        """Recognize speech from a single audio chunk using local Whisper."""
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write audio data to temporary file
                sf.write(temp_file.name, audio_data, self.sample_rate)
                temp_file_path = temp_file.name
            
            try:
                # Use local Whisper model for transcription (run in thread pool to avoid blocking)
                whisper_options = {
                    "language": settings.whisper_language if hasattr(settings, 'whisper_language') and settings.whisper_language else None,
                    "task": "transcribe"
                }
                
                # Run Whisper in thread pool to avoid blocking the event loop
                transcribe_func = functools.partial(
                    self.model.transcribe,
                    temp_file_path,
                    **whisper_options
                )
                
                loop = asyncio.get_event_loop()
                whisper_result = await loop.run_in_executor(self.executor, transcribe_func)
                
                # Extract text and other information
                text = whisper_result["text"].strip()
                language = whisper_result.get("language", language_code)
                
                # Calculate confidence from segments if available
                confidence = self._calculate_confidence_from_segments(whisper_result.get("segments", []))
                if confidence == 0.0:  # Fallback to text-based estimation
                    confidence = self._estimate_confidence(text)
                
                # Perform speaker diarization if available
                speaker_id = None
                if self.diarization_pipeline and len(audio_data) > self.sample_rate * 2:  # At least 2 seconds
                    try:
                        speaker_id = await self._perform_diarization(temp_file_path, audio_data)
                    except Exception as e:
                        logger.warning(f"Speaker diarization failed: {e}")
                
                return SpeechRecognitionResult(
                    text=text,
                    confidence=confidence,
                    language=language,
                    speaker_id=speaker_id,
                    is_final=True
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Audio chunk recognition error: {e}")
            # Return empty result instead of raising
            return SpeechRecognitionResult(
                text="",
                confidence=0.0,
                language=language_code,
                is_final=True
            )
    
    def _calculate_confidence_from_segments(self, segments: List[Dict]) -> float:
        """Calculate confidence score from Whisper segments."""
        if not segments:
            return 0.0
        
        # Whisper provides logprob (log probability) for segments
        # Convert to confidence score (0.0 to 1.0)
        total_logprob = 0.0
        total_tokens = 0
        
        for segment in segments:
            if "avg_logprob" in segment:
                logprob = segment["avg_logprob"]
                tokens = len(segment.get("words", [segment.get("text", "").split()]))
                total_logprob += logprob * tokens
                total_tokens += tokens
        
        if total_tokens == 0:
            return 0.0
            
        avg_logprob = total_logprob / total_tokens
        # Convert log probability to confidence (approximate)
        confidence = min(0.95, max(0.1, 1.0 + avg_logprob / 5.0))
        return confidence
    
    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence score based on text characteristics."""
        if not text or not text.strip():
            return 0.0
            
        # Simple heuristic: longer, more complex text generally indicates better recognition
        text_length = len(text.strip())
        word_count = len(text.split())
        
        # Base confidence
        confidence = 0.7
        
        # Adjust based on length
        if text_length > 50:
            confidence += 0.15
        elif text_length > 20:
            confidence += 0.1
        elif text_length < 5:
            confidence -= 0.2
            
        # Adjust based on word count
        if word_count > 10:
            confidence += 0.1
        elif word_count < 3:
            confidence -= 0.15
            
        # Check for common filler words or unclear speech indicators
        filler_words = ['um', 'uh', 'er', 'ah', '...']
        if any(filler in text.lower() for filler in filler_words):
            confidence -= 0.1
            
        return max(0.1, min(0.95, confidence))
    
    async def _perform_diarization(self, audio_file_path: str, audio_data: np.ndarray) -> Optional[str]:
        """Perform speaker diarization on audio."""
        if not self.diarization_pipeline:
            return None
            
        try:
            # Run diarization
            diarization = self.diarization_pipeline(audio_file_path)
            
            # Find the most prominent speaker in this segment
            speaker_durations = {}
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                duration = turn.end - turn.start
                if speaker not in speaker_durations:
                    speaker_durations[speaker] = 0
                speaker_durations[speaker] += duration
            
            if speaker_durations:
                # Return the speaker with the most speaking time
                primary_speaker = max(speaker_durations.items(), key=lambda x: x[1])[0]
                return f"speaker_{primary_speaker}"
            
        except Exception as e:
            logger.warning(f"Diarization error: {e}")
            
        return None


class WhisperTranslateService:
    """Local Translation service (free alternatives to Google Translate)."""
    
    def __init__(self):
        # Initialize local Whisper model for translation if not already done
        self.whisper_model = None
        self._init_translation_model()
    
    def _init_translation_model(self):
        """Initialize model for translation."""
        try:
            # Try to reuse existing Whisper model or load a new one for translation
            self.whisper_model = whisper.load_model("base")  # Good balance for translation
            logger.info("Whisper model loaded for translation")
        except Exception as e:
            logger.warning(f"Could not load Whisper model for translation: {e}")
            self.whisper_model = None
    
    async def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> TranslationResult:
        """Translate text to target language using free methods."""
        try:
            # Skip translation if source and target are the same
            if source_language == target_language:
                return TranslationResult(
                    translated_text=text,
                    source_language=source_language,
                    target_language=target_language,
                    confidence=1.0
                )
            
            # For now, we'll use a simple approach that works well for audio translation:
            # 1. If we have audio data, we can use Whisper's built-in translation to English
            # 2. For text-only translation, we'll implement a basic dictionary-based approach
            #    or suggest using external free services
            
            # Simple pass-through for now - in a real implementation, you'd want to:
            # - Use Google Translate's free web interface (with rate limits)
            # - Use Microsoft Translator's free tier
            # - Use local translation models like Helsinki-NLP models
            # - Use Whisper's built-in translation (audio to English only)
            
            logger.warning("Translation service using fallback - implement free translation service")
            
            # Detect source language if not provided
            if source_language is None:
                source_language = await self._detect_language(text)
            
            # For this example, return the original text with a note
            # In production, implement proper free translation
            translated_text = f"[Translation to {target_language}]: {text}"
            
            return TranslationResult(
                translated_text=translated_text,
                source_language=source_language or "unknown",
                target_language=target_language,
                confidence=0.7  # Lower confidence since we're using fallback
            )
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise
    
    async def _detect_language(self, text: str) -> str:
        """Detect the language of the text using simple heuristics."""
        try:
            # Simple language detection based on common patterns
            # In production, you'd use a proper library like langdetect or polyglot
            
            text_lower = text.lower()
            
            # Basic language detection patterns
            if any(word in text_lower for word in ['the', 'and', 'is', 'are', 'was', 'were', 'have', 'has']):
                return "en"
            elif any(word in text_lower for word in ['el', 'la', 'de', 'en', 'y', 'es', 'que', 'se', 'un', 'una']):
                return "es"
            elif any(word in text_lower for word in ['le', 'la', 'de', 'et', 'est', 'que', 'se', 'un', 'une', 'des']):
                return "fr"
            elif any(word in text_lower for word in ['der', 'die', 'das', 'und', 'ist', 'sind', 'war', 'waren', 'haben', 'hat']):
                return "de"
            elif any(word in text_lower for word in ['il', 'la', 'di', 'e', 'è', 'che', 'se', 'un', 'una', 'sono']):
                return "it"
            else:
                return "unknown"
            
        except Exception as e:
            logger.warning(f"Language detection error: {e}")
            return "unknown"
    
    async def batch_translate(self, texts: list[str], target_language: str, source_language: Optional[str] = None) -> list[TranslationResult]:
        """Translate multiple texts in batch for efficiency."""
        try:
            tasks = [self.translate_text(text, target_language, source_language) for text in texts]
            return await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            raise
