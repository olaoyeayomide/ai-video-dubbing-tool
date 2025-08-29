import asyncio
import json
import base64
import time
import wave
import numpy as np
from pathlib import Path

from app.main import app
from utils.audio_processing import AudioProcessingPipeline
from models.audio_models import ProcessingRequest, AudioChunk, AudioFormat
from config.settings import settings


async def test_audio_processing():
    """Test the audio processing pipeline with sample data."""
    print("Testing Real-Time AI Dubbing System")
    print("===================================\n")

    # Initialize pipeline
    pipeline = AudioProcessingPipeline()

    # Create synthetic audio data for testing
    print("1. Creating synthetic audio data...")
    duration = 3.0  # seconds
    sample_rate = settings.sample_rate
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Generate sine wave (simulating speech)
    frequency = 440  # A4 note
    audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Add some noise to make it more realistic
    noise = 0.1 * np.random.randn(len(audio_data))
    audio_data += noise

    # Create audio chunk
    audio_chunk = AudioChunk(
        data=audio_data,
        sample_rate=sample_rate,
        timestamp=time.time(),
        chunk_id="test_chunk_001",
        format=AudioFormat.WAV,
    )

    print(f"   Duration: {duration}s")
    print(f"   Sample Rate: {sample_rate}Hz")
    print(f"   Data Shape: {audio_data.shape}")
    print(f"   Max Amplitude: {np.max(np.abs(audio_data)):.3f}\n")

    # Test speaker identification
    print("2. Testing speaker identification...")
    session_id = "test_session_001"
    speaker_id = pipeline.speaker_service.identify_speaker(audio_chunk, session_id)
    speaker_profile = pipeline.speaker_service.get_speaker_profile(speaker_id)

    print(f"   Detected Speaker: {speaker_id}")
    print(f"   Confidence: {speaker_profile.confidence if speaker_profile else 'N/A'}")
    print(
        f"   Embedding Shape: {speaker_profile.voice_embedding.shape if speaker_profile else 'N/A'}\n"
    )

    # Test audio format conversion
    print("3. Testing audio format conversion...")
    audio_bytes = pipeline.audio_chunk_to_bytes(audio_chunk)
    reconstructed_chunk = pipeline.parse_audio_data(audio_bytes)

    print(f"   Original Size: {len(audio_data)} samples")
    print(f"   Bytes Size: {len(audio_bytes)} bytes")
    print(f"   Reconstructed Size: {len(reconstructed_chunk.data)} samples")
    print(
        f"   Data Integrity: {'PASS' if np.allclose(audio_data, reconstructed_chunk.data, atol=1e-3) else 'FAIL'}\n"
    )

    # Test session management
    print("4. Testing session management...")
    session_id = "test_session_001"

    # Create processing request
    request = ProcessingRequest(
        session_id=session_id,
        audio_chunk=audio_chunk,
        target_language="en",
        preserve_voice=True,
    )

    print(f"   Session ID: {session_id}")
    print(f"   Target Language: {request.target_language}")
    print(f"   Preserve Voice: {request.preserve_voice}\n")

    # NOTE: The following tests would require valid API keys
    print("5. API Integration Tests (Simulated)")
    print("   Note: These require valid API keys to run fully\n")

    try:
        # Test without actual API calls (would fail without keys)
        print("   Speech Recognition: SKIPPED (requires Google Cloud API key)")
        print("   Translation: SKIPPED (requires Google Cloud API key)")
        print("   Voice Synthesis: SKIPPED (requires ElevenLabs API key)")
    except Exception as e:
        print(f"   API Test Error: {e}")

    print("\n6. Session Info Test...")
    session_info = pipeline.get_session_info(session_id)
    print(f"   Session Found: {session_info is not None}")

    if session_info:
        print(f"   Speakers: {session_info.get('speakers', [])}")
        print(f"   Processing Count: {session_info.get('processing_count', 0)}")

    print("\n7. Performance Metrics...")
    start_time = time.time()

    # Simulate processing time
    for i in range(5):
        embedding = pipeline.speaker_service.extract_speaker_embedding(audio_chunk)

    processing_time = (time.time() - start_time) / 5
    print(f"   Average Embedding Extraction: {processing_time:.3f}s")
    print(f"   Estimated Real-time Factor: {duration/processing_time:.1f}x")

    print("\n8. WebSocket Message Format Test...")
    # Test WebSocket message format
    audio_b64 = base64.b64encode(audio_bytes).decode()

    websocket_message = {
        "type": "audio_chunk",
        "audio_data": audio_b64[:100] + "...",  # Truncated for display
        "source_language": "auto",
        "target_language": "en",
        "preserve_voice": True,
    }

    print("   WebSocket Message Example:")
    print(json.dumps(websocket_message, indent=4))

    print("\n" + "=" * 50)
    print("CORE BACKEND TESTING COMPLETED")
    print("Next Steps:")
    print("1. Set up API keys in .env file")
    print("2. Run the FastAPI server: python -m app.main")
    print("3. Test WebSocket connection at ws://localhost:8000")
    print("4. Build browser extension for audio capture")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_audio_processing())
