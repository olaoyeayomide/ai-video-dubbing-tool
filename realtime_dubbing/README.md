# Real-Time AI Dubbing System

A powerful real-time AI dubbing system that automatically translates and voices foreign-language content into your preferred language with voice preservation.

## Features

- **Real-time Processing**: Sub-second latency for immediate dubbing
- **Voice Preservation**: Maintains original actor voices through AI cloning
- **Universal Compatibility**: Works with any streaming platform via browser extension
- **Multi-language Support**: Automatic language detection and translation
- **Speaker Identification**: Tracks multiple speakers throughout content
- **High Quality**: Professional-grade voice synthesis and translation

## Architecture

### Core Components

1. **Python Backend**: FastAPI server with WebSocket support
2. **Audio Processing Pipeline**: Real-time speech recognition, translation, and synthesis
3. **Voice Management**: Speaker identification and voice cloning
4. **Browser Extension**: Audio capture and real-time replacement
5. **AI Services**: Google Cloud Speech/Translate + ElevenLabs voice synthesis

### Technology Stack

- **Backend**: Python 3.12, FastAPI, WebSockets
- **Audio Processing**: librosa, soundfile, numpy
- **AI Services**: Google Cloud Speech-to-Text, Google Translate, ElevenLabs
- **Real-time**: WebSocket communication, streaming audio
- **Browser**: Chrome Extension with Web Audio API

## Installation

### Prerequisites

1. Python 3.12+
2. Google Cloud account with Speech-to-Text and Translation APIs enabled
3. ElevenLabs API account
4. Chrome browser for extension

### Backend Setup

1. **Clone and install dependencies**:

   ```bash
   cd code/realtime_dubbing
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file:

   ```env
   # API Keys
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   GOOGLE_CLOUD_CREDENTIALS_PATH=/path/to/google/credentials.json

   # Server Configuration
   HOST=localhost
   PORT=8000
   DEBUG=true

   # Audio Configuration
   SAMPLE_RATE=16000
   CHUNK_SIZE=1024

   # Voice Settings
   VOICE_SIMILARITY_THRESHOLD=0.8
   VOICE_STABILITY=0.5
   VOICE_CLARITY=0.75
   ```

3. **Set up Google Cloud credentials**:

   - Download your Google Cloud service account key
   - Set the `GOOGLE_CLOUD_CREDENTIALS_PATH` environment variable

4. **Run the server**:
   ```bash
   python -m app.main
   ```

## Usage

### Web Interface

1. Start the backend server
2. Open http://localhost:8000 in your browser
3. Click "Connect" to establish WebSocket connection
4. Click "Start Dubbing" to begin processing

### WebSocket API

Connect to `ws://localhost:8000/ws/{connection_id}/{session_id}`

#### Message Types

**Audio Processing**:

```json
{
  "type": "audio_chunk",
  "audio_data": "base64_encoded_audio",
  "source_language": "auto",
  "target_language": "en",
  "preserve_voice": true
}
```

**Start Dubbing**:

```json
{
  "type": "start_dubbing",
  "target_language": "en",
  "preserve_voice": true
}
```

**Create Voice Clone**:

```json
{
  "type": "create_voice_clone",
  "speaker_id": "speaker_001",
  "audio_samples": ["base64_audio1", "base64_audio2"]
}
```

### REST API

**Health Check**:

```bash
GET /api/health
```

**Get Available Voices**:

```bash
GET /api/voices
```

**Upload Audio**:

```bash
POST /api/upload-audio
Content-Type: multipart/form-data
```

**Get Session Info**:

```bash
GET /api/sessions/{session_id}
```

## Performance Optimization

### Latency Targets

- Speech Recognition: <300ms
- Translation: <200ms
- Voice Synthesis: <400ms
- Total Pipeline: <1000ms

### Optimization Strategies

1. **Streaming Processing**: Process audio chunks in real-time
2. **Connection Pooling**: Pre-established AI service connections
3. **Caching**: Voice models and common translations
4. **Parallel Execution**: Concurrent API calls
5. **Model Quantization**: Optimized inference performance

