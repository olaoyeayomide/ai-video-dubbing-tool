class PopupController {
    constructor() {
        this.isActive = false;
        this.settings = {
            targetLanguage: 'en',
            serverUrl: 'ws://localhost:8000',
            voicePreservation: 'auto'
        };
        this.init();
    }
    
    async init() {
        await this.loadSettings();
        this.setupEventListeners();
        this.updateUI();
        this.checkTabStatus();
    }
    
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get([
                'isActive',
                'targetLanguage',
                'serverUrl',
                'voicePreservation'
            ]);
            
            this.isActive = result.isActive || false;
            this.settings.targetLanguage = result.targetLanguage || 'en';
            this.settings.serverUrl = result.serverUrl || 'ws://localhost:8000';
            this.settings.voicePreservation = result.voicePreservation || 'auto';
            
            // Update form values
            document.getElementById('targetLanguage').value = this.settings.targetLanguage;
            document.getElementById('serverUrl').value = this.settings.serverUrl;
            document.getElementById('voicePreservation').value = this.settings.voicePreservation;
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    async saveSettings() {
        try {
            await chrome.storage.sync.set({
                isActive: this.isActive,
                targetLanguage: this.settings.targetLanguage,
                serverUrl: this.settings.serverUrl,
                voicePreservation: this.settings.voicePreservation
            });
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }
    
    setupEventListeners() {
        // Toggle button
        document.getElementById('toggleButton').addEventListener('click', () => {
            this.toggleDubbing();
        });
        
        // Settings
        document.getElementById('targetLanguage').addEventListener('change', (e) => {
            this.settings.targetLanguage = e.target.value;
            this.saveSettings();
            this.notifyContentScript();
        });
        
        document.getElementById('serverUrl').addEventListener('change', (e) => {
            this.settings.serverUrl = e.target.value;
            this.saveSettings();
            this.notifyContentScript();
        });
        
        document.getElementById('voicePreservation').addEventListener('change', (e) => {
            this.settings.voicePreservation = e.target.value;
            this.saveSettings();
            this.notifyContentScript();
        });
    }
    
    async toggleDubbing() {
        try {
            // Get active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (!this.isValidStreamingPlatform(tab.url)) {
                this.showError('This extension only works on supported streaming platforms.');
                return;
            }
            
            this.isActive = !this.isActive;
            
            // Send message to content script
            await chrome.tabs.sendMessage(tab.id, {
                action: this.isActive ? 'start_dubbing' : 'stop_dubbing',
                settings: this.settings
            });
            
            await this.saveSettings();
            this.updateUI();
        } catch (error) {
            console.error('Failed to toggle dubbing:', error);
            this.showError('Failed to communicate with the page. Please refresh and try again.');
        }
    }
    
    async notifyContentScript() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            await chrome.tabs.sendMessage(tab.id, {
                action: 'update_settings',
                settings: this.settings
            });
        } catch (error) {
            console.error('Failed to notify content script:', error);
        }
    }
    
    isValidStreamingPlatform(url) {
        const supportedPlatforms = [
            'netflix.com',
            'youtube.com',
            'crunchyroll.com',
            'hulu.com',
            'disneyplus.com',
            'amazon.com',
            'funimation.com',
            'hbo.com',
            'twitch.tv'
        ];
        
        return supportedPlatforms.some(platform => url.includes(platform));
    }
    
    updateUI() {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const toggleButton = document.getElementById('toggleButton');
        
        if (this.isActive) {
            statusIndicator.classList.remove('inactive');
            statusIndicator.classList.add('active');
            statusText.textContent = 'Active';
            toggleButton.textContent = 'Disable Dubbing';
            toggleButton.classList.add('active');
        } else {
            statusIndicator.classList.remove('active');
            statusIndicator.classList.add('inactive');
            statusText.textContent = 'Inactive';
            toggleButton.textContent = 'Enable Dubbing';
            toggleButton.classList.remove('active');
        }
    }
    
    async checkTabStatus() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            const response = await chrome.tabs.sendMessage(tab.id, { action: 'get_status' });
            
            if (response && response.stats) {
                document.getElementById('stats').textContent = 
                    `${response.stats.processedChunks} chunks processed`;
            }
        } catch (error) {
            // Content script might not be loaded yet
            document.getElementById('stats').textContent = 'Page not ready';
        }
    }
    
    showError(message) {
        // Simple error display - could be enhanced with better UI
        alert(message);
    }
}

// Initialize popup controller
new PopupController();