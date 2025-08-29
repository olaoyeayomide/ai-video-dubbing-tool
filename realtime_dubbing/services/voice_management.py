import asyncio
import json
import os
import sys
import time
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import SpeakerProfile, AudioChunk
from services.wsi_speaker_identification import WSISpeakerIdentification
from services.enhanced_voice_service import EnhancedVoiceService
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ActorVoiceProfile:
    """Actor voice profile linking content to voice clones."""
    actor_id: str  # Unique identifier for the actor
    name: str  # Actor's name
    voice_ids: List[str]  # List of voice IDs (can have multiple per actor)
    speaker_ids: List[str]  # List of speaker IDs associated with this actor
    metadata: Dict[str, Any]  # Additional metadata (e.g., content appearances)
    created_at: float
    updated_at: float
    

class VoiceManagementSystem:
    """Advanced voice management system for preserving actor voices across content."""
    
    def __init__(self, 
                 data_dir: str = "data/voice_management",
                 speaker_service: Optional[WSISpeakerIdentification] = None,
                 voice_service: Optional[EnhancedVoiceService] = None):
        # Directory for persistent storage
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Actor voice profiles
        self.actor_profiles: Dict[str, ActorVoiceProfile] = {}
        
        # Speaker to actor mapping
        self.speaker_actor_map: Dict[str, str] = {}  # speaker_id -> actor_id
        
        # Content tracking
        self.content_actors: Dict[str, Set[str]] = {}  # content_id -> set of actor_ids
        
        # Services
        self.speaker_service = speaker_service or WSISpeakerIdentification()
        self.voice_service = voice_service or EnhancedVoiceService()
        
        # Load existing data
        self._load_actor_profiles()
    
    def _load_actor_profiles(self):
        """Load actor profiles from disk."""
        try:
            profiles_path = self.data_dir / "actor_profiles.json"
            if profiles_path.exists():
                with open(profiles_path, 'r') as f:
                    data = json.load(f)
                
                for actor_id, profile_data in data.get("actor_profiles", {}).items():
                    profile = ActorVoiceProfile(
                        actor_id=actor_id,
                        name=profile_data.get("name", ""),
                        voice_ids=profile_data.get("voice_ids", []),
                        speaker_ids=profile_data.get("speaker_ids", []),
                        metadata=profile_data.get("metadata", {}),
                        created_at=profile_data.get("created_at", 0),
                        updated_at=profile_data.get("updated_at", 0)
                    )
                    self.actor_profiles[actor_id] = profile
                
                # Load speaker-actor mapping
                for speaker_id, actor_id in data.get("speaker_actor_map", {}).items():
                    self.speaker_actor_map[speaker_id] = actor_id
                
                # Load content tracking
                for content_id, actor_ids in data.get("content_actors", {}).items():
                    self.content_actors[content_id] = set(actor_ids)
                
                logger.info(f"Loaded {len(self.actor_profiles)} actor profiles")
        except Exception as e:
            logger.error(f"Error loading actor profiles: {e}")
    
    def _save_actor_profiles(self):
        """Save actor profiles to disk."""
        try:
            profiles_path = self.data_dir / "actor_profiles.json"
            
            # Prepare data for serialization
            serialized_content_actors = {}
            for content_id, actor_ids in self.content_actors.items():
                serialized_content_actors[content_id] = list(actor_ids)
            
            data = {
                "actor_profiles": {
                    profile.actor_id: {
                        "name": profile.name,
                        "voice_ids": profile.voice_ids,
                        "speaker_ids": profile.speaker_ids,
                        "metadata": profile.metadata,
                        "created_at": profile.created_at,
                        "updated_at": profile.updated_at
                    }
                    for profile in self.actor_profiles.values()
                },
                "speaker_actor_map": self.speaker_actor_map,
                "content_actors": serialized_content_actors
            }
            
            with open(profiles_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.actor_profiles)} actor profiles")
        except Exception as e:
            logger.error(f"Error saving actor profiles: {e}")
    
    async def create_actor_profile(self, name: str, speaker_ids: List[str] = None) -> str:
        """Create a new actor profile."""
        try:
            # Generate actor ID
            actor_id = f"actor_{len(self.actor_profiles) + 1:03d}"
            
            # Create profile
            profile = ActorVoiceProfile(
                actor_id=actor_id,
                name=name,
                voice_ids=[],
                speaker_ids=speaker_ids or [],
                metadata={},
                created_at=time.time(),
                updated_at=time.time()
            )
            
            # Add to collection
            self.actor_profiles[actor_id] = profile
            
            # Update speaker-actor mapping
            for speaker_id in profile.speaker_ids:
                self.speaker_actor_map[speaker_id] = actor_id
            
            # Save changes
            self._save_actor_profiles()
            
            logger.info(f"Created actor profile: {actor_id} ({name})")
            return actor_id
            
        except Exception as e:
            logger.error(f"Error creating actor profile: {e}")
            raise
    
    async def associate_speaker_with_actor(self, speaker_id: str, actor_id: str) -> bool:
        """Associate a speaker with an actor profile."""
        try:
            if actor_id not in self.actor_profiles:
                logger.error(f"Actor ID {actor_id} not found")
                return False
            
            # Get speaker profile
            speaker_profile = self.speaker_service.get_speaker_profile(speaker_id)
            if not speaker_profile:
                logger.error(f"Speaker ID {speaker_id} not found")
                return False
            
            # Update actor profile
            profile = self.actor_profiles[actor_id]
            if speaker_id not in profile.speaker_ids:
                profile.speaker_ids.append(speaker_id)
                profile.updated_at = time.time()
            
            # Update speaker-actor mapping
            self.speaker_actor_map[speaker_id] = actor_id
            
            # Get any voice clone associated with this speaker
            voice_id = self.voice_service.get_voice_for_speaker(speaker_id)
            if voice_id and voice_id not in profile.voice_ids:
                profile.voice_ids.append(voice_id)
            
            # Save changes
            self._save_actor_profiles()
            
            logger.info(f"Associated speaker {speaker_id} with actor {actor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error associating speaker with actor: {e}")
            return False
    
    async def add_voice_to_actor(self, actor_id: str, voice_id: str) -> bool:
        """Add a voice to an actor profile."""
        try:
            if actor_id not in self.actor_profiles:
                logger.error(f"Actor ID {actor_id} not found")
                return False
            
            # Update actor profile
            profile = self.actor_profiles[actor_id]
            if voice_id not in profile.voice_ids:
                profile.voice_ids.append(voice_id)
                profile.updated_at = time.time()
                
                # Save changes
                self._save_actor_profiles()
                
                logger.info(f"Added voice {voice_id} to actor {actor_id}")
                return True
            return True  # Voice already in profile
            
        except Exception as e:
            logger.error(f"Error adding voice to actor: {e}")
            return False
    
    async def track_actor_in_content(self, content_id: str, actor_id: str) -> bool:
        """Track an actor's appearance in content."""
        try:
            if actor_id not in self.actor_profiles:
                logger.error(f"Actor ID {actor_id} not found")
                return False
            
            # Initialize content tracking if needed
            if content_id not in self.content_actors:
                self.content_actors[content_id] = set()
            
            # Add actor to content
            self.content_actors[content_id].add(actor_id)
            
            # Update actor metadata
            profile = self.actor_profiles[actor_id]
            if "content_appearances" not in profile.metadata:
                profile.metadata["content_appearances"] = []
            
            if content_id not in profile.metadata["content_appearances"]:
                profile.metadata["content_appearances"].append(content_id)
                profile.updated_at = time.time()
            
            # Save changes
            self._save_actor_profiles()
            
            logger.info(f"Tracked actor {actor_id} in content {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking actor in content: {e}")
            return False
    
    async def get_actor_for_speaker(self, speaker_id: str) -> Optional[ActorVoiceProfile]:
        """Get actor profile associated with a speaker."""
        actor_id = self.speaker_actor_map.get(speaker_id)
        if actor_id:
            return self.actor_profiles.get(actor_id)
        return None
    
    async def get_best_voice_for_actor(self, actor_id: str) -> Optional[str]:
        """Get the best voice for an actor based on quality metrics."""
        if actor_id not in self.actor_profiles:
            return None
        
        profile = self.actor_profiles[actor_id]
        if not profile.voice_ids:
            return None
        
        # If only one voice, return it
        if len(profile.voice_ids) == 1:
            return profile.voice_ids[0]
        
        # Get voice information to compare quality
        best_voice = None
        best_quality = -1
        
        for voice_id in profile.voice_ids:
            voice_info = self.voice_service.get_voice_clone_info(voice_id)
            if voice_info and voice_info.get("metrics", {}).get("estimated_quality", 0) > best_quality:
                best_quality = voice_info["metrics"]["estimated_quality"]
                best_voice = voice_id
        
        return best_voice
    
    async def identify_speaker_with_actor_context(self, 
                                                audio_chunk: AudioChunk, 
                                                session_id: str,
                                                content_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Identify speaker with actor context awareness.
        
        Returns: (speaker_id, actor_id)
        """
        try:
            # First identify the speaker
            speaker_id = self.speaker_service.identify_speaker(audio_chunk, session_id)
            if not speaker_id:
                return None, None
            
            # Check if speaker is already associated with an actor
            actor_id = self.speaker_actor_map.get(speaker_id)
            
            # If content_id provided, check if we have actors tracked for this content
            if not actor_id and content_id and content_id in self.content_actors:
                # Get speaker profile for comparing with actors
                speaker_profile = self.speaker_service.get_speaker_profile(speaker_id)
                if speaker_profile and speaker_profile.voice_embedding is not None:
                    # Compare with all speakers from all actors in this content
                    best_match_actor = None
                    best_match_similarity = self.speaker_service.similarity_threshold - 0.05  # Slightly lower threshold
                    
                    for content_actor_id in self.content_actors[content_id]:
                        if content_actor_id in self.actor_profiles:
                            profile = self.actor_profiles[content_actor_id]
                            
                            # Check all speakers for this actor
                            for actor_speaker_id in profile.speaker_ids:
                                actor_speaker = self.speaker_service.get_speaker_profile(actor_speaker_id)
                                if actor_speaker and actor_speaker.voice_embedding is not None:
                                    # Calculate similarity
                                    similarity = np.dot(
                                        speaker_profile.voice_embedding, 
                                        actor_speaker.voice_embedding
                                    )
                                    
                                    if similarity > best_match_similarity:
                                        best_match_similarity = similarity
                                        best_match_actor = content_actor_id
                    
                    # If we found a good match, associate with that actor
                    if best_match_actor:
                        await self.associate_speaker_with_actor(speaker_id, best_match_actor)
                        actor_id = best_match_actor
            
            return speaker_id, actor_id
            
        except Exception as e:
            logger.error(f"Error in actor-aware speaker identification: {e}")
            return None, None
    
    async def get_all_actors(self) -> Dict[str, ActorVoiceProfile]:
        """Get all actor profiles."""
        return self.actor_profiles.copy()
    
    async def get_actors_in_content(self, content_id: str) -> List[ActorVoiceProfile]:
        """Get all actors tracked in a specific content."""
        if content_id not in self.content_actors:
            return []
        
        return [self.actor_profiles[actor_id] 
                for actor_id in self.content_actors[content_id] 
                if actor_id in self.actor_profiles]
    
    async def update_actor_metadata(self, actor_id: str, metadata_update: Dict[str, Any]) -> bool:
        """Update actor metadata."""
        if actor_id not in self.actor_profiles:
            logger.error(f"Actor ID {actor_id} not found")
            return False
        
        try:
            profile = self.actor_profiles[actor_id]
            
            # Update metadata
            for key, value in metadata_update.items():
                profile.metadata[key] = value
            
            profile.updated_at = time.time()
            
            # Save changes
            self._save_actor_profiles()
            
            logger.info(f"Updated metadata for actor {actor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating actor metadata: {e}")
            return False