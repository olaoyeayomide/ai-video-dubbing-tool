import asyncio
import aiohttp
import io
import json
from typing import Optional, Dict, Any
from elevenlabs import VoiceSettings, Voice, ElevenLabs
from elevenlabs.client import ElevenLabs
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import VoiceSynthesisResult, AudioFormat, SpeakerProfile
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ElevenLabsVoiceService:
    """ElevenLabs voice synthesis and cloning service."""
    
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_cache: Dict[str, str] = {}  # speaker_id -> voice_id mapping
        self.default_voice_settings = VoiceSettings(
            stability=settings.voice_stability,
            similarity_boost=settings.voice_clarity,
            style=0.5,
            use_speaker_boost=True
        )
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None, speaker_profile: Optional[SpeakerProfile] = None) -> VoiceSynthesisResult:
        """Synthesize speech using ElevenLabs TTS."""
        try:
            # Determine voice to use
            target_voice_id = self._get_voice_for_speaker(voice_id, speaker_profile)
            
            # Generate audio using streaming for lower latency
            audio_generator = self.client.generate(
                text=text,
                voice=target_voice_id,
                voice_settings=self.default_voice_settings,
                model="eleven_multilingual_v2",
                stream=True
            )
            
            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                if chunk:
                    audio_chunks.append(chunk)
            
            # Combine audio data
            audio_data = b''.join(audio_chunks)
            
            # Calculate duration (approximate)
            duration = len(audio_data) / (settings.sample_rate * 2)  # 16-bit audio
            
            return VoiceSynthesisResult(
                audio_data=audio_data,
                format=AudioFormat.WAV,
                duration=duration,
                voice_id=target_voice_id
            )
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            raise
    
    async def clone_voice(self, speaker_profile: SpeakerProfile, audio_samples: list[bytes], speaker_name: str) -> str:
        """Clone a voice using audio samples."""
        try:
            # Create voice clone
            voice = self.client.clone(
                name=f"cloned_{speaker_name}_{speaker_profile.speaker_id}",
                description=f"Cloned voice for speaker {speaker_profile.speaker_id}",
                files=audio_samples
            )
            
            # Cache the voice mapping
            self.voice_cache[speaker_profile.speaker_id] = voice.voice_id
            
            logger.info(f"Successfully cloned voice for speaker {speaker_profile.speaker_id}: {voice.voice_id}")
            return voice.voice_id
            
        except Exception as e:
            logger.error(f"Voice cloning error: {e}")
            raise
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices."""
        try:
            voices = self.client.voices.get_all()
            return {
                voice.voice_id: {
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "preview_url": voice.preview_url
                }
                for voice in voices.voices
            }
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            raise
    
    def _get_voice_for_speaker(self, voice_id: Optional[str], speaker_profile: Optional[SpeakerProfile]) -> str:
        """Determine the appropriate voice ID for a speaker."""
        # If specific voice_id provided, use it
        if voice_id:
            return voice_id
        
        # If speaker profile with clone exists, use it
        if speaker_profile and speaker_profile.voice_clone_id:
            return speaker_profile.voice_clone_id
        
        # Check cache for speaker
        if speaker_profile and speaker_profile.speaker_id in self.voice_cache:
            return self.voice_cache[speaker_profile.speaker_id]
        
        # Default to a preset voice
        return "pNInz6obpgDQGcFmaJgB"  # Adam voice as default
    
    async def create_instant_voice_clone(self, audio_data: bytes, speaker_id: str) -> str:
        """Create an instant voice clone from audio data."""
        try:
            # Save audio to temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"sample_{speaker_id}.wav"
            
            # Create instant voice clone
            voice = self.client.clone(
                name=f"instant_{speaker_id}",
                description=f"Instant clone for speaker {speaker_id}",
                files=[audio_file]
            )
            
            # Cache the mapping
            self.voice_cache[speaker_id] = voice.voice_id
            
            logger.info(f"Created instant voice clone for speaker {speaker_id}: {voice.voice_id}")
            return voice.voice_id
            
        except Exception as e:
            logger.error(f"Instant voice cloning error: {e}")
            raise
    
    async def enhance_voice_settings(self, speaker_profile: SpeakerProfile) -> VoiceSettings:
        """Create optimized voice settings for a speaker profile."""
        # Analyze speaker characteristics to optimize settings
        stability = settings.voice_stability
        similarity = settings.voice_clarity
        
        if speaker_profile.characteristics:
            # Adjust based on speaker characteristics
            if speaker_profile.characteristics.get('pitch_variance', 0) > 0.5:
                stability = max(0.3, stability - 0.2)  # Lower stability for dynamic speakers
            
            if speaker_profile.characteristics.get('energy_level', 0) > 0.7:
                similarity = min(1.0, similarity + 0.1)  # Higher similarity for energetic speakers
        
        return VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=0.5,
            use_speaker_boost=True
        )