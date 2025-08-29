#!/usr/bin/env python3
"""
Test script for the new OpenAI Whisper speech recognition implementation.
Tests both speech recognition and translation functionality.
"""

import asyncio
import sys
import os
import numpy as np
import logging
from typing import List
import time

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whisper_speech_service import WhisperSpeechService, WhisperTranslateService
from services.speech_services import SpeechService, TranslationService
from models.audio_models import AudioChunk, AudioFormat
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhisperTestSuite:
    """Test suite for OpenAI Whisper implementation."""
    
    def __init__(self):
        self.results = []
        
    def create_test_audio(self, duration: float = 2.0, sample_rate: int = 16000) -> np.ndarray:
        """Create test audio signal (sine wave)."""
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        # Create a 440 Hz sine wave (A note)
        audio = np.sin(2 * np.pi * 440 * t) * 0.3
        return audio.astype(np.float32)
    
    async def test_whisper_speech_service_direct(self):
        """Test WhisperSpeechService directly."""
        logger.info("🧪 Testing WhisperSpeechService directly...")
        
        try:
            # Check if API key is available
            if not settings.openai_api_key:
                logger.warning("⚠️ OpenAI API key not found. Skipping direct Whisper test.")
                self.results.append(("WhisperSpeechService Direct", "SKIPPED", "No API key"))
                return
            
            service = WhisperSpeechService()
            
            # Create test audio
            test_audio = self.create_test_audio()
            
            # Test recognition
            start_time = time.time()
            result = await service.recognize_audio_chunk(test_audio)
            processing_time = time.time() - start_time
            
            logger.info(f"✅ WhisperSpeechService recognition completed in {processing_time:.3f}s")
            logger.info(f"   Result: text='{result.text}', confidence={result.confidence}, language='{result.language}'")
            
            self.results.append(("WhisperSpeechService Direct", "PASS", f"Processed in {processing_time:.3f}s"))
            
        except Exception as e:
            logger.error(f"❌ WhisperSpeechService test failed: {e}")
            self.results.append(("WhisperSpeechService Direct", "FAIL", str(e)))
    
    async def test_whisper_translate_service_direct(self):
        """Test WhisperTranslateService directly."""
        logger.info("🧪 Testing WhisperTranslateService directly...")
        
        try:
            # Check if API key is available
            if not settings.openai_api_key:
                logger.warning("⚠️ OpenAI API key not found. Skipping direct Whisper translate test.")
                self.results.append(("WhisperTranslateService Direct", "SKIPPED", "No API key"))
                return
            
            service = WhisperTranslateService()
            
            # Test translation
            test_text = "Hello, this is a test."
            target_language = "es"  # Spanish
            
            start_time = time.time()
            result = await service.translate_text(test_text, target_language)
            processing_time = time.time() - start_time
            
            logger.info(f"✅ WhisperTranslateService translation completed in {processing_time:.3f}s")
            logger.info(f"   Original: '{test_text}'")
            logger.info(f"   Translated: '{result.translated_text}' ({result.source_language} -> {result.target_language})")
            
            self.results.append(("WhisperTranslateService Direct", "PASS", f"Processed in {processing_time:.3f}s"))
            
        except Exception as e:
            logger.error(f"❌ WhisperTranslateService test failed: {e}")
            self.results.append(("WhisperTranslateService Direct", "FAIL", str(e)))
    
    async def test_speech_service_wrapper(self):
        """Test SpeechService wrapper."""
        logger.info("🧪 Testing SpeechService wrapper...")
        
        try:
            service = SpeechService()
            
            # Create test audio
            test_audio = self.create_test_audio()
            
            # Test recognition
            start_time = time.time()
            result = await service.recognize_audio_chunk(test_audio)
            processing_time = time.time() - start_time
            
            logger.info(f"✅ SpeechService wrapper test completed in {processing_time:.3f}s")
            logger.info(f"   Result: text='{result.text}', confidence={result.confidence}")
            
            self.results.append(("SpeechService Wrapper", "PASS", f"Processed in {processing_time:.3f}s"))
            
        except Exception as e:
            logger.error(f"❌ SpeechService wrapper test failed: {e}")
            self.results.append(("SpeechService Wrapper", "FAIL", str(e)))
    
    async def test_translation_service_wrapper(self):
        """Test TranslationService wrapper."""
        logger.info("🧪 Testing TranslationService wrapper...")
        
        try:
            service = TranslationService()
            
            # Test translation
            test_text = "Good morning, how are you today?"
            target_language = "fr"  # French
            
            start_time = time.time()
            result = await service.translate_text(test_text, target_language)
            processing_time = time.time() - start_time
            
            logger.info(f"✅ TranslationService wrapper test completed in {processing_time:.3f}s")
            logger.info(f"   Original: '{test_text}'")
            logger.info(f"   Translated: '{result.translated_text}' ({result.source_language} -> {result.target_language})")
            
            self.results.append(("TranslationService Wrapper", "PASS", f"Processed in {processing_time:.3f}s"))
            
        except Exception as e:
            logger.error(f"❌ TranslationService wrapper test failed: {e}")
            self.results.append(("TranslationService Wrapper", "FAIL", str(e)))
    
    def test_configuration(self):
        """Test configuration settings."""
        logger.info("🧪 Testing configuration...")
        
        try:
            # Check basic settings
            assert hasattr(settings, 'openai_api_key'), "openai_api_key setting missing"
            assert hasattr(settings, 'whisper_model'), "whisper_model setting missing"
            assert hasattr(settings, 'max_speakers'), "max_speakers setting missing"
            assert hasattr(settings, 'diarization_model'), "diarization_model setting missing"
            
            logger.info(f"✅ Configuration test passed")
            logger.info(f"   Whisper model: {settings.whisper_model}")
            logger.info(f"   Max speakers: {settings.max_speakers}")
            logger.info(f"   Diarization model: {settings.diarization_model}")
            logger.info(f"   OpenAI API key: {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
            
            self.results.append(("Configuration", "PASS", "All settings present"))
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.results.append(("Configuration", "FAIL", str(e)))
    
    def test_dependencies(self):
        """Test that all required dependencies are available."""
        logger.info("🧪 Testing dependencies...")
        
        required_packages = [
            ('openai', 'OpenAI client library'),
            ('pyannote.audio', 'PyAnnote audio processing'),
            ('torch', 'PyTorch'),
            ('librosa', 'Audio processing'),
            ('soundfile', 'Audio file I/O'),
            ('numpy', 'Numerical computing')
        ]
        
        missing_packages = []
        
        for package, description in required_packages:
            try:
                __import__(package.replace('-', '_').split('.')[0])
                logger.info(f"   ✅ {package} - {description}")
            except ImportError:
                logger.error(f"   ❌ {package} - {description} - NOT FOUND")
                missing_packages.append(package)
        
        if missing_packages:
            self.results.append(("Dependencies", "FAIL", f"Missing: {', '.join(missing_packages)}"))
        else:
            self.results.append(("Dependencies", "PASS", "All dependencies available"))
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🚀 Starting Whisper Implementation Test Suite")
        logger.info("=" * 60)
        
        # Configuration and dependency tests (synchronous)
        self.test_configuration()
        self.test_dependencies()
        
        # Service tests (asynchronous)
        await self.test_whisper_speech_service_direct()
        await self.test_whisper_translate_service_direct()
        await self.test_speech_service_wrapper()
        await self.test_translation_service_wrapper()
        
        # Print results
        logger.info("=" * 60)
        logger.info("🏁 Test Results Summary")
        logger.info("=" * 60)
        
        passed = failed = skipped = 0
        
        for test_name, status, details in self.results:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIPPED": "⚠️"}[status]
            logger.info(f"{status_emoji} {test_name}: {status}")
            if details:
                logger.info(f"   {details}")
            
            if status == "PASS":
                passed += 1
            elif status == "FAIL":
                failed += 1
            else:
                skipped += 1
        
        logger.info("-" * 60)
        logger.info(f"📊 Summary: {passed} passed, {failed} failed, {skipped} skipped")
        
        if failed > 0:
            logger.error("🔥 Some tests failed. Please check the configuration and API keys.")
            return False
        else:
            logger.info("🎉 All tests passed successfully!")
            return True

async def main():
    """Main test execution."""
    test_suite = WhisperTestSuite()
    success = await test_suite.run_all_tests()
    
    if not success:
        logger.info("\n💡 Setup Instructions:")
        logger.info("1. Set your OpenAI API key in the environment:")
        logger.info("   export OPENAI_API_KEY=your_api_key_here")
        logger.info("2. Or create a .env file with:")
        logger.info("   OPENAI_API_KEY=your_api_key_here")
        logger.info("3. Install missing dependencies:")
        logger.info("   pip install -r requirements.txt")
        
        sys.exit(1)
    else:
        logger.info("✨ Whisper implementation is ready to use!")

if __name__ == "__main__":
    asyncio.run(main())
