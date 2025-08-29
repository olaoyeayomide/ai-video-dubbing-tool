from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import io
import json
import base64
import numpy as np
import time
import logging
from pydantic import BaseModel

from services.voice_management import VoiceManagementSystem
from services.wsi_speaker_identification import WSISpeakerIdentification
from services.enhanced_voice_service import EnhancedVoiceService
from models.audio_models import (
    VoiceCloneRequest,
    VoiceCloneResult,
    ActorProfile,
    AudioChunk,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-management", tags=["voice-management"])

# Service instances
voice_management = VoiceManagementSystem()
speaker_identification = WSISpeakerIdentification()
voice_service = EnhancedVoiceService()


# Pydantic models for API requests/responses
class ActorCreateRequest(BaseModel):
    name: str
    speaker_ids: Optional[List[str]] = None


class VoiceSampleUpload(BaseModel):
    speaker_id: str
    name: str
    description: Optional[str] = None
    actor_id: Optional[str] = None


class ActorVoiceAssociation(BaseModel):
    actor_id: str
    voice_id: str


class SpeakerActorAssociation(BaseModel):
    speaker_id: str
    actor_id: str


class ContentActorTracking(BaseModel):
    content_id: str
    actor_id: str


class ActorMetadataUpdate(BaseModel):
    actor_id: str
    metadata: Dict[str, Any]


@router.get("/actors")
async def get_all_actors():
    """Get all actor profiles."""
    try:
        actors = await voice_management.get_all_actors()
        return {
            "success": True,
            "actors": {
                actor_id: {
                    "actor_id": profile.actor_id,
                    "name": profile.name,
                    "voice_ids": profile.voice_ids,
                    "speaker_ids": profile.speaker_ids,
                    "metadata": profile.metadata,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                }
                for actor_id, profile in actors.items()
            },
        }
    except Exception as e:
        logger.error(f"Error retrieving actor profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actors", response_model=Dict[str, Any])
async def create_actor(request: ActorCreateRequest):
    """Create a new actor profile."""
    try:
        actor_id = await voice_management.create_actor_profile(
            name=request.name, speaker_ids=request.speaker_ids or []
        )

        return {
            "success": True,
            "actor_id": actor_id,
            "message": f"Created actor profile: {request.name}",
        }
    except Exception as e:
        logger.error(f"Error creating actor profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actors/{actor_id}/voices")
async def add_voice_to_actor(actor_id: str, voice_id: str):
    """Add a voice to an actor profile."""
    try:
        success = await voice_management.add_voice_to_actor(actor_id, voice_id)
        if not success:
            raise HTTPException(status_code=404, detail="Actor or voice not found")

        return {
            "success": True,
            "message": f"Added voice {voice_id} to actor {actor_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding voice to actor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actors/{actor_id}/speakers")
async def associate_speaker_with_actor(actor_id: str, speaker_id: str):
    """Associate a speaker with an actor profile."""
    try:
        success = await voice_management.associate_speaker_with_actor(
            speaker_id, actor_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Actor or speaker not found")

        return {
            "success": True,
            "message": f"Associated speaker {speaker_id} with actor {actor_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating speaker with actor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/{content_id}/actors/{actor_id}")
async def track_actor_in_content(content_id: str, actor_id: str):
    """Track an actor's appearance in content."""
    try:
        success = await voice_management.track_actor_in_content(content_id, actor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Actor not found")

        return {
            "success": True,
            "message": f"Tracked actor {actor_id} in content {content_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking actor in content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{content_id}/actors")
async def get_actors_in_content(content_id: str):
    """Get all actors tracked in a specific content."""
    try:
        actors = await voice_management.get_actors_in_content(content_id)
        return {
            "success": True,
            "actors": [
                {
                    "actor_id": actor.actor_id,
                    "name": actor.name,
                    "voice_ids": actor.voice_ids,
                    "speaker_ids": actor.speaker_ids,
                    "metadata": actor.metadata,
                }
                for actor in actors
            ],
        }
    except Exception as e:
        logger.error(f"Error retrieving actors in content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-clones", response_model=Dict[str, Any])
async def clone_voice(
    background_tasks: BackgroundTasks,
    speaker_id: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    actor_id: Optional[str] = Form(None),
    audio_files: List[UploadFile] = File(...),
):
    """Create a voice clone from audio samples."""
    try:
        # Process audio files
        audio_samples = []
        for file in audio_files:
            content = await file.read()
            audio_samples.append(content)

        if not audio_samples:
            raise HTTPException(status_code=400, detail="No audio samples provided")

        # Get speaker profile if available
        speaker_profile = speaker_identification.get_speaker_profile(speaker_id)

        # Start voice cloning (this can take time, so run in background)
        background_tasks.add_task(
            _process_voice_clone,
            speaker_id,
            name,
            description,
            audio_samples,
            speaker_profile,
            actor_id,
        )

        return {
            "success": True,
            "message": "Voice cloning started",
            "speaker_id": speaker_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting voice cloning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_voice_clone(
    speaker_id: str,
    name: str,
    description: Optional[str],
    audio_samples: List[bytes],
    speaker_profile: Optional[Any],
    actor_id: Optional[str],
):
    """Process voice clone in background."""
    try:
        # Create voice clone
        voice_id = await voice_service.create_professional_voice_clone(
            speaker_id=speaker_id,
            name=name,
            audio_samples=audio_samples,
            speaker_profile=speaker_profile,
        )

        # Associate with speaker in speaker identification service
        speaker_identification.set_voice_clone_id(speaker_id, voice_id)

        # If actor_id provided, associate with actor
        if actor_id:
            await voice_management.add_voice_to_actor(actor_id, voice_id)

        logger.info(f"Completed voice cloning: {voice_id} for speaker {speaker_id}")

    except Exception as e:
        logger.error(f"Error in background voice cloning: {e}")


@router.get("/voices")
async def get_available_voices():
    """Get all available voices including voice library."""
    try:
        voices = await voice_service.get_available_voices(include_library=True)
        return {"success": True, "voices": voices}
    except Exception as e:
        logger.error(f"Error retrieving available voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/{voice_id}")
async def get_voice_info(voice_id: str):
    """Get detailed information about a voice."""
    try:
        voice_info = voice_service.get_voice_clone_info(voice_id)
        if not voice_info:
            raise HTTPException(status_code=404, detail="Voice not found")

        return {"success": True, "voice": voice_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving voice info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/actors/{actor_id}/metadata")
async def update_actor_metadata(actor_id: str, update: ActorMetadataUpdate):
    """Update actor metadata."""
    try:
        if update.actor_id != actor_id:
            raise HTTPException(status_code=400, detail="Actor ID mismatch")

        success = await voice_management.update_actor_metadata(
            actor_id, update.metadata
        )
        if not success:
            raise HTTPException(status_code=404, detail="Actor not found")

        return {"success": True, "message": f"Updated metadata for actor {actor_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating actor metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-voice-quality")
async def analyze_voice_quality(audio_file: UploadFile = File(...)):
    """Analyze voice quality metrics from an audio sample."""
    try:
        content = await audio_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Assuming WAV format with 16-bit PCM at 16kHz
        metrics = await voice_service.analyze_voice_quality(content, 16000)

        return {"success": True, "metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing voice quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))
