// Content script for RealTime AI Dubbing
class RTDContentScript {
  constructor() {
    this.isActive = false;
    this.settings = {
      targetLanguage: "en",
      serverUrl: "ws://localhost:8000",
      voicePreservation: "auto",
    };
    this.audioContext = null;
    this.websocket = null;
    this.mediaStream = null;
    this.audioProcessor = null;
    this.videoElement = null;
    this.overlayElement = null;
    this.audioVisualization = null;
    this.stats = {
      processedChunks: 0,
      averageLatency: 0,
      connectionStatus: "disconnected",
    };

    this.init();
  }

  async init() {
    await this.loadSettings();
    this.detectPlatform();
    this.setupMessageListeners();
    this.createOverlay();
    this.findVideoElement();

    // Wait for video element if not found immediately
    if (!this.videoElement) {
      this.waitForVideo();
    }
  }

  async loadSettings() {
    try {
      const result = await chrome.storage.sync.get([
        "isActive",
        "targetLanguage",
        "serverUrl",
        "voicePreservation",
      ]);

      this.isActive = result.isActive || false;
      this.settings.targetLanguage = result.targetLanguage || "en";
      this.settings.serverUrl = result.serverUrl || "ws://localhost:8000";
      this.settings.voicePreservation = result.voicePreservation || "auto";
    } catch (error) {
      console.error("RTD: Failed to load settings:", error);
    }
  }

  detectPlatform() {
    const hostname = window.location.hostname;
    let platform = "unknown";

    if (hostname.includes("netflix.com")) platform = "netflix";
    else if (hostname.includes("youtube.com")) platform = "youtube";
    else if (hostname.includes("crunchyroll.com")) platform = "crunchyroll";
    else if (hostname.includes("hulu.com")) platform = "hulu";
    else if (hostname.includes("disneyplus.com")) platform = "disneyplus";
    else if (hostname.includes("amazon.com")) platform = "amazon";
    else if (hostname.includes("funimation.com")) platform = "funimation";
    else if (hostname.includes("hbo.com")) platform = "hbo";
    else if (hostname.includes("twitch.tv")) platform = "twitch";

    document.body.setAttribute("data-platform", platform);
    this.platform = platform;
  }

  setupMessageListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true;
    });
  }

  async handleMessage(message, sender, sendResponse) {
    try {
      switch (message.action) {
        case "start_dubbing":
          await this.startDubbing(message.settings);
          sendResponse({ success: true });
          break;

        case "stop_dubbing":
          await this.stopDubbing();
          sendResponse({ success: true });
          break;

        case "update_settings":
          this.updateSettings(message.settings);
          sendResponse({ success: true });
          break;

        case "get_status":
          sendResponse({
            isActive: this.isActive,
            stats: this.stats,
            platform: this.platform,
          });
          break;

        default:
          sendResponse({ error: "Unknown action" });
      }
    } catch (error) {
      console.error("RTD: Message handler error:", error);
      sendResponse({ error: error.message });
    }
  }

  async startDubbing(settings) {
    try {
      this.settings = { ...this.settings, ...settings };

      // Find video element
      if (!this.videoElement) {
        await this.findVideoElement();
      }

      if (!this.videoElement) {
        throw new Error("No video element found on this page");
      }

      // Setup audio context and capture
      await this.setupAudioCapture();

      // Connect to backend server
      await this.connectToServer();

      this.isActive = true;
      document.body.classList.add("rtd-active");

      this.updateOverlay();
      this.showNotification("Dubbing activated!", "success");

      // Notify background script
      chrome.runtime.sendMessage({
        action: "update_badge",
        status: "active",
      });
    } catch (error) {
      console.error("RTD: Failed to start dubbing:", error);
      this.showNotification(`Failed to start: ${error.message}`, "error");
      throw error;
    }
  }

  async stopDubbing() {
    try {
      this.isActive = false;
      document.body.classList.remove("rtd-active");

      // Close WebSocket connection
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }

      // Stop audio capture
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((track) => track.stop());
        this.mediaStream = null;
      }

      // Close audio context
      if (this.audioContext) {
        await this.audioContext.close();
        this.audioContext = null;
      }

      this.updateOverlay();
      this.showNotification("Dubbing deactivated", "warning");

      // Notify background script
      chrome.runtime.sendMessage({
        action: "update_badge",
        status: "ready",
      });
    } catch (error) {
      console.error("RTD: Failed to stop dubbing:", error);
    }
  }

  updateSettings(settings) {
    this.settings = { ...this.settings, ...settings };

    // If WebSocket is connected, send updated settings
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(
        JSON.stringify({
          type: "settings_update",
          settings: this.settings,
        })
      );
    }
  }

  async setupAudioCapture() {
    try {
      // Create audio context
      this.audioContext = new (window.AudioContext ||
        window.webkitAudioContext)();

      // Capture audio from video element
      const stream = this.audioContext.createMediaElementSource(
        this.videoElement
      );

      // Create audio processor
      await this.audioContext.audioWorklet.addModule(
        chrome.runtime.getURL("audio-processor.js")
      );

      this.audioProcessor = new AudioWorkletNode(
        this.audioContext,
        "audio-processor"
      );

      // Setup audio processing chain
      stream.connect(this.audioProcessor);
      this.audioProcessor.connect(this.audioContext.destination);

      // Listen for processed audio data
      this.audioProcessor.port.onmessage = (event) => {
        this.handleAudioData(event.data);
      };

      // Create audio visualization
      this.createAudioVisualization();
    } catch (error) {
      console.error("RTD: Audio capture setup failed:", error);
      throw new Error(
        "Failed to setup audio capture. Please check browser permissions."
      );
    }
  }

  async connectToServer() {
    return new Promise((resolve, reject) => {
      try {
        // Generate connection and session IDs
        const connectionId = "conn_" + Math.random().toString(36).substr(2, 9);
        const sessionId = "session_" + Math.random().toString(36).substr(2, 9);

        const wsUrl =
          this.settings.serverUrl.replace("http", "ws") +
          `/ws/${connectionId}/${sessionId}`;
        this.websocket = new WebSocket(wsUrl);

        const timeout = setTimeout(() => {
          this.websocket.close();
          reject(new Error("Connection timeout"));
        }, 5000);

        this.websocket.onopen = () => {
          clearTimeout(timeout);
          console.log("RTD: Connected to server");

          // Send initial configuration
          this.websocket.send(
            JSON.stringify({
              type: "config",
              settings: this.settings,
              platform: this.platform,
            })
          );

          this.stats.connectionStatus = "connected";
          resolve();
        };

        this.websocket.onmessage = (event) => {
          this.handleServerMessage(event.data);
        };

        this.websocket.onclose = () => {
          console.log("RTD: Disconnected from server");
          this.stats.connectionStatus = "disconnected";
          this.updateOverlay();
        };

        this.websocket.onerror = (error) => {
          clearTimeout(timeout);
          console.error("RTD: WebSocket error:", error);
          reject(new Error("Failed to connect to server"));
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  handleAudioData(audioData) {
    if (
      !this.isActive ||
      !this.websocket ||
      this.websocket.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    // Send audio chunk to server for processing
    this.websocket.send(
      JSON.stringify({
        type: "audio_chunk",
        data: Array.from(audioData.audioBuffer),
        sampleRate: audioData.sampleRate,
        timestamp: Date.now(),
      })
    );

    // Update audio visualization
    this.updateAudioVisualization(audioData.level);
  }

  handleServerMessage(data) {
    try {
      const message = JSON.parse(data);

      switch (message.type) {
        case "dubbed_audio":
          this.playDubbedAudio(message.audioData, message.timestamp);
          this.stats.processedChunks++;
          break;

        case "translation":
          console.log("RTD: Translation:", message.text);
          break;

        case "error":
          console.error("RTD: Server error:", message.error);
          this.showNotification(`Server error: ${message.error}`, "error");
          break;

        case "stats":
          this.stats = { ...this.stats, ...message.stats };
          this.updateOverlay();
          break;
      }
    } catch (error) {
      console.error("RTD: Failed to parse server message:", error);
    }
  }

  async playDubbedAudio(audioData, timestamp) {
    try {
      // Convert base64 audio data to audio buffer
      const audioBuffer = await this.audioContext.decodeAudioData(
        this.base64ToArrayBuffer(audioData)
      );

      // Create audio source
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;

      // Calculate playback timing
      const latency = Date.now() - timestamp;
      const playbackTime = this.audioContext.currentTime + latency / 1000;

      // Temporarily mute original audio and play dubbed version
      this.videoElement.volume = 0.1; // Keep very low but not muted
      source.connect(this.audioContext.destination);
      source.start(playbackTime);

      // Restore original volume after dubbed audio ends
      setTimeout(() => {
        this.videoElement.volume = 1;
      }, audioBuffer.duration * 1000 + 100);
    } catch (error) {
      console.error("RTD: Failed to play dubbed audio:", error);
    }
  }

  findVideoElement() {
    // Platform-specific video element selectors
    const selectors = {
      netflix: "video",
      youtube: "video.video-stream",
      crunchyroll: "video",
      hulu: "video",
      disneyplus: "video",
      amazon: "video",
      funimation: "video",
      hbo: "video",
      twitch: "video",
      unknown: "video",
    };

    const selector = selectors[this.platform] || "video";
    this.videoElement = document.querySelector(selector);

    if (this.videoElement) {
      console.log("RTD: Found video element:", this.videoElement);
    }

    return this.videoElement;
  }

  waitForVideo() {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "childList") {
          const video = this.findVideoElement();
          if (video) {
            console.log("RTD: Video element found after waiting");
            observer.disconnect();
            break;
          }
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Stop observing after 30 seconds
    setTimeout(() => {
      observer.disconnect();
    }, 30000);
  }

  createOverlay() {
    // Remove existing overlay
    const existing = document.querySelector(".rtd-overlay");
    if (existing) {
      existing.remove();
    }

    this.overlayElement = document.createElement("div");
    this.overlayElement.className = "rtd-overlay";
    this.overlayElement.innerHTML = `
            <div class="rtd-header">
                <div class="rtd-title">🎬 AI Dubbing</div>
                <button class="rtd-close" onclick="this.parentElement.parentElement.classList.add('hidden')">×</button>
            </div>
            <div class="rtd-status">
                <div class="rtd-status-dot"></div>
                <span class="rtd-status-text">Inactive</span>
            </div>
            <div class="rtd-info">
                Platform: <span class="rtd-platform">${this.platform}</span><br>
                Language: <span class="rtd-language">${this.settings.targetLanguage}</span>
            </div>
            <div class="rtd-stats">
                <span>Chunks: <span class="rtd-chunks">0</span></span>
                <span>Latency: <span class="rtd-latency">--</span>ms</span>
            </div>
        `;

    document.body.appendChild(this.overlayElement);
    this.updateOverlay();
  }

  updateOverlay() {
    if (!this.overlayElement) return;

    const statusDot = this.overlayElement.querySelector(".rtd-status-dot");
    const statusText = this.overlayElement.querySelector(".rtd-status-text");
    const chunks = this.overlayElement.querySelector(".rtd-chunks");
    const latency = this.overlayElement.querySelector(".rtd-latency");
    const language = this.overlayElement.querySelector(".rtd-language");

    if (this.isActive) {
      statusDot.className = "rtd-status-dot active";
      statusText.textContent = "Active";
    } else {
      statusDot.className = "rtd-status-dot";
      statusText.textContent = "Inactive";
    }

    chunks.textContent = this.stats.processedChunks;
    latency.textContent = this.stats.averageLatency || "--";
    language.textContent = this.settings.targetLanguage;
  }

  createAudioVisualization() {
    this.audioVisualization = document.createElement("div");
    this.audioVisualization.className = "rtd-audio-viz";

    // Create visualization bars
    for (let i = 0; i < 10; i++) {
      const bar = document.createElement("div");
      bar.className = "rtd-bar";
      this.audioVisualization.appendChild(bar);
    }

    document.body.appendChild(this.audioVisualization);
  }

  updateAudioVisualization(level) {
    if (!this.audioVisualization || !this.isActive) return;

    const bars = this.audioVisualization.querySelectorAll(".rtd-bar");
    const normalizedLevel = Math.min(level * 10, 10);

    bars.forEach((bar, index) => {
      if (index < normalizedLevel) {
        bar.classList.add("active");
        bar.style.height = `${4 + normalizedLevel * 2}px`;
      } else {
        bar.classList.remove("active");
        bar.style.height = "4px";
      }
    });
  }

  showNotification(message, type = "error") {
    const notification = document.createElement("div");
    notification.className = `rtd-notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }
}

// Initialize content script when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    new RTDContentScript();
  });
} else {
  new RTDContentScript();
}
