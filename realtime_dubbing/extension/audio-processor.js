// Audio Worklet Processor for Real-time Audio Processing
class AudioProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();
        
        this.bufferSize = 2048; // Process in small chunks for low latency
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
        this.sampleRate = 44100; // Default, will be updated
        
        // Audio analysis properties
        this.analyser = {
            fftSize: 256,
            frequencyData: new Float32Array(128)
        };
        
        // Processing state
        this.isProcessing = true;
        this.frameCount = 0;
        
        // Listen for messages from main thread
        this.port.onmessage = (event) => {
            this.handleMessage(event.data);
        };
        
        console.log('AudioProcessor: Initialized');
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'start':
                this.isProcessing = true;
                break;
            case 'stop':
                this.isProcessing = false;
                break;
            case 'set_buffer_size':
                this.updateBufferSize(data.size);
                break;
        }
    }
    
    updateBufferSize(newSize) {
        this.bufferSize = Math.max(1024, Math.min(8192, newSize));
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }
    
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        const output = outputs[0];
        
        if (!input || input.length === 0) {
            return true;
        }
        
        const inputChannel = input[0];
        const outputChannel = output[0];
        
        // Update sample rate from context
        if (this.sampleRate !== sampleRate) {
            this.sampleRate = sampleRate;
        }
        
        // Process audio in chunks
        for (let i = 0; i < inputChannel.length; i++) {
            // Copy input to output (pass-through)
            outputChannel[i] = inputChannel[i];
            
            // Buffer audio for processing
            if (this.isProcessing) {
                this.buffer[this.bufferIndex] = inputChannel[i];
                this.bufferIndex++;
                
                // When buffer is full, send to main thread for processing
                if (this.bufferIndex >= this.bufferSize) {
                    this.processBuffer();
                    this.bufferIndex = 0;
                }
            }
        }
        
        this.frameCount++;
        return true;
    }
    
    processBuffer() {
        // Calculate audio level for visualization
        const audioLevel = this.calculateAudioLevel(this.buffer);
        
        // Apply basic audio preprocessing
        const processedBuffer = this.preprocessAudio(this.buffer);
        
        // Send processed audio chunk to main thread
        this.port.postMessage({
            type: 'audio_chunk',
            audioBuffer: processedBuffer,
            sampleRate: this.sampleRate,
            level: audioLevel,
            timestamp: currentTime * 1000 // Convert to milliseconds
        });
    }
    
    calculateAudioLevel(buffer) {
        let sum = 0;
        for (let i = 0; i < buffer.length; i++) {
            sum += Math.abs(buffer[i]);
        }
        return sum / buffer.length;
    }
    
    preprocessAudio(inputBuffer) {
        const outputBuffer = new Float32Array(inputBuffer.length);
        
        // Apply basic noise reduction and normalization
        for (let i = 0; i < inputBuffer.length; i++) {
            let sample = inputBuffer[i];
            
            // Simple noise gate (remove very quiet samples)
            if (Math.abs(sample) < 0.001) {
                sample = 0;
            }
            
            // Gentle compression to normalize levels
            sample = this.compress(sample, 0.7, 0.5);
            
            outputBuffer[i] = sample;
        }
        
        return outputBuffer;
    }
    
    compress(sample, threshold, ratio) {
        const absSample = Math.abs(sample);
        
        if (absSample > threshold) {
            const excess = absSample - threshold;
            const compressedExcess = excess * ratio;
            const compressedSample = threshold + compressedExcess;
            return sample >= 0 ? compressedSample : -compressedSample;
        }
        
        return sample;
    }
    
    // Perform spectral analysis for voice detection
    analyzeSpectrum(buffer) {
        // Simple FFT approximation for voice detection
        const fftData = this.simpleFFT(buffer);
        
        // Detect voice characteristics
        const voiceDetected = this.detectVoice(fftData);
        
        return {
            voiceDetected,
            spectralData: fftData
        };
    }
    
    simpleFFT(buffer) {
        // Simplified FFT for voice detection
        // In a real implementation, you'd use a proper FFT library
        const fftSize = Math.min(buffer.length, 256);
        const fftData = new Float32Array(fftSize / 2);
        
        for (let k = 0; k < fftSize / 2; k++) {
            let real = 0;
            let imag = 0;
            
            for (let n = 0; n < fftSize; n++) {
                const angle = -2 * Math.PI * k * n / fftSize;
                real += buffer[n] * Math.cos(angle);
                imag += buffer[n] * Math.sin(angle);
            }
            
            fftData[k] = Math.sqrt(real * real + imag * imag);
        }
        
        return fftData;
    }
    
    detectVoice(fftData) {
        // Simple voice detection based on spectral characteristics
        // Voice typically has energy in 85-255 Hz (fundamental) and harmonics
        
        let lowFreqEnergy = 0;
        let midFreqEnergy = 0;
        let highFreqEnergy = 0;
        
        const binSize = this.sampleRate / (fftData.length * 2);
        
        for (let i = 0; i < fftData.length; i++) {
            const freq = i * binSize;
            
            if (freq < 300) {
                lowFreqEnergy += fftData[i];
            } else if (freq < 3000) {
                midFreqEnergy += fftData[i];
            } else {
                highFreqEnergy += fftData[i];
            }
        }
        
        // Voice typically has significant mid-frequency energy
        const totalEnergy = lowFreqEnergy + midFreqEnergy + highFreqEnergy;
        if (totalEnergy === 0) return false;
        
        const midFreqRatio = midFreqEnergy / totalEnergy;
        return midFreqRatio > 0.3 && totalEnergy > 0.01;
    }
}

// Register the processor
registerProcessor('audio-processor', AudioProcessor);

console.log('Audio Worklet Processor registered successfully');