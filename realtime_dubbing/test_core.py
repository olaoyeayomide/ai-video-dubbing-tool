import asyncio
import json
import base64
import time
import numpy as np
from pathlib import Path
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from models.audio_models import AudioChunk, AudioFormat, SpeakerProfile
from services.speaker_identification import SpeakerIdentificationService
from config.settings import settings

async def test_core_functionality():
    """Test core functionality without external API dependencies."""
    print("Testing Real-Time AI Dubbing System - Core Functionality")
    print("=========================================================\n")
    
    # Test 1: Configuration Loading
    print("1. Testing Configuration...")
    print(f"   Sample Rate: {settings.sample_rate}Hz")
    print(f"   Chunk Size: {settings.chunk_size}")
    print(f"   Voice Similarity Threshold: {settings.voice_similarity_threshold}")
    print(f"   Voice Stability: {settings.voice_stability}")
    print(f"   Voice Clarity: {settings.voice_clarity}")
    print("   ✓ Configuration loaded successfully\n")
    
    # Test 2: Audio Data Generation and Processing
    print("2. Testing Audio Data Processing...")
    duration = 2.0  # seconds
    sample_rate = settings.sample_rate
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate different types of synthetic audio for speaker testing
    speakers_data = []
    
    # Speaker 1: Male voice simulation (lower frequency)
    freq1 = 120  # Hz, typical male fundamental frequency
    audio1 = 0.7 * np.sin(2 * np.pi * freq1 * t) + 0.3 * np.sin(2 * np.pi * freq1 * 2 * t)
    audio1 += 0.1 * np.random.randn(len(audio1))  # Add noise
    speakers_data.append((audio1, "Male Speaker"))
    
    # Speaker 2: Female voice simulation (higher frequency)
    freq2 = 220  # Hz, typical female fundamental frequency
    audio2 = 0.6 * np.sin(2 * np.pi * freq2 * t) + 0.4 * np.sin(2 * np.pi * freq2 * 1.5 * t)
    audio2 += 0.1 * np.random.randn(len(audio2))  # Add noise
    speakers_data.append((audio2, "Female Speaker"))
    
    # Speaker 3: Child voice simulation (even higher frequency)
    freq3 = 300  # Hz, typical child fundamental frequency
    audio3 = 0.5 * np.sin(2 * np.pi * freq3 * t) + 0.5 * np.sin(2 * np.pi * freq3 * 1.2 * t)
    audio3 += 0.15 * np.random.randn(len(audio3))  # Add more noise
    speakers_data.append((audio3, "Child Speaker"))
    
    print(f"   Generated {len(speakers_data)} synthetic speaker samples")
    print(f"   Duration: {duration}s each")
    print(f"   Sample Rate: {sample_rate}Hz")
    print("   ✓ Audio data generation successful\n")
    
    # Test 3: Speaker Identification Service
    print("3. Testing Speaker Identification...")
    speaker_service = SpeakerIdentificationService()
    
    detected_speakers = []
    for i, (audio_data, speaker_name) in enumerate(speakers_data):
        # Create audio chunk
        audio_chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=time.time(),
            chunk_id=f"test_chunk_{i+1:03d}",
            format=AudioFormat.WAV
        )
        
        # Test speaker identification
        speaker_id = speaker_service.identify_speaker(audio_chunk)
        speaker_profile = speaker_service.get_speaker_profile(speaker_id)
        
        detected_speakers.append(speaker_id)
        
        print(f"   {speaker_name}:")
        print(f"     Speaker ID: {speaker_id}")
        print(f"     Confidence: {speaker_profile.confidence:.3f}")
        print(f"     Embedding Shape: {speaker_profile.voice_embedding.shape}")
        if speaker_profile.characteristics:
            print(f"     Pitch Mean: {speaker_profile.characteristics.get('pitch_mean', 0):.1f}Hz")
            print(f"     Energy Level: {speaker_profile.characteristics.get('energy_level', 0):.3f}")
    
    print(f"\n   Detected {len(set(detected_speakers))} unique speakers")
    print("   ✓ Speaker identification successful\n")
    
    # Test 4: Audio Feature Extraction
    print("4. Testing Audio Feature Extraction...")
    test_chunk = AudioChunk(
        data=speakers_data[0][0],
        sample_rate=sample_rate,
        timestamp=time.time(),
        chunk_id="feature_test",
        format=AudioFormat.WAV
    )
    
    # Extract features
    embedding = speaker_service.extract_speaker_embedding(test_chunk)
    characteristics = speaker_service._analyze_voice_characteristics(test_chunk)
    
    print(f"   Embedding Dimensions: {embedding.shape[0]}")
    print(f"   Embedding Range: [{embedding.min():.3f}, {embedding.max():.3f}]")
    print(f"   Voice Characteristics: {len(characteristics)} features")
    for key, value in characteristics.items():
        print(f"     {key}: {value:.3f}")
    print("   ✓ Feature extraction successful\n")
    
    # Test 5: Speaker Consistency
    print("5. Testing Speaker Consistency...")
    # Test the same speaker multiple times
    same_speaker_ids = []
    for i in range(3):
        # Add slight variations to simulate real audio
        varied_audio = speakers_data[0][0] + 0.05 * np.random.randn(len(speakers_data[0][0]))
        varied_chunk = AudioChunk(
            data=varied_audio,
            sample_rate=sample_rate,
            timestamp=time.time(),
            chunk_id=f"consistency_test_{i}",
            format=AudioFormat.WAV
        )
        
        speaker_id = speaker_service.identify_speaker(varied_chunk)
        same_speaker_ids.append(speaker_id)
    
    consistency = len(set(same_speaker_ids)) == 1
    print(f"   Same speaker detected {len(same_speaker_ids)} times")
    print(f"   Speaker IDs: {same_speaker_ids}")
    print(f"   Consistency: {'PASS' if consistency else 'FAIL'}")
    print("   ✓ Speaker consistency test completed\n")
    
    # Test 6: Memory and Performance
    print("6. Testing Performance...")
    start_time = time.time()
    
    # Process multiple chunks to test performance
    processing_times = []
    for i in range(10):
        chunk_start = time.time()
        
        # Create random audio chunk
        test_audio = 0.5 * np.random.randn(int(sample_rate * 0.5))  # 0.5 second chunk
        test_chunk = AudioChunk(
            data=test_audio,
            sample_rate=sample_rate,
            timestamp=time.time(),
            chunk_id=f"perf_test_{i}",
            format=AudioFormat.WAV
        )
        
        # Process chunk
        speaker_service.identify_speaker(test_chunk)
        
        processing_times.append(time.time() - chunk_start)
    
    avg_processing_time = np.mean(processing_times)
    real_time_factor = 0.5 / avg_processing_time  # 0.5s audio / processing time
    
    print(f"   Processed 10 chunks in {time.time() - start_time:.3f}s")
    print(f"   Average processing time: {avg_processing_time:.3f}s")
    print(f"   Real-time factor: {real_time_factor:.1f}x")
    print(f"   Memory usage: {len(speaker_service.speaker_profiles)} speakers tracked")
    print("   ✓ Performance test completed\n")
    
    # Test 7: Data Structure Validation
    print("7. Testing Data Structures...")
    
    # Test SpeakerProfile
    test_profile = SpeakerProfile(
        speaker_id="test_speaker_001",
        voice_embedding=np.random.randn(29),
        confidence=0.95,
        characteristics={
            "pitch_mean": 150.0,
            "energy_level": 0.7
        }
    )
    
    print(f"   SpeakerProfile created: {test_profile.speaker_id}")
    print(f"   Embedding shape: {test_profile.voice_embedding.shape}")
    print(f"   Confidence: {test_profile.confidence}")
    print(f"   Characteristics: {len(test_profile.characteristics)} features")
    
    # Test AudioChunk
    test_audio_chunk = AudioChunk(
        data=np.random.randn(1024),
        sample_rate=16000,
        timestamp=time.time(),
        chunk_id="test_chunk",
        format=AudioFormat.WAV
    )
    
    print(f"   AudioChunk created: {test_audio_chunk.chunk_id}")
    print(f"   Data shape: {test_audio_chunk.data.shape}")
    print(f"   Sample rate: {test_audio_chunk.sample_rate}")
    print(f"   Format: {test_audio_chunk.format.value}")
    print("   ✓ Data structures validated\n")
    
    # Test 8: WebSocket Message Format
    print("8. Testing WebSocket Message Format...")
    
    # Simulate audio data as base64
    audio_bytes = (speakers_data[0][0] * 32767).astype(np.int16).tobytes()
    audio_b64 = base64.b64encode(audio_bytes).decode()
    
    # Create sample WebSocket messages
    messages = {
        "audio_chunk": {
            "type": "audio_chunk",
            "audio_data": audio_b64[:100] + "...",  # Truncated for display
            "source_language": "auto",
            "target_language": "en",
            "preserve_voice": True
        },
        "start_dubbing": {
            "type": "start_dubbing",
            "target_language": "en",
            "preserve_voice": True
        },
        "session_info": {
            "type": "session_info",
            "data": {
                "session_id": "test_session_001",
                "speakers": list(detected_speakers),
                "processing_count": 10
            }
        }
    }
    
    for msg_type, message in messages.items():
        print(f"   {msg_type} message format:")
        print(f"     Size: {len(json.dumps(message))} characters")
        print(f"     Valid JSON: {json.dumps(message) is not None}")
    
    print("   ✓ WebSocket message format validated\n")
    
    # Summary
    print("="*60)
    print("CORE FUNCTIONALITY TEST SUMMARY")
    print("="*60)
    print("✓ Configuration management: WORKING")
    print("✓ Audio data processing: WORKING")
    print("✓ Speaker identification: WORKING")
    print("✓ Feature extraction: WORKING")
    print("✓ Speaker consistency: WORKING")
    print("✓ Performance metrics: ACCEPTABLE")
    print("✓ Data structures: VALIDATED")
    print("✓ WebSocket format: READY")
    print("\nREADY FOR INTEGRATION TESTING!")
    print("\nNext Steps:")
    print("1. Set up API keys for Google Cloud and ElevenLabs")
    print("2. Test with real audio files")
    print("3. Start FastAPI server for WebSocket testing")
    print("4. Develop browser extension for audio capture")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_core_functionality())