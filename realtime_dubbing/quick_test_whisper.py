#!/usr/bin/env python3
"""
Quick test for OpenAI Whisper migration - Core functionality only.
This test focuses on the essential Whisper API integration without requiring PyTorch/PyAnnote.
"""

import asyncio
import sys
import os
import numpy as np
import logging
import time
import tempfile
import soundfile as sf

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickWhisperTest:
    """Quick test for core Whisper functionality."""
    
    def __init__(self):
        self.results = []
        
    def test_configuration(self):
        """Test basic configuration."""
        logger.info("🧪 Testing configuration...")
        
        try:
            # Check settings
            assert hasattr(settings, 'openai_api_key'), "openai_api_key setting missing"
            assert settings.openai_api_key, "openai_api_key is empty"
            assert hasattr(settings, 'whisper_model'), "whisper_model setting missing"
            
            logger.info(f"✅ Configuration OK")
            logger.info(f"   Whisper model: {settings.whisper_model}")
            logger.info(f"   OpenAI API key: {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
            
            self.results.append(("Configuration", "PASS", "All settings present"))
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.results.append(("Configuration", "FAIL", str(e)))
    
    def test_dependencies(self):
        """Test core dependencies."""
        logger.info("🧪 Testing core dependencies...")
        
        required_packages = [
            ('openai', 'OpenAI client library'),
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
            self.results.append(("Dependencies", "PASS", "Core dependencies available"))
    
    async def test_openai_connection(self):
        """Test OpenAI API connection."""
        logger.info("🧪 Testing OpenAI API connection...")
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Test with a simple text completion to verify API key works
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'API test successful'"}],
                max_tokens=10
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI API connection successful")
            logger.info(f"   Response: {result_text}")
            
            self.results.append(("OpenAI API", "PASS", "Connection successful"))
            
        except Exception as e:
            logger.error(f"❌ OpenAI API test failed: {e}")
            self.results.append(("OpenAI API", "FAIL", str(e)))
    
    async def test_whisper_with_sample_audio(self):
        """Test Whisper with a generated audio sample."""
        logger.info("🧪 Testing Whisper with sample audio...")
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Create a simple test audio file (silence)
            # Note: Whisper might not transcribe silence, but this tests the API integration
            sample_rate = 16000
            duration = 2.0
            samples = int(sample_rate * duration)
            
            # Generate a simple sine wave (more likely to be transcribed than silence)
            t = np.linspace(0, duration, samples, False)
            audio_data = 0.1 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave at low volume
            
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_file_path = temp_file.name
            
            try:
                # Test Whisper transcription
                with open(temp_file_path, "rb") as audio_file:
                    transcription = await client.audio.transcriptions.create(
                        model=settings.whisper_model,
                        file=audio_file,
                        response_format="json"
                    )
                
                logger.info(f"✅ Whisper transcription completed")
                logger.info(f"   Result: '{transcription.text}' (Note: sine wave may produce no text)")
                
                self.results.append(("Whisper API", "PASS", "Transcription API working"))
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Whisper test failed: {e}")
            self.results.append(("Whisper API", "FAIL", str(e)))
    
    async def test_translation_service(self):
        """Test OpenAI translation capability."""
        logger.info("🧪 Testing OpenAI translation...")
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Test translation
            test_text = "Hello, how are you?"
            target_language = "Spanish"
            
            messages = [
                {
                    "role": "system", 
                    "content": f"Translate the following text to {target_language}. Only return the translation."
                },
                {"role": "user", "content": test_text}
            ]
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=50
            )
            
            translation = response.choices[0].message.content.strip()
            
            logger.info(f"✅ Translation completed")
            logger.info(f"   Original: '{test_text}'")
            logger.info(f"   Translated: '{translation}'")
            
            self.results.append(("Translation", "PASS", "OpenAI translation working"))
            
        except Exception as e:
            logger.error(f"❌ Translation test failed: {e}")
            self.results.append(("Translation", "FAIL", str(e)))
    
    async def run_tests(self):
        """Run all tests."""
        logger.info("🚀 Quick Whisper Migration Test")
        logger.info("=" * 50)
        
        # Configuration and dependency tests
        self.test_configuration()
        self.test_dependencies()
        
        # API tests
        await self.test_openai_connection()
        await self.test_whisper_with_sample_audio()
        await self.test_translation_service()
        
        # Print results
        logger.info("=" * 50)
        logger.info("🏁 Test Results")
        logger.info("=" * 50)
        
        passed = failed = 0
        
        for test_name, status, details in self.results:
            status_emoji = {"PASS": "✅", "FAIL": "❌"}[status]
            logger.info(f"{status_emoji} {test_name}: {status}")
            if details:
                logger.info(f"   {details}")
            
            if status == "PASS":
                passed += 1
            else:
                failed += 1
        
        logger.info("-" * 50)
        logger.info(f"📊 Summary: {passed} passed, {failed} failed")
        
        return failed == 0

async def main():
    """Main test execution."""
    test = QuickWhisperTest()
    success = await test.run_tests()
    
    if success:
        logger.info("🎉 Core Whisper migration is working!")
        logger.info("💡 Next steps:")
        logger.info("   1. Install PyTorch for speaker diarization: pip install torch torchaudio")
        logger.info("   2. Install PyAnnote: pip install pyannote-audio")  
        logger.info("   3. Run full tests: python test_whisper_migration.py")
        logger.info("   4. Start your application as usual!")
    else:
        logger.error("❌ Some core tests failed. Check API key and configuration.")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
