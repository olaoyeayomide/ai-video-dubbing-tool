import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Optional, List, Tuple
import numpy as np
import librosa
import soundfile as sf
from io import BytesIO

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import (
    AudioChunk, 
    AudioFormat, 
    ProcessingRequest, 
    ProcessingResponse, 
    ProcessingStatus,
    SpeechRecognitionResult,
    TranslationResult,
    VoiceSynthesisResult
)
from services.speech_services import SpeechService, TranslationService
from services.enhanced_voice_service import EnhancedVoiceService
from services.wsi_speaker_identification import WSISpeakerIdentification
from services.voice_management import VoiceManagementSystem
from config.settings import settings

logger = logging.getLogger(__name__)

class AudioProcessingPipeline:
    """Main audio processing pipeline for real-time dubbing."""
    
    def __init__(self):
        # Initialize services
        self.speech_service = SpeechService()
        self.translate_service = TranslationService()
        self.voice_service = EnhancedVoiceService()
        self.speaker_service = WSISpeakerIdentification()
        self.voice_management = VoiceManagementSystem(
            speaker_service=self.speaker_service,
            voice_service=self.voice_service
        )
        
        # Processing state
        self.active_sessions: Dict[str, Dict] = {}
        self.processing_queue = asyncio.Queue()
        
    async def process_audio_chunk(self, request: ProcessingRequest) -> ProcessingResponse:
        """Process a single audio chunk through the complete pipeline."""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Processing audio chunk {request_id} for session {request.session_id}")
            
            # Step 1: Speaker Identification (with actor context if enabled)
            if request.actor_aware and request.content_id:
                # Use voice management for actor-aware speaker identification
                speaker_id, actor_id = await self.voice_management.identify_speaker_with_actor_context(
                    request.audio_chunk,
                    request.session_id,
                    request.content_id
                )
            else:
                # Use regular speaker identification
                speaker_id = self.speaker_service.identify_speaker(request.audio_chunk, request.session_id)
                actor_id = None
                
                # Try to find associated actor if speaker was identified
                if speaker_id:
                    actor_profile = await self.voice_management.get_actor_for_speaker(speaker_id)
                    actor_id = actor_profile.actor_id if actor_profile else None
            
            # Get speaker profile
            speaker_profile = self.speaker_service.get_speaker_profile(speaker_id) if speaker_id else None
            
            # Step 2: Speech Recognition
            speech_result = await self.speech_service.recognize_audio_chunk(
                request.audio_chunk.data,
                request.source_language or "auto"
            )
            
            if not speech_result.text.strip():
                # No speech detected, return empty response
                return ProcessingResponse(
                    request_id=request_id,
                    status=ProcessingStatus.COMPLETED,
                    processing_time=time.time() - start_time,
                    speaker_id=speaker_id,
                    actor_id=actor_id
                )
            
            # Step 3: Translation
            translation_result = await self.translate_service.translate_text(
                speech_result.text,
                request.target_language,
                speech_result.language if speech_result.language != "unknown" else None
            )
            
            # Step 4: Voice Synthesis (with advanced voice settings if preserve_voice enabled)
            voice_id = None
            if request.preserve_voice:
                # Try to get best voice for actor if actor was identified
                if actor_id:
                    voice_id = await self.voice_management.get_best_voice_for_actor(actor_id)
                
                # If no actor voice, try speaker's voice
                if not voice_id and speaker_profile and speaker_profile.voice_clone_id:
                    voice_id = speaker_profile.voice_clone_id
            
            synthesis_result = await self.voice_service.synthesize_speech(
                text=translation_result.translated_text,
                voice_id=voice_id,
                speaker_profile=speaker_profile if request.preserve_voice else None,
                optimize_settings=request.preserve_voice
            )
            
            # Step 5: Update session state
            self._update_session_state(
                session_id=request.session_id, 
                speaker_id=speaker_id, 
                actor_id=actor_id,
                speech_result=speech_result, 
                translation_result=translation_result
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Completed processing {request_id} in {processing_time:.3f}s")
            
            return ProcessingResponse(
                request_id=request_id,
                status=ProcessingStatus.COMPLETED,
                processed_audio=synthesis_result.audio_data,
                original_text=speech_result.text,
                translated_text=translation_result.translated_text,
                processing_time=processing_time,
                speaker_id=speaker_id,
                actor_id=actor_id,
                voice_id=synthesis_result.voice_id
            )
            
        except Exception as e:
            logger.error(f"Error processing audio chunk {request_id}: {e}")
            return ProcessingResponse(
                request_id=request_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _update_session_state(self, session_id: str, speaker_id: str, actor_id: Optional[str],
                            speech_result: SpeechRecognitionResult, 
                            translation_result: TranslationResult):
        """Update session state with processing results."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "speakers": set(),
                "actors": set(),
                "languages_detected": set(),
                "processing_count": 0,
                "created_at": time.time()
            }
        
        session = self.active_sessions[session_id]
        if speaker_id:
            session["speakers"].add(speaker_id)
        if actor_id:
            session["actors"].add(actor_id)
        session["languages_detected"].add(speech_result.language)
        session["processing_count"] += 1
        session["last_activity"] = time.time()
    
    def parse_audio_data(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> AudioChunk:
        """Parse audio data from bytes into AudioChunk."""
        try:
            # Load audio using soundfile
            audio_io = BytesIO(audio_data)
            data, sample_rate = sf.read(audio_io)
            
            # Ensure mono audio
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Resample if necessary
            if sample_rate != settings.sample_rate:
                data = librosa.resample(data, orig_sr=sample_rate, target_sr=settings.sample_rate)
                sample_rate = settings.sample_rate
            
            # Normalize audio
            if np.max(np.abs(data)) > 0:
                data = data / np.max(np.abs(data))
            
            return AudioChunk(
                data=data,
                sample_rate=sample_rate,
                timestamp=time.time(),
                chunk_id=str(uuid.uuid4()),
                format=format
            )
            
        except Exception as e:
            logger.error(f"Error parsing audio data: {e}")
            raise
    
    def audio_chunk_to_bytes(self, audio_chunk: AudioChunk, format: AudioFormat = AudioFormat.WAV) -> bytes:
        """Convert AudioChunk back to bytes."""
        try:
            output_io = BytesIO()
            
            # Convert to appropriate format
            if format == AudioFormat.WAV:
                sf.write(output_io, audio_chunk.data, audio_chunk.sample_rate, format='WAV')
            elif format == AudioFormat.MP3:
                # Note: soundfile doesn't support MP3 writing, would need additional library
                sf.write(output_io, audio_chunk.data, audio_chunk.sample_rate, format='WAV')
            else:
                sf.write(output_io, audio_chunk.data, audio_chunk.sample_rate, format='WAV')
            
            output_io.seek(0)
            return output_io.read()
            
        except Exception as e:
            logger.error(f"Error converting audio chunk to bytes: {e}")
            raise
    
    async def create_voice_clone(self, session_id: str, speaker_id: str, audio_samples: list[bytes], 
                                 name: Optional[str] = None, actor_id: Optional[str] = None) -> str:
        """Create a voice clone for a speaker with optional actor association."""
        try:
            # Get speaker profile
            speaker_profile = self.speaker_service.get_speaker_profile(speaker_id)
            if not speaker_profile:
                raise ValueError(f"Speaker {speaker_id} not found")
            
            # Create voice clone name
            clone_name = name or f"session_{session_id}_speaker_{speaker_id}"
            
            # Create professional voice clone using enhanced voice service
            voice_id = await self.voice_service.create_professional_voice_clone(
                speaker_id=speaker_id,
                name=clone_name,
                audio_samples=audio_samples,
                speaker_profile=speaker_profile
            )
            
            # Update speaker profile with clone ID
            self.speaker_service.set_voice_clone_id(speaker_id, voice_id)
            
            # If actor provided, associate with actor
            if actor_id:
                await self.voice_management.add_voice_to_actor(actor_id, voice_id)
            
            logger.info(f"Created voice clone {voice_id} for speaker {speaker_id}" + 
                      (f" and actor {actor_id}" if actor_id else ""))
            
            return voice_id
            
        except Exception as e:
            logger.error(f"Error creating voice clone: {e}")
            raise
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a processing session."""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                "session_id": session_id,
                "speakers": list(session["speakers"]),
                "actors": list(session.get("actors", [])),
                "languages_detected": list(session["languages_detected"]),
                "processing_count": session["processing_count"],
                "created_at": session["created_at"],
                "last_activity": session.get("last_activity", session["created_at"])
            }
        return None
    
    def cleanup_session(self, session_id: str):
        """Clean up session data."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
    
    def get_speaker_profiles(self, session_id: str) -> Dict:
        """Get all speaker profiles for a session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        profiles = {}
        for speaker_id in session["speakers"]:
            profile = self.speaker_service.get_speaker_profile(speaker_id)
            if profile:
                # Get actor info if available
                actor_profile = None
                actor_task = asyncio.create_task(
                    self.voice_management.get_actor_for_speaker(speaker_id)
                )
                try:
                    # We need to run this synchronously since we're in a sync method
                    loop = asyncio.get_event_loop()
                    actor_profile = loop.run_until_complete(actor_task)
                except Exception as e:
                    logger.error(f"Error getting actor for speaker {speaker_id}: {e}")
                
                profiles[speaker_id] = {
                    "speaker_id": profile.speaker_id,
                    "confidence": profile.confidence,
                    "voice_clone_id": profile.voice_clone_id,
                    "characteristics": profile.characteristics or {},
                    "actor_id": actor_profile.actor_id if actor_profile else None
                }
        
        return profiles
        
    async def get_actor_profiles(self, session_id: str) -> Dict:
        """Get all actor profiles for a session."""
        session = self.active_sessions.get(session_id)
        if not session or "actors" not in session:
            return {}
        
        profiles = {}
        for actor_id in session["actors"]:
            actor_profile = await self.voice_management.get_all_actors()
            if actor_id in actor_profile:
                profile = actor_profile[actor_id]
                profiles[actor_id] = {
                    "actor_id": profile.actor_id,
                    "name": profile.name,
                    "voice_ids": profile.voice_ids,
                    "speaker_ids": profile.speaker_ids,
                    "metadata": profile.metadata
                }
        
        return profiles