## Voice Management

### Advanced Speaker Detection

The system automatically identifies different speakers using:

- WSI (Whisper Speaker Identification) framework
- 256-dimensional speaker embeddings
- Cross-lingual speaker identification
- Session context awareness

### Actor Voice Preservation

- Creates actor profiles to maintain consistent voice mapping
- Tracks actors across different content
- Automatically associates new speakers with existing actors
- Preserves emotional characteristics and speaking style

### Voice Clone Management

- Professional voice clones with quality metrics
- Voice settings optimization for natural output
- Voice sample management and analysis
- Voice preview and testing capabilities

### Voice Management Interface

Browse to `/voice-management` to access:

- Actor profile management
- Voice library browsing
- Voice clone creation
- Speaker association tools

## Browser Extension Integration

### Audio Capture

- Uses Chrome's `tabCapture` API
- Real-time audio stream processing
- Cross-browser compatibility layers

### Audio Replacement

- Web Audio API manipulation
- Real-time audio track substitution
- Seamless playback integration

### Privacy & Legal

- Respects DRM protection
- No audio storage or recording
- Legal compliance guidelines

## Configuration

### Audio Settings

```python
# Sample rate for processing
SAMPLE_RATE = 16000

# Audio chunk size for real-time processing
CHUNK_SIZE = 1024

# Maximum chunk duration
MAX_CHUNK_DURATION = 1.0  # seconds
```

### Voice Settings

```python
# Voice similarity threshold for speaker matching
VOICE_SIMILARITY_THRESHOLD = 0.8

# Voice stability (0.0-1.0)
VOICE_STABILITY = 0.5

# Voice clarity (0.0-1.0)
VOICE_CLARITY = 0.75
```

### Performance Settings

```python
# Maximum concurrent processing requests
MAX_CONCURRENT_REQUESTS = 10

# Cache TTL for translations and voice models
CACHE_TTL = 3600  # seconds
```

## Monitoring & Logging

### Metrics Tracked

- Processing latency per component
- Audio quality metrics
- Voice similarity scores
- Session statistics
- Error rates

### Logging

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Component-specific loggers
logger = logging.getLogger(__name__)
```

## Development

### Project Structure

```
code/realtime_dubbing/
├── app/
│   └── main.py              # FastAPI application
├── config/
│   └── settings.py          # Configuration settings
├── models/
│   └── audio_models.py      # Data models
├── services/
│   ├── speech_services.py   # Speech recognition & translation
│   ├── voice_services.py    # Voice synthesis & cloning
│   └── speaker_identification.py  # Speaker tracking
├── utils/
│   └── audio_processing.py  # Audio processing pipeline
└── static/
    ├── js/                  # JavaScript files
    └── css/                 # CSS files
```

### Testing

```bash
# Run with audio file
python test_audio.py sample.wav

# WebSocket testing
python test_websocket.py

# Load testing
python load_test.py
```

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "app.main"]
```

### Production Considerations

- Use production ASGI server (Gunicorn + Uvicorn)
- Configure proper CORS settings
- Set up SSL/TLS certificates
- Implement rate limiting
- Monitor resource usage

## Troubleshooting

### Common Issues

1. **Audio Quality Issues**

   - Check sample rate consistency
   - Verify audio format compatibility
   - Monitor processing latency

2. **API Errors**

   - Verify API keys are correctly set
   - Check service quotas and limits
   - Monitor network connectivity

3. **Performance Issues**
   - Monitor CPU/GPU usage
   - Check memory consumption
   - Optimize batch sizes

### Debug Mode

```bash
# Enable debug logging
DEBUG=true python -m app.main

# Verbose audio processing
AUDIO_DEBUG=true python -m app.main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:

- Create GitHub issues for bugs
- Check documentation for common solutions
- Review configuration settings

---

**Note**: This system is designed for legitimate use cases and educational purposes. Please respect content creators' rights and platform terms of service.
