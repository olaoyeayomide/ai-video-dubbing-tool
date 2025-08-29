import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import SpeakerProfile, AudioChunk
from config.settings import settings

logger = logging.getLogger(__name__)

class SpeakerIdentificationService:
    """Service for identifying and tracking speakers across audio."""
    
    def __init__(self):
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
        self.speaker_embeddings: List[np.ndarray] = []
        self.speaker_ids: List[str] = []
        self.similarity_threshold = settings.voice_similarity_threshold
    
    def extract_speaker_embedding(self, audio_chunk: AudioChunk) -> np.ndarray:
        """Extract speaker embedding from audio chunk using librosa features."""
        try:
            # Extract various audio features that characterize speaker identity
            
            # MFCC features (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(
                y=audio_chunk.data, 
                sr=audio_chunk.sample_rate, 
                n_mfcc=13
            )
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_chunk.data, sr=audio_chunk.sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_chunk.data, sr=audio_chunk.sample_rate)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_chunk.data, sr=audio_chunk.sample_rate)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_chunk.data)
            
            # Pitch features
            pitches, magnitudes = librosa.piptrack(y=audio_chunk.data, sr=audio_chunk.sample_rate)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # Combine all features into a single embedding vector
            embedding = np.concatenate([
                mfcc_mean,
                mfcc_std,
                [np.mean(spectral_centroids)],
                [np.mean(spectral_rolloff)],
                [np.mean(spectral_bandwidth)],
                [np.mean(zcr)],
                [pitch_mean]
            ])
            
            # Normalize the embedding
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error extracting speaker embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(29)  # 13 + 13 + 1 + 1 + 1 + 1 + 1
    
    def identify_speaker(self, audio_chunk: AudioChunk) -> Optional[str]:
        """Identify speaker from audio chunk."""
        try:
            # Extract embedding for the current audio
            current_embedding = self.extract_speaker_embedding(audio_chunk)
            
            if len(self.speaker_embeddings) == 0:
                # First speaker
                speaker_id = f"speaker_001"
                self._add_new_speaker(speaker_id, current_embedding, audio_chunk)
                return speaker_id
            
            # Calculate similarity with existing speakers
            similarities = []
            for existing_embedding in self.speaker_embeddings:
                similarity = cosine_similarity(
                    current_embedding.reshape(1, -1),
                    existing_embedding.reshape(1, -1)
                )[0][0]
                similarities.append(similarity)
            
            # Find best match
            max_similarity = max(similarities)
            best_match_idx = similarities.index(max_similarity)
            
            if max_similarity >= self.similarity_threshold:
                # Match found
                speaker_id = self.speaker_ids[best_match_idx]
                self._update_speaker_profile(speaker_id, current_embedding)
                return speaker_id
            else:
                # New speaker
                speaker_id = f"speaker_{len(self.speaker_embeddings) + 1:03d}"
                self._add_new_speaker(speaker_id, current_embedding, audio_chunk)
                return speaker_id
                
        except Exception as e:
            logger.error(f"Error identifying speaker: {e}")
            return None
    
    def _add_new_speaker(self, speaker_id: str, embedding: np.ndarray, audio_chunk: AudioChunk):
        """Add a new speaker to the tracking system."""
        # Create speaker profile
        characteristics = self._analyze_voice_characteristics(audio_chunk)
        
        profile = SpeakerProfile(
            speaker_id=speaker_id,
            voice_embedding=embedding,
            confidence=1.0,
            characteristics=characteristics
        )
        
        # Store in tracking lists
        self.speaker_profiles[speaker_id] = profile
        self.speaker_embeddings.append(embedding)
        self.speaker_ids.append(speaker_id)
        
        logger.info(f"Added new speaker: {speaker_id}")
    
    def _update_speaker_profile(self, speaker_id: str, new_embedding: np.ndarray):
        """Update existing speaker profile with new embedding."""
        if speaker_id in self.speaker_profiles:
            profile = self.speaker_profiles[speaker_id]
            
            # Exponential moving average for embedding update
            alpha = 0.1  # Learning rate
            profile.voice_embedding = (1 - alpha) * profile.voice_embedding + alpha * new_embedding
            
            # Update confidence (simplified)
            profile.confidence = min(1.0, profile.confidence + 0.05)
    
    def _analyze_voice_characteristics(self, audio_chunk: AudioChunk) -> Dict[str, float]:
        """Analyze voice characteristics for speaker profiling."""
        try:
            # Pitch analysis
            pitches, magnitudes = librosa.piptrack(y=audio_chunk.data, sr=audio_chunk.sample_rate)
            valid_pitches = pitches[pitches > 0]
            
            pitch_mean = np.mean(valid_pitches) if len(valid_pitches) > 0 else 0
            pitch_variance = np.var(valid_pitches) if len(valid_pitches) > 0 else 0
            
            # Energy analysis
            energy = np.sum(audio_chunk.data ** 2) / len(audio_chunk.data)
            
            # Spectral characteristics
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(
                y=audio_chunk.data, sr=audio_chunk.sample_rate
            ))
            
            # Speaking rate (approximate)
            onset_frames = librosa.onset.onset_detect(
                y=audio_chunk.data, sr=audio_chunk.sample_rate
            )
            speaking_rate = len(onset_frames) / (len(audio_chunk.data) / audio_chunk.sample_rate)
            
            return {
                "pitch_mean": float(pitch_mean),
                "pitch_variance": float(pitch_variance),
                "energy_level": float(energy),
                "spectral_centroid": float(spectral_centroid),
                "speaking_rate": float(speaking_rate)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing voice characteristics: {e}")
            return {}
    
    def get_speaker_profile(self, speaker_id: str) -> Optional[SpeakerProfile]:
        """Get speaker profile by ID."""
        return self.speaker_profiles.get(speaker_id)
    
    def set_voice_clone_id(self, speaker_id: str, voice_clone_id: str):
        """Associate a voice clone ID with a speaker."""
        if speaker_id in self.speaker_profiles:
            self.speaker_profiles[speaker_id].voice_clone_id = voice_clone_id
            logger.info(f"Associated voice clone {voice_clone_id} with speaker {speaker_id}")
    
    def get_all_speakers(self) -> Dict[str, SpeakerProfile]:
        """Get all tracked speakers."""
        return self.speaker_profiles.copy()
    
    def reset_speakers(self):
        """Reset all speaker tracking data."""
        self.speaker_profiles.clear()
        self.speaker_embeddings.clear()
        self.speaker_ids.clear()
        logger.info("Reset all speaker tracking data")