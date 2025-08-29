#!/usr/bin/env python

"""
Quick test for the Voice Management system

This script demonstrates the key capabilities of the voice management system:
1. Advanced speaker identification
2. Actor voice preservation
3. Voice clone management
"""

import asyncio
import os
import sys
import logging
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.wsi_speaker_identification import WSISpeakerIdentification
from services.enhanced_voice_service import EnhancedVoiceService
from services.voice_management import VoiceManagementSystem
from models.audio_models import AudioChunk, AudioFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Voice Management Test")
    
    # Initialize services
    speaker_service = WSISpeakerIdentification()
    voice_service = EnhancedVoiceService()
    voice_management = VoiceManagementSystem(
        speaker_service=speaker_service,
        voice_service=voice_service
    )
    
    # Create test audio chunk (synthetic data for demonstration)
    sample_rate = 16000
    duration = 3  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Generate a sine wave as test audio
    audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    
    test_audio = AudioChunk(
        data=audio_data,
        sample_rate=sample_rate,
        timestamp=0.0,
        chunk_id="test_chunk",
        format=AudioFormat.WAV
    )
    
    # 1. Test speaker identification
    logger.info("Testing WSI Speaker Identification...")
    speaker_id = speaker_service.identify_speaker(test_audio, "test_session")
    logger.info(f"Identified speaker: {speaker_id}")
    
    # 2. Test actor profile creation
    logger.info("Creating actor profile...")
    actor_id = await voice_management.create_actor_profile(
        name="Test Actor",
        speaker_ids=[speaker_id] if speaker_id else []
    )
    logger.info(f"Created actor profile: {actor_id}")
    
    # 3. Test voice quality analysis
    logger.info("Analyzing voice quality...")
    # Convert AudioChunk to bytes (simplified for testing)
    import soundfile as sf
    from io import BytesIO
    
    output_io = BytesIO()
    sf.write(output_io, test_audio.data, test_audio.sample_rate, format='WAV')
    output_io.seek(0)
    audio_bytes = output_io.read()
    
    quality_metrics = await voice_service.analyze_voice_quality(audio_bytes, sample_rate)
    logger.info(f"Voice quality metrics: {quality_metrics}")
    
    # 4. Get all actors
    logger.info("Getting all actors...")
    actors = await voice_management.get_all_actors()
    logger.info(f"Found {len(actors)} actors")
    
    # Display actor information
    for actor_id, profile in actors.items():
        logger.info(f"Actor: {profile.name} (ID: {actor_id})")
        logger.info(f"  Speakers: {profile.speaker_ids}")
        logger.info(f"  Voices: {profile.voice_ids}")
    
    logger.info("Voice Management Test Completed")

if __name__ == "__main__":
    asyncio.run(main())
