// Installation and setup guide for the RealTime AI Dubbing extension

# RealTime AI Dubbing Extension Installation Guide

## Overview
This Chrome extension enables real-time AI dubbing for streaming content on supported platforms including Netflix, YouTube, Crunchyroll, and more.

## Installation Steps

### 1. Prepare the Extension Files
1. Ensure all extension files are in the `extension/` directory
2. Make sure the backend server is running (see backend setup guide)

### 2. Create Extension Icons
Create the following icon files in the `icons/` directory:
- `icon-16.png` (16x16 pixels)
- `icon-48.png` (48x48 pixels) 
- `icon-128.png` (128x128 pixels)

### 3. Load Extension in Chrome
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/` directory
5. The extension should appear in your extensions list

### 4. Configure Server Connection
1. Click the extension icon in Chrome toolbar
2. Set "Server URL" to match your backend server:
   - Local development: `ws://localhost:8000`
   - Production: `wss://your-domain.com`
3. Select your target language
4. Choose voice preservation mode

### 5. Test the Extension
1. Navigate to a supported streaming platform
2. Start playing video content
3. Click the extension icon and enable dubbing
4. The overlay should appear showing active status

## Supported Platforms
- Netflix
- YouTube
- Crunchyroll
- Hulu
- Disney+
- Amazon Prime Video
- Funimation
- HBO Max
- Twitch

## Troubleshooting

### Extension Not Loading
- Check that all required files are present
- Verify manifest.json syntax
- Check Chrome developer console for errors

### Audio Capture Issues
- Ensure microphone permissions are granted
- Check that video element is detected
- Verify Web Audio API support

### Server Connection Problems
- Verify backend server is running
- Check firewall settings
- Ensure WebSocket URL is correct

### Platform-Specific Issues
- Some platforms may block audio capture
- Try refreshing the page
- Check platform-specific content scripts

## Development Notes

### File Structure
```
extension/
├── manifest.json          # Extension manifest
├── popup.html             # Extension popup UI
├── popup.js              # Popup controller
├── background.js         # Service worker
├── content.js            # Content script
├── audio-processor.js    # Audio worklet processor
├── styles.css           # Extension styles
└── icons/               # Extension icons
    ├── icon-16.png
    ├── icon-48.png
    └── icon-128.png
```

### Key Features
- Real-time audio capture from video elements
- WebSocket communication with backend
- Platform-specific video element detection
- Audio visualization
- Settings persistence
- Error handling and notifications

### Security Considerations
- Extension requests minimal permissions
- Audio data sent to localhost by default
- No persistent storage of audio data
- Content Security Policy compliant

### Performance Optimization
- Small audio buffer sizes for low latency
- Efficient audio processing in worklet
- Minimal DOM manipulation
- Optimized WebSocket communication
