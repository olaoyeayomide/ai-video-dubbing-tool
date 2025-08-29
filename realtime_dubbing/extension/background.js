// Background service worker for RealTime AI Dubbing extension
class BackgroundService {
    constructor() {
        this.init();
    }
    
    init() {
        // Listen for extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            this.handleInstall(details);
        });
        
        // Listen for messages from content scripts and popup
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Keep message channel open for async responses
        });
        
        // Listen for tab updates to check for supported streaming platforms
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            this.handleTabUpdate(tabId, changeInfo, tab);
        });
    }
    
    handleInstall(details) {
        if (details.reason === 'install') {
            // Set default settings
            chrome.storage.sync.set({
                isActive: false,
                targetLanguage: 'en',
                serverUrl: 'ws://localhost:8000',
                voicePreservation: 'auto'
            });
            
            // Show welcome notification
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon-48.png',
                title: 'RealTime AI Dubbing Installed!',
                message: 'Click the extension icon to start dubbing your favorite content.'
            });
        }
    }
    
    async handleMessage(message, sender, sendResponse) {
        try {
            switch (message.action) {
                case 'check_server_connection':
                    const isConnected = await this.checkServerConnection(message.serverUrl);
                    sendResponse({ connected: isConnected });
                    break;
                    
                case 'log_error':
                    console.error('Content script error:', message.error);
                    // Could send to analytics service here
                    break;
                    
                case 'update_badge':
                    this.updateBadge(sender.tab.id, message.status);
                    break;
                    
                case 'get_tab_info':
                    const tab = await chrome.tabs.get(sender.tab.id);
                    sendResponse({
                        url: tab.url,
                        title: tab.title,
                        platform: this.detectPlatform(tab.url)
                    });
                    break;
                    
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ error: error.message });
        }
    }
    
    async checkServerConnection(serverUrl) {
        try {
            // Simple WebSocket connection test
            const ws = new WebSocket(serverUrl + '/ws/test');
            
            return new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    ws.close();
                    resolve(false);
                }, 3000);
                
                ws.onopen = () => {
                    clearTimeout(timeout);
                    ws.close();
                    resolve(true);
                };
                
                ws.onerror = () => {
                    clearTimeout(timeout);
                    resolve(false);
                };
            });
        } catch (error) {
            return false;
        }
    }
    
    handleTabUpdate(tabId, changeInfo, tab) {
        // Check if the tab is a supported streaming platform
        if (changeInfo.status === 'complete' && tab.url) {
            const platform = this.detectPlatform(tab.url);
            if (platform) {
                // Update badge to show supported platform
                this.updateBadge(tabId, 'ready');
            } else {
                this.updateBadge(tabId, 'unsupported');
            }
        }
    }
    
    detectPlatform(url) {
        const platforms = {
            'netflix.com': 'Netflix',
            'youtube.com': 'YouTube',
            'crunchyroll.com': 'Crunchyroll',
            'hulu.com': 'Hulu',
            'disneyplus.com': 'Disney+',
            'amazon.com': 'Prime Video',
            'funimation.com': 'Funimation',
            'hbo.com': 'HBO Max',
            'twitch.tv': 'Twitch'
        };
        
        for (const [domain, name] of Object.entries(platforms)) {
            if (url.includes(domain)) {
                return name;
            }
        }
        return null;
    }
    
    updateBadge(tabId, status) {
        const badgeConfig = {
            'ready': { text: '', color: '#4CAF50' },
            'active': { text: 'ON', color: '#4CAF50' },
            'error': { text: '!', color: '#f44336' },
            'unsupported': { text: '', color: '#9E9E9E' }
        };
        
        const config = badgeConfig[status] || badgeConfig['unsupported'];
        
        chrome.action.setBadgeText({ tabId, text: config.text });
        chrome.action.setBadgeBackgroundColor({ tabId, color: config.color });
    }
}

// Initialize background service
new BackgroundService();