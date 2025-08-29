#!/usr/bin/env python3
"""
Real-Time AI Dubbing System - Quick Start Script

This script helps you set up and test the real-time AI dubbing system.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "librosa",
        "numpy",
        "whisper",
        "elevenlabs",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")

    if not env_file.exists():
        print("Creating .env template...")
        template = """
# API Keys (Required)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GOOGLE_CLOUD_CREDENTIALS_PATH=/path/to/google/credentials.json

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Audio Configuration
SAMPLE_RATE=16000
CHUNK_SIZE=1024
MAX_CHUNK_DURATION=1.0

# Voice Settings
VOICE_SIMILARITY_THRESHOLD=0.8
VOICE_STABILITY=0.5
VOICE_CLARITY=0.75

# Performance
MAX_CONCURRENT_REQUESTS=10
CACHE_TTL=3600
"""
        env_file.write_text(template.strip())
        print("  Created .env template")
        print("  Please edit .env with your API keys")
        return False

    print("  ✓ .env file exists")
    return True


def install_packages():
    """Install required packages."""
    print("Installing packages...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("  ✓ Packages installed")
        return True
    except subprocess.CalledProcessError:
        print("  ✗ Failed to install packages")
        return False


def run_tests():
    """Run backend tests."""
    print("Running backend tests...")
    try:
        subprocess.run([sys.executable, "test_backend.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("  ✗ Tests failed")
        return False


def start_server():
    """Start the FastAPI server."""
    print("Starting server...")
    print("Server will be available at http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/{connection_id}/{session_id}")
    print("Press Ctrl+C to stop\n")

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "localhost",
                "--port",
                "8000",
                "--reload",
            ]
        )
    except KeyboardInterrupt:
        print("\nServer stopped")


def main():
    parser = argparse.ArgumentParser(description="Real-Time AI Dubbing System Setup")
    parser.add_argument(
        "action", choices=["setup", "test", "run", "install"], help="Action to perform"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force action even if checks fail"
    )

    args = parser.parse_args()

    print("Real-Time AI Dubbing System Setup")
    print("=" * 40)

    if args.action == "install":
        if install_packages():
            print("\n✓ Installation completed")
        else:
            print("\n✗ Installation failed")
            sys.exit(1)

    elif args.action == "setup":
        # Check and setup environment
        deps_ok = check_dependencies()
        env_ok = check_env_file()

        if not deps_ok and not args.force:
            print("\nPlease install missing dependencies first:")
            print("python quick_start.py install")
            sys.exit(1)

        if not env_ok and not args.force:
            print("\nPlease configure your .env file with API keys")
            sys.exit(1)

        print("\n✓ Setup completed")
        print("\nNext steps:")
        print("1. Edit .env with your API keys")
        print("2. Run tests: python quick_start.py test")
        print("3. Start server: python quick_start.py run")

    elif args.action == "test":
        if run_tests():
            print("\n✓ All tests passed")
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)

    elif args.action == "run":
        if not args.force:
            deps_ok = check_dependencies()
            if not deps_ok:
                print("\nDependencies missing. Run setup first.")
                sys.exit(1)

        start_server()


if __name__ == "__main__":
    main()
