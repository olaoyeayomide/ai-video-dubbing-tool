#!/usr/bin/env python3
"""
Simple import test for the real-time dubbing system.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test all the main imports."""
    print("Testing imports...")

    try:
        print("  Testing FastAPI...")
        from fastapi import FastAPI

        print("    ✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"    ✗ FastAPI import failed: {e}")
        return False

    try:
        print("  Testing audio models...")
        from models.audio_models import AudioChunk, AudioFormat

        print("    ✓ Audio models imported successfully")
    except ImportError as e:
        print(f"    ✗ Audio models import failed: {e}")
        return False

    try:
        print("  Testing audio processing...")
        from utils.audio_processing import AudioProcessingPipeline

        print("    ✓ Audio processing imported successfully")
    except ImportError as e:
        print(f"    ✗ Audio processing import failed: {e}")
        return False

    try:
        print("  Testing voice management...")
        from services.voice_management import VoiceManagementSystem

        print("    ✓ Voice management imported successfully")
    except ImportError as e:
        print(f"    ✗ Voice management import failed: {e}")
        return False

    try:
        print("  Testing speaker identification...")
        from services.wsi_speaker_identification import WSISpeakerIdentification

        print("    ✓ Speaker identification imported successfully")
    except ImportError as e:
        print(f"    ✗ Speaker identification import failed: {e}")
        return False

    try:
        print("  Testing voice services...")
        from services.enhanced_voice_service import EnhancedVoiceService

        print("    ✓ Voice services imported successfully")
    except ImportError as e:
        print(f"    ✗ Voice services import failed: {e}")
        return False

    try:
        print("  Testing settings...")
        from config.settings import settings

        print("    ✓ Settings imported successfully")
    except ImportError as e:
        print(f"    ✗ Settings import failed: {e}")
        return False

    try:
        print("  Testing main app...")
        from app.main import app

        print("    ✓ Main app imported successfully")
    except ImportError as e:
        print(f"    ✗ Main app import failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print("Real-Time AI Dubbing System - Import Test")
    print("=" * 50)

    success = test_imports()

    if success:
        print("\n✓ All imports successful! The system is ready to run.")
    else:
        print("\n✗ Some imports failed. Please check the errors above.")
        sys.exit(1)
