from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set, Tuple
from enum import Enum
import numpy as np
import time

class ProcessingStatus(Enum):
    """Status of audio processing pipeline."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"

@dataclass
class AudioChunk:
    """Represents a chunk of audio data."""
    data: np.ndarray
    sample_rate: int
    timestamp: float
    chunk_id: str
    format: AudioFormat = AudioFormat.WAV
    
@dataclass
class SpeechRecognitionResult:
    """Result from speech recognition service."""
    text: str
    confidence: float
    language: str
    speaker_id: Optional[str] = None
    timestamp: float = 0.0
    is_final: bool = True
    
@dataclass
class TranslationResult:
    """Result from translation service."""
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    
@dataclass
class VoiceSynthesisResult:
    """Result from voice synthesis service."""
    audio_data: bytes
    format: AudioFormat
    duration: float
    voice_id: str
    
@dataclass
class SpeakerProfile:
    """Speaker identification and voice profile."""
    speaker_id: str
    voice_embedding: np.ndarray
    voice_clone_id: Optional[str] = None
    confidence: float = 0.0
    characteristics: Dict[str, Any] = None
    
@dataclass
class VoiceCloneRequest:
    """Request for voice cloning."""
    speaker_id: str
    name: str
    audio_samples: List[bytes]
    description: Optional[str] = None
    session_id: Optional[str] = None
    speaker_profile: Optional[SpeakerProfile] = None

@dataclass
class VoiceCloneResult:
    """Result from voice cloning."""
    voice_id: str
    speaker_id: str
    name: str
    success: bool
    quality_score: float
    message: Optional[str] = None

@dataclass
class ActorProfile:
    """Actor profile for voice management."""
    actor_id: str
    name: str
    voice_ids: List[str] = field(default_factory=list)
    speaker_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

@dataclass
class VoiceQualityMetrics:
    """Voice quality metrics."""
    overall_quality: float
    signal_to_noise: Optional[float] = None
    clarity: Optional[float] = None
    stability: Optional[float] = None
    naturalness: Optional[float] = None
    additional_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class ProcessingRequest:
    """Request for audio processing pipeline."""
    session_id: str
    audio_chunk: AudioChunk
    source_language: Optional[str] = None
    target_language: str = "en"
    preserve_voice: bool = True
    content_id: Optional[str] = None
    actor_aware: bool = False
    
@dataclass
class ProcessingResponse:
    """Response from audio processing pipeline."""
    request_id: str
    status: ProcessingStatus
    processed_audio: Optional[bytes] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None
    speaker_id: Optional[str] = None
    actor_id: Optional[str] = None
    voice_id: Optional[str] = None