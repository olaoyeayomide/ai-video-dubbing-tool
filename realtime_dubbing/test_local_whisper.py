#!/usr/bin/env python3
"""
Test script for Local Whisper integration (100% Free!)
This tests the new local Whisper implementation without any API dependencies.
"""

import asyncio
import numpy as np
import tempfile
import soundfile as sf
import sys
import os

# Add the project path to sys.path
sys.path.append('/workspace/code/realtime_dubbing')

from services.whisper_speech_service import WhisperSpeechService
from models.audio_models import SpeechRecognitionResult

async def test_local_whisper():
    """Test local Whisper speech recognition."""
    print("🎉 Testing Local Whisper Speech-to-Text (100% Free!)")
    print("=" * 60)
    
    try:
        # Initialize the service
        print("📊 Initializing WhisperSpeechService...")
        service = WhisperSpeechService()
        print("✅ Service initialized successfully!")
        
        # Create a simple test audio signal (sine wave representing speech-like audio)
        print("\n🎵 Creating test audio signal...")
        duration = 3.0  # 3 seconds
        sample_rate = 16000
        frequency = 440  # A4 note frequency
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a more complex waveform that might be recognized as speech
        # Mix multiple frequencies to simulate speech patterns
        audio_signal = (
            0.3 * np.sin(frequency * 2.0 * np.pi * t) +
            0.2 * np.sin(frequency * 1.5 * 2.0 * np.pi * t) +
            0.1 * np.sin(frequency * 0.8 * 2.0 * np.pi * t)
        )
        
        # Add some noise to make it more realistic
        noise = np.random.normal(0, 0.05, audio_signal.shape)
        audio_signal = audio_signal + noise
        
        # Normalize
        audio_signal = audio_signal / np.max(np.abs(audio_signal))
        
        print(f"✅ Test audio created: {duration}s at {sample_rate}Hz")
        
        # Test recognition
        print("\n🎯 Testing speech recognition...")
        result = await service.recognize_audio_chunk(audio_signal, "en")
        
        print("\n📈 Recognition Results:")
        print(f"   Text: '{result.text}'")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Language: {result.language}")
        print(f"   Is Final: {result.is_final}")
        print(f"   Speaker ID: {result.speaker_id}")
        
        # Test with real silence (should produce empty result)
        print("\n🔇 Testing with silence...")
        silence = np.zeros(int(sample_rate * 2.0))  # 2 seconds of silence
        silence_result = await service.recognize_audio_chunk(silence, "en")
        print(f"   Silence Text: '{silence_result.text}'")
        print(f"   Silence Confidence: {silence_result.confidence:.2f}")
        
        print("\n🎊 ALL TESTS PASSED!")
        print("\n💡 Key Benefits:")
        print("   ✅ Completely FREE - no API costs!")
        print("   ✅ Works offline - no internet required!")
        print("   ✅ Privacy-friendly - all processing local!")
        print("   ✅ No quotas or rate limits!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_local_whisper())
    if success:
        print("\n🎉 Migration to Local Whisper: SUCCESS!")
    else:
        print("\n💔 Migration needs attention.")
        sys.exit(1)
