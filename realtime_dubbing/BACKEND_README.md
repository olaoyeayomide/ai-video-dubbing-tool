# Real-Time AI Dubbing System - Core Python Backend

This directory contains the core Python backend for the real-time AI dubbing system.

## Quick Start

```bash
# 1. Install dependencies
python quick_start.py install

# 2. Setup environment
python quick_start.py setup

# 3. Configure API keys in .env
# Edit .env file with your Google Cloud and ElevenLabs API keys

# 4. Test the system
python quick_start.py test

# 5. Run the server
python quick_start.py run
```

## Project Structure

```
code/realtime_dubbing/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application with WebSocket support
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── models/
│   ├── __init__.py
│   └── audio_models.py      # Data models for audio processing
├── services/
│   ├── __init__.py
│   ├── speech_services.py   # Google Cloud Speech & Translation
│   ├── voice_services.py    # ElevenLabs voice synthesis
│   └── speaker_identification.py  # Speaker tracking
├── utils/
│   ├── __init__.py
│   └── audio_processing.py  # Main audio processing pipeline
├── static/
│   ├── js/                  # JavaScript files (for web interface)
│   └── css/                 # CSS files (for web interface)
├── requirements.txt         # Python dependencies
├── quick_start.py          # Setup and management script
├── test_backend.py         # Backend testing script
└── README.md               # This file
```

## Core Backend Components Completed ✅

### 1. FastAPI Server with WebSocket Support
- Real-time WebSocket communication
- REST API endpoints
- Connection management
- Session handling
- Built-in web interface for testing

### 2. Audio Processing Pipeline
- Real-time audio chunk processing
- Speech recognition integration
- Translation services
- Voice synthesis
- Speaker identification
- Voice cloning support

### 3. AI Services Integration
- **Google Cloud Speech-to-Text**: Streaming speech recognition
- **Google Cloud Translate**: Real-time translation
- **ElevenLabs**: Voice synthesis and cloning
- Optimized for low-latency processing

### 4. Speaker Identification System
- Automatic speaker detection using audio features
- MFCC and spectral analysis
- Voice embedding generation
- Speaker profile management
- Voice clone mapping

### 5. Configuration Management
- Environment-based configuration
- Secure API key handling
- Performance tuning parameters
- Audio processing settings

## Technical Capabilities

### Real-Time Processing
- Sub-second latency targeting
- Streaming audio processing
- Concurrent request handling
- WebSocket-based communication

### Voice Preservation
- Automatic speaker detection
- Voice embedding extraction
- ElevenLabs voice cloning integration
- Consistent voice mapping

### Audio Processing
- 16kHz sample rate processing
- Multiple audio format support
- Real-time format conversion
- Audio quality optimization

### Session Management
- Multi-session support
- Speaker tracking per session
- Processing statistics
- Session cleanup

## API Reference

### WebSocket Endpoints

**Connection**: `ws://localhost:8000/ws/{connection_id}/{session_id}`

**Message Types**:
- `audio_chunk`: Process audio data
- `start_dubbing`: Begin dubbing session
- `stop_dubbing`: End dubbing session
- `create_voice_clone`: Create voice clone for speaker
- `get_session_info`: Retrieve session information

### REST Endpoints

- `GET /`: Web interface
- `GET /api/health`: Health check
- `GET /api/voices`: Available voices
- `POST /api/upload-audio`: Upload audio file
- `GET /api/sessions/{session_id}`: Session information

## Performance Metrics

### Target Latencies
- Speech Recognition: <300ms
- Translation: <200ms
- Voice Synthesis: <400ms
- Total Pipeline: <1000ms

### Optimization Features
- Connection pooling
- Audio chunk caching
- Parallel processing
- Streaming inference
- Model quantization support

## Testing

The backend includes comprehensive testing:

### Automated Tests
```bash
python test_backend.py
```

Tests include:
- Audio processing pipeline
- Speaker identification
- Format conversion
- Session management
- Performance benchmarks

### Manual Testing
1. Start server: `python quick_start.py run`
2. Open http://localhost:8000
3. Test WebSocket connection
4. Send audio data for processing

## Next Steps

With the core Python backend complete, the next phases are:

1. **Browser Extension Development** (Step 6)
   - Chrome extension with audio capture
   - Web Audio API integration
   - Real-time audio replacement

2. **Voice Management Enhancement** (Step 7)
   - Advanced speaker tracking
   - Voice quality optimization
   - Actor voice library

3. **Performance Optimization** (Step 8)
   - Latency reduction
   - Resource optimization
   - Scalability improvements

## Requirements

- Python 3.12+
- Google Cloud Speech-to-Text API access
- Google Cloud Translation API access
- ElevenLabs API key
- 4GB+ RAM
- Stable internet connection

## License

MIT License - See main project LICENSE for details