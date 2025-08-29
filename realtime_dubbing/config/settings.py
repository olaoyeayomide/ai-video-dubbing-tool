from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os

class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Server Configuration
    host: str = "localhost"
    port: int = 8000
    debug: bool = True
    
    # API Keys (OpenAI no longer needed for local Whisper)
    # openai_api_key: Optional[str] = None  # Removed - using local Whisper now
    elevenlabs_api_key: Optional[str] = None
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Audio Processing Configuration
    sample_rate: int = 16000
    chunk_size: int = 1024
    max_chunk_duration: float = 1.0  # seconds
    
    # AI Service Configuration
    speech_recognition_language: str = "auto"
    target_language: str = "en"
    voice_synthesis_model: str = "eleven_multilingual_v2"
    
    # Performance Configuration
    max_concurrent_requests: int = 10
    cache_ttl: int = 3600  # seconds
    
    # Voice Management Configuration
    voice_library_dir: str = "data/voice_library"
    speaker_profiles_dir: str = "data/speaker_profiles"
    actor_profiles_dir: str = "data/voice_management"
    
    # Voice Cloning Configuration
    voice_similarity_threshold: float = 0.8
    voice_stability: float = 0.5
    voice_clarity: float = 0.75
    voice_sample_min_duration: float = 30.0  # seconds
    voice_quality_threshold: float = 0.6
    
    # Local Whisper Configuration (completely free)
    whisper_model: str = "base"  # Options: tiny, base, small, medium, large
    whisper_language: Optional[str] = None  # Auto-detect if None
    
    # Speaker Diarization Configuration
    max_speakers: int = 5
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    speaker_embedding_model: str = "pyannote/embedding"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()