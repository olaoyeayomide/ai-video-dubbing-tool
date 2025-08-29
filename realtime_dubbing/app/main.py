from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import logging
import uuid
from typing import Dict, List
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.audio_models import (
    ProcessingRequest, 
    AudioChunk, 
    AudioFormat, 
    ProcessingStatus
)
from utils.audio_processing import AudioProcessingPipeline
from config.settings import settings
from app.voice_management_api import router as voice_management_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Real-Time AI Dubbing API",
    description="Real-time audio processing and dubbing service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include voice management router
app.include_router(voice_management_router)

# Global instances
audio_pipeline = AudioProcessingPipeline()
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, List[str]] = {}  # session_id -> [connection_ids]
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
    
    def disconnect(self, connection_id: str, session_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id in self.session_connections:
            if connection_id in self.session_connections[session_id]:
                self.session_connections[session_id].remove(connection_id)
            
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
                # Clean up session data
                audio_pipeline.cleanup_session(session_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await websocket.send_text(json.dumps(message))
    
    async def broadcast_to_session(self, message: dict, session_id: str):
        if session_id in self.session_connections:
            for connection_id in self.session_connections[session_id]:
                await self.send_personal_message(message, connection_id)

manager = ConnectionManager()

@app.get("/voice-management")
async def voice_management_page():
    """Serve the voice management web interface."""
    return FileResponse("static/voice_management.html")

@app.get("/")
async def read_root():
    """Serve the main web interface."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-Time AI Dubbing</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            button { padding: 10px 20px; margin: 5px; }
            #log { height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Real-Time AI Dubbing System</h1>
            <div id="status" class="status disconnected">Disconnected</div>
            
            <h2>Controls</h2>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
            <button onclick="startDubbing()">Start Dubbing</button>
            <button onclick="stopDubbing()">Stop Dubbing</button>
            
            <h2>Session Info</h2>
            <div id="sessionInfo"></div>
            
            <h2>Activity Log</h2>
            <div id="log"></div>
        </div>
        
        <script>
            let socket = null;
            let sessionId = null;
            
            function updateStatus(connected) {
                const status = document.getElementById('status');
                if (connected) {
                    status.textContent = 'Connected';
                    status.className = 'status connected';
                } else {
                    status.textContent = 'Disconnected';
                    status.className = 'status disconnected';
                }
            }
            
            function log(message) {
                const logDiv = document.getElementById('log');
                const timestamp = new Date().toLocaleTimeString();
                logDiv.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            function connect() {
                sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
                const connectionId = 'conn_' + Math.random().toString(36).substr(2, 9);
                
                socket = new WebSocket(`ws://localhost:8000/ws/${connectionId}/${sessionId}`);
                
                socket.onopen = function(event) {
                    updateStatus(true);
                    log('Connected to dubbing service');
                };
                
                socket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    log(`Received: ${JSON.stringify(data, null, 2)}`);
                    
                    if (data.type === 'session_info') {
                        updateSessionInfo(data.data);
                    }
                };
                
                socket.onclose = function(event) {
                    updateStatus(false);
                    log('Disconnected from dubbing service');
                };
                
                socket.onerror = function(error) {
                    log('WebSocket error: ' + error);
                };
            }
            
            function disconnect() {
                if (socket) {
                    socket.close();
                    socket = null;
                }
            }
            
            function startDubbing() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'start_dubbing',
                        target_language: 'en',
                        preserve_voice: true
                    }));
                    log('Started dubbing session');
                } else {
                    log('Not connected to service');
                }
            }
            
            function stopDubbing() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'stop_dubbing'
                    }));
                    log('Stopped dubbing session');
                } else {
                    log('Not connected to service');
                }
            }
            
            function updateSessionInfo(info) {
                const sessionDiv = document.getElementById('sessionInfo');
                sessionDiv.innerHTML = `
                    <p><strong>Session ID:</strong> ${info.session_id || sessionId}</p>
                    <p><strong>Speakers:</strong> ${info.speakers ? info.speakers.join(', ') : 'None'}</p>
                    <p><strong>Languages:</strong> ${info.languages_detected ? info.languages_detected.join(', ') : 'None'}</p>
                    <p><strong>Processing Count:</strong> ${info.processing_count || 0}</p>
                `;
            }
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws/{connection_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str, session_id: str):
    """WebSocket endpoint for real-time audio processing."""
    await manager.connect(websocket, connection_id, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                # Process audio chunk
                await handle_audio_chunk(message, session_id, connection_id)
            
            elif message_type == "start_dubbing":
                # Start dubbing session
                await handle_start_dubbing(message, session_id, connection_id)
            
            elif message_type == "stop_dubbing":
                # Stop dubbing session
                await handle_stop_dubbing(session_id, connection_id)
            
            elif message_type == "get_session_info":
                # Get session information
                await handle_get_session_info(session_id, connection_id)
            
            elif message_type == "create_voice_clone":
                # Create voice clone
                await handle_create_voice_clone(message, session_id, connection_id)
            
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, connection_id)
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": str(e)
        }, connection_id)
        manager.disconnect(connection_id, session_id)

async def handle_audio_chunk(message: dict, session_id: str, connection_id: str):
    """Handle incoming audio chunk for processing."""
    try:
        # Extract audio data (base64 encoded)
        import base64
        audio_data = base64.b64decode(message["audio_data"])
        
        # Parse audio chunk
        audio_chunk = audio_pipeline.parse_audio_data(audio_data)
        
        # Create processing request
        request = ProcessingRequest(
            session_id=session_id,
            audio_chunk=audio_chunk,
            source_language=message.get("source_language"),
            target_language=message.get("target_language", "en"),
            preserve_voice=message.get("preserve_voice", True)
        )
        
        # Process audio
        response = await audio_pipeline.process_audio_chunk(request)
        
        # Send response back to client
        response_message = {
            "type": "audio_response",
            "request_id": response.request_id,
            "status": response.status.value,
            "processing_time": response.processing_time
        }
        
        if response.processed_audio:
            # Encode processed audio as base64
            response_message["processed_audio"] = base64.b64encode(response.processed_audio).decode()
        
        if response.original_text:
            response_message["original_text"] = response.original_text
        
        if response.translated_text:
            response_message["translated_text"] = response.translated_text
        
        if response.error_message:
            response_message["error"] = response.error_message
        
        await manager.send_personal_message(response_message, connection_id)
        
    except Exception as e:
        logger.error(f"Error handling audio chunk: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        }, connection_id)

async def handle_start_dubbing(message: dict, session_id: str, connection_id: str):
    """Handle start dubbing request."""
    try:
        await manager.send_personal_message({
            "type": "dubbing_started",
            "session_id": session_id,
            "target_language": message.get("target_language", "en"),
            "preserve_voice": message.get("preserve_voice", True)
        }, connection_id)
        
        # Also send session info
        await handle_get_session_info(session_id, connection_id)
        
    except Exception as e:
        logger.error(f"Error starting dubbing: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Start dubbing error: {str(e)}"
        }, connection_id)

async def handle_stop_dubbing(session_id: str, connection_id: str):
    """Handle stop dubbing request."""
    try:
        await manager.send_personal_message({
            "type": "dubbing_stopped",
            "session_id": session_id
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Error stopping dubbing: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Stop dubbing error: {str(e)}"
        }, connection_id)

async def handle_get_session_info(session_id: str, connection_id: str):
    """Handle get session info request."""
    try:
        session_info = audio_pipeline.get_session_info(session_id)
        speaker_profiles = audio_pipeline.get_speaker_profiles(session_id)
        
        await manager.send_personal_message({
            "type": "session_info",
            "data": {
                **(session_info or {}),
                "speaker_profiles": speaker_profiles
            }
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Session info error: {str(e)}"
        }, connection_id)

async def handle_create_voice_clone(message: dict, session_id: str, connection_id: str):
    """Handle create voice clone request."""
    try:
        speaker_id = message["speaker_id"]
        audio_samples_b64 = message["audio_samples"]  # List of base64 encoded audio
        
        # Decode audio samples
        import base64
        audio_samples = [base64.b64decode(sample) for sample in audio_samples_b64]
        
        # Create voice clone
        voice_clone_id = await audio_pipeline.create_voice_clone(
            session_id, speaker_id, audio_samples
        )
        
        await manager.send_personal_message({
            "type": "voice_clone_created",
            "speaker_id": speaker_id,
            "voice_clone_id": voice_clone_id
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Error creating voice clone: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Voice clone error: {str(e)}"
        }, connection_id)

# REST API endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/voices")
async def get_available_voices():
    """Get available voices for synthesis."""
    try:
        voices = await audio_pipeline.voice_service.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for processing."""
    try:
        audio_data = await file.read()
        audio_chunk = audio_pipeline.parse_audio_data(audio_data)
        
        return {
            "chunk_id": audio_chunk.chunk_id,
            "duration": len(audio_chunk.data) / audio_chunk.sample_rate,
            "sample_rate": audio_chunk.sample_rate
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    session_info = audio_pipeline.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    speaker_profiles = audio_pipeline.get_speaker_profiles(session_id)
    return {
        **session_info,
        "speaker_profiles": speaker_profiles
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )