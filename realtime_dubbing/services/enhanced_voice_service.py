import asyncio
import aiohttp
import io
import json
import os
import sys
import numpy as np
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from elevenlabs import VoiceSettings, Voice, ElevenLabs
from elevenlabs.client import ElevenLabs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import VoiceSynthesisResult, AudioFormat, SpeakerProfile, AudioChunk
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class VoiceClone:
    """Voice clone data."""
    voice_id: str
    speaker_id: str
    name: str
    creation_time: float
    samples_duration: float
    voice_settings: Dict[str, Any]
    metrics: Dict[str, float] = None
    last_used: float = None


class EnhancedVoiceService:
    """Enhanced voice synthesis and cloning service with voice quality optimization."""
    
    def __init__(self, voice_library_dir: str = "data/voice_library"):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        
        # Voice library storage
        self.voice_library_dir = Path(voice_library_dir)
        self.voice_library_dir.mkdir(exist_ok=True, parents=True)
        
        # Voice clone mapping
        self.voice_clones: Dict[str, VoiceClone] = {}  # voice_id -> VoiceClone
        self.speaker_voices: Dict[str, str] = {}  # speaker_id -> voice_id mapping
        
        # Voice optimization defaults
        self.default_voice_settings = VoiceSettings(
            stability=settings.voice_stability,
            similarity_boost=settings.voice_clarity,
            style=0.5,
            use_speaker_boost=True
        )
        
        # Load existing voice library
        self._load_voice_library()
    
    def _load_voice_library(self):
        """Load voice library metadata from disk."""
        try:
            metadata_path = self.voice_library_dir / "voice_library.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    library_data = json.load(f)
                
                for voice_id, data in library_data.items():
                    clone = VoiceClone(
                        voice_id=voice_id,
                        speaker_id=data.get("speaker_id", ""),
                        name=data.get("name", ""),
                        creation_time=data.get("creation_time", 0),
                        samples_duration=data.get("samples_duration", 0),
                        voice_settings=data.get("voice_settings", {}),
                        metrics=data.get("metrics", {}),
                        last_used=data.get("last_used", 0)
                    )
                    
                    self.voice_clones[voice_id] = clone
                    if clone.speaker_id:
                        self.speaker_voices[clone.speaker_id] = voice_id
                
                logger.info(f"Loaded {len(self.voice_clones)} voice clones from library")
        except Exception as e:
            logger.error(f"Error loading voice library: {e}")
    
    def _save_voice_library(self):
        """Save voice library metadata to disk."""
        try:
            metadata_path = self.voice_library_dir / "voice_library.json"
            library_data = {}
            
            for voice_id, clone in self.voice_clones.items():
                library_data[voice_id] = {
                    "voice_id": clone.voice_id,
                    "speaker_id": clone.speaker_id,
                    "name": clone.name,
                    "creation_time": clone.creation_time,
                    "samples_duration": clone.samples_duration,
                    "voice_settings": clone.voice_settings,
                    "metrics": clone.metrics,
                    "last_used": clone.last_used
                }
            
            with open(metadata_path, 'w') as f:
                json.dump(library_data, f, indent=2)
                
            logger.debug(f"Saved voice library with {len(self.voice_clones)} voice clones")
        except Exception as e:
            logger.error(f"Error saving voice library: {e}")
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None, 
                               speaker_profile: Optional[SpeakerProfile] = None,
                               optimize_settings: bool = True) -> VoiceSynthesisResult:
        """Synthesize speech using enhanced voice settings."""
        try:
            # Determine voice to use
            target_voice_id = self._get_voice_for_speaker(voice_id, speaker_profile)
            
            # Determine voice settings
            voice_settings = self.default_voice_settings
            if optimize_settings and speaker_profile and speaker_profile.characteristics:
                voice_settings = self._optimize_voice_settings(speaker_profile)
            
            # Update last used time for voice clone
            if target_voice_id in self.voice_clones:
                self.voice_clones[target_voice_id].last_used = time.time()
            
            # Generate audio using streaming for lower latency
            audio_generator = self.client.generate(
                text=text,
                voice=target_voice_id,
                voice_settings=voice_settings,
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
            logger.error(f"Enhanced speech synthesis error: {e}")
            raise
    
    async def create_professional_voice_clone(self, 
                                         speaker_id: str, 
                                         name: str,
                                         audio_samples: List[bytes], 
                                         speaker_profile: Optional[SpeakerProfile] = None) -> str:
        """Create a professional voice clone with quality metrics."""
        try:
            # Prepare audio samples
            file_objects = []
            total_duration = 0
            
            for i, sample in enumerate(audio_samples):
                sample_io = io.BytesIO(sample)
                sample_io.name = f"sample_{speaker_id}_{i}.wav"
                file_objects.append(sample_io)
                
                # Estimate duration (crude approximation)
                total_duration += len(sample) / (settings.sample_rate * 2)  # 16-bit audio
            
            # Create voice clone
            clone_name = f"{name}_{speaker_id}"
            description = f"Professional voice clone for {name} (speaker {speaker_id})"
            
            voice = self.client.clone(
                name=clone_name,
                description=description,
                files=file_objects
            )
            
            voice_id = voice.voice_id
            
            # Create voice clone metadata
            voice_clone = VoiceClone(
                voice_id=voice_id,
                speaker_id=speaker_id,
                name=name,
                creation_time=time.time(),
                samples_duration=total_duration,
                voice_settings={
                    "stability": settings.voice_stability,
                    "similarity_boost": settings.voice_clarity,
                    "style": 0.5,
                    "use_speaker_boost": True
                },
                metrics={
                    "sample_count": len(audio_samples),
                    "estimated_quality": self._estimate_clone_quality(total_duration)
                },
                last_used=time.time()
            )
            
            # Store in mappings
            self.voice_clones[voice_id] = voice_clone
            self.speaker_voices[speaker_id] = voice_id
            
            # Save library
            self._save_voice_library()
            
            logger.info(f"Created professional voice clone for speaker {speaker_id}: {voice_id}")
            return voice_id
            
        except Exception as e:
            logger.error(f"Professional voice cloning error: {e}")
            raise
    
    def _estimate_clone_quality(self, total_duration: float) -> float:
        """Estimate voice clone quality based on sample duration.
        
        Returns a value between 0.0 and 1.0.
        """
        # Based on ElevenLabs guidelines:
        # - <30 seconds: poor quality
        # - 30-60 seconds: basic quality
        # - 1-5 minutes: good quality
        # - 5-30 minutes: excellent quality
        if total_duration <= 30:
            return 0.3
        elif total_duration <= 60:
            return 0.5
        elif total_duration <= 300:  # 5 minutes
            return 0.7 + (total_duration - 60) / (300 - 60) * 0.2
        else:
            return min(0.9 + (total_duration - 300) / (1800 - 300) * 0.1, 1.0)
    
    def _optimize_voice_settings(self, speaker_profile: SpeakerProfile) -> VoiceSettings:
        """Create optimized voice settings based on speaker characteristics."""
        characteristics = speaker_profile.characteristics or {}
        
        # Start with defaults
        stability = settings.voice_stability
        similarity = settings.voice_clarity
        style = 0.5
        use_speaker_boost = True
        
        # Adjust settings based on voice characteristics
        if "pitch_std" in characteristics:
            # Higher pitch variance -> lower stability for more expression
            pitch_variance = characteristics["pitch_std"]
            if pitch_variance > 20:
                stability = max(0.3, stability - 0.2)
            elif pitch_variance < 10:
                stability = min(0.8, stability + 0.1)
        
        if "speaking_rate" in characteristics:
            # Faster speakers get higher style parameter
            speaking_rate = characteristics["speaking_rate"]
            style = min(0.8, 0.3 + speaking_rate / 10.0)
        
        if "voice_clarity" in characteristics:
            # Clearer voice gets higher similarity boost
            clarity = characteristics["voice_clarity"]
            similarity = min(1.0, 0.5 + clarity * 0.5)
        
        if "energy" in characteristics:
            # High energy speakers get speaker boost
            energy = characteristics["energy"]
            use_speaker_boost = energy > 0.3
        
        return VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=style,
            use_speaker_boost=use_speaker_boost
        )
    
    def _get_voice_for_speaker(self, voice_id: Optional[str], speaker_profile: Optional[SpeakerProfile]) -> str:
        """Determine the appropriate voice ID for a speaker."""
        # If specific voice_id provided, use it
        if voice_id:
            return voice_id
        
        # If speaker profile with clone exists, use it
        if speaker_profile and speaker_profile.voice_clone_id:
            return speaker_profile.voice_clone_id
        
        # Check speaker mapping
        if speaker_profile and speaker_profile.speaker_id in self.speaker_voices:
            return self.speaker_voices[speaker_profile.speaker_id]
        
        # Default to a preset voice with gender-matching if possible
        if speaker_profile and speaker_profile.characteristics and "gender_likelihood" in speaker_profile.characteristics:
            gender_likelihood = speaker_profile.characteristics["gender_likelihood"]
            
            if gender_likelihood < 0.3:  # Likely male
                return "pNInz6obpgDQGcFmaJgB"  # Adam (male)
            elif gender_likelihood > 0.7:  # Likely female
                return "21m00Tcm4TlvDq8ikWAM"  # Rachel (female)
        
        # Default voice if all else fails
        return "pNInz6obpgDQGcFmaJgB"  # Adam
    
    async def get_available_voices(self, include_library: bool = True) -> Dict[str, Any]:
        """Get list of available voices, including voice library."""
        try:
            # Get voices from ElevenLabs
            api_voices = self.client.voices.get_all()
            
            voices = {
                voice.voice_id: {
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "preview_url": voice.preview_url,
                    "is_cloned": False,
                    "source": "elevenlabs"
                }
                for voice in api_voices.voices
            }
            
            # Add voice library
            if include_library:
                for voice_id, clone in self.voice_clones.items():
                    voices[voice_id] = {
                        "name": clone.name,
                        "category": "cloned",
                        "description": f"Cloned voice for speaker {clone.speaker_id}",
                        "is_cloned": True,
                        "speaker_id": clone.speaker_id,
                        "creation_time": clone.creation_time,
                        "quality": clone.metrics.get("estimated_quality", 0.0) if clone.metrics else 0.0,
                        "source": "library"
                    }
            
            return voices
            
        except Exception as e:
            logger.error(f"Error fetching available voices: {e}")
            raise
    
    async def analyze_voice_quality(self, audio_data: bytes, sample_rate: int) -> Dict[str, float]:
        """Analyze voice quality metrics from audio sample."""
        try:
            # Convert to AudioChunk for analysis
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            audio_chunk = AudioChunk(
                data=audio,
                sample_rate=sample_rate,
                timestamp=time.time(),
                chunk_id="quality_analysis"
            )
            
            # Signal-to-noise ratio (higher is better)
            signal = np.mean(audio**2)
            audio_filtered = audio - np.mean(audio)
            noise = np.mean(audio_filtered**2)
            snr = 10 * np.log10(signal / (noise + 1e-10))
            
            # Check for clipping (audio exceeding amplitude limits)
            clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)
            
            # Analyze dynamic range
            percentile_95 = np.percentile(np.abs(audio), 95)
            percentile_5 = np.percentile(np.abs(audio), 5)
            dynamic_range = percentile_95 / (percentile_5 + 1e-10)
            
            # Silence detection
            silence_threshold = 0.01
            is_silence = np.abs(audio) < silence_threshold
            silence_ratio = np.sum(is_silence) / len(audio)
            
            # Calculate overall quality score (0.0-1.0)
            snr_score = min(1.0, max(0.0, (snr - 10) / 50))
            clipping_score = 1.0 - min(1.0, clipping_ratio * 20)
            dynamic_score = min(1.0, max(0.0, (dynamic_range - 5) / 40))
            silence_score = 1.0 if silence_ratio < 0.3 else max(0.0, 1.0 - (silence_ratio - 0.3) * 2)
            
            overall_quality = (snr_score * 0.4 + 
                             clipping_score * 0.2 + 
                             dynamic_score * 0.2 + 
                             silence_score * 0.2)
            
            return {
                "overall_quality": float(overall_quality),
                "snr": float(snr),
                "clipping_ratio": float(clipping_ratio),
                "dynamic_range": float(dynamic_range),
                "silence_ratio": float(silence_ratio)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing voice quality: {e}")
            return {"overall_quality": 0.5}  # Default moderate quality
    
    async def update_voice_settings(self, voice_id: str, settings_update: Dict[str, Any]) -> bool:
        """Update voice settings for a cloned voice."""
        if voice_id not in self.voice_clones:
            logger.error(f"Voice ID {voice_id} not found in voice library")
            return False
        
        try:
            clone = self.voice_clones[voice_id]
            
            # Update settings
            current_settings = clone.voice_settings or {}
            for key, value in settings_update.items():
                if key in ["stability", "similarity_boost", "style", "use_speaker_boost"]:
                    current_settings[key] = value
            
            clone.voice_settings = current_settings
            self._save_voice_library()
            
            logger.info(f"Updated voice settings for {voice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating voice settings: {e}")
            return False
    
    def get_voice_for_speaker(self, speaker_id: str) -> Optional[str]:
        """Get the voice ID associated with a speaker."""
        return self.speaker_voices.get(speaker_id)
    
    def get_voice_clone_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a voice clone."""
        if voice_id in self.voice_clones:
            clone = self.voice_clones[voice_id]
            return {
                "voice_id": clone.voice_id,
                "speaker_id": clone.speaker_id,
                "name": clone.name,
                "creation_time": clone.creation_time,
                "samples_duration": clone.samples_duration,
                "voice_settings": clone.voice_settings,
                "metrics": clone.metrics,
                "last_used": clone.last_used
            }
        return None
    
    def list_voices_for_speaker(self, speaker_id: str) -> List[str]:
        """List all voice IDs associated with a speaker."""
        return [v_id for v_id, clone in self.voice_clones.items() 
                if clone.speaker_id == speaker_id]