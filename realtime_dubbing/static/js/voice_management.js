// Voice Management Component
const VoiceManagementUI = {
  init() {
    this.container = document.getElementById('voice-management-container');
    if (!this.container) return;
    
    this.renderUI();
    this.attachEventListeners();
    this.loadActorProfiles();
    this.loadAvailableVoices();
  },
  
  renderUI() {
    this.container.innerHTML = `
      <div class="p-6">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Voice Management</h2>
        
        <div class="border-b border-gray-200 mb-6">
          <nav class="flex space-x-8">
            <button class="tab-button tab-button-active" data-tab="actors">Actors</button>
            <button class="tab-button" data-tab="voices">Voice Library</button>
            <button class="tab-button" data-tab="speakers">Speaker Profiles</button>
          </nav>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" id="actors-tab">
          <div>
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Actor Profiles</h3>
              <button id="create-actor-btn" class="btn-primary">Create Actor</button>
            </div>
            
            <div class="card max-h-96 overflow-y-auto" id="actors-list">
              <p class="text-gray-500">Loading actor profiles...</p>
            </div>
          </div>
          
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Actor Details</h3>
            <div class="card" id="actor-detail">
              <p class="text-gray-500">Select an actor to view details</p>
            </div>
          </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 hidden" id="voices-tab">
          <div>
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-900">Voice Library</h3>
              <button id="create-voice-btn" class="btn-primary">Create Voice Clone</button>
            </div>
            
            <div class="card max-h-96 overflow-y-auto" id="voices-list">
              <p class="text-gray-500">Loading voice library...</p>
            </div>
          </div>
          
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Voice Details</h3>
            <div class="card" id="voice-detail">
              <p class="text-gray-500">Select a voice to view details</p>
            </div>
          </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 hidden" id="speakers-tab">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Speaker Profiles</h3>
            <div class="card max-h-96 overflow-y-auto" id="speakers-list">
              <p class="text-gray-500">Loading speaker profiles...</p>
            </div>
          </div>
          
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Speaker Details</h3>
            <div class="card" id="speaker-detail">
              <p class="text-gray-500">Select a speaker to view details</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Create Actor Modal -->
      <div class="modal-overlay hidden" id="create-actor-modal">
        <div class="modal-content">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-semibold text-gray-900">Create New Actor</h3>
            <button class="close-btn text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
          </div>
          <form id="create-actor-form">
            <div class="mb-4">
              <label for="actor-name" class="form-label">Actor Name:</label>
              <input type="text" id="actor-name" class="form-input" required>
            </div>
            <div class="mb-4">
              <label class="form-label">Associate Speakers:</label>
              <div id="speaker-selection-list" class="border border-gray-200 rounded-md p-3 max-h-40 overflow-y-auto">
                <p class="text-gray-500">Loading speakers...</p>
              </div>
            </div>
            <div class="flex justify-end">
              <button type="submit" class="btn-primary">Create Actor</button>
            </div>
          </form>
        </div>
      </div>
      
      <!-- Create Voice Clone Modal -->
      <div class="modal-overlay hidden" id="create-voice-modal">
        <div class="modal-content">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-semibold text-gray-900">Create Voice Clone</h3>
            <button class="close-btn text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
          </div>
          <form id="create-voice-form" enctype="multipart/form-data">
            <div class="mb-4">
              <label for="voice-name" class="form-label">Voice Name:</label>
              <input type="text" id="voice-name" class="form-input" required>
            </div>
            <div class="mb-4">
              <label for="voice-description" class="form-label">Description:</label>
              <input type="text" id="voice-description" class="form-input">
            </div>
            <div class="mb-4">
              <label for="speaker-select" class="form-label">Associated Speaker:</label>
              <select id="speaker-select" class="form-input" required>
                <option value="">Select a speaker...</option>
              </select>
            </div>
            <div class="mb-4">
              <label for="actor-select" class="form-label">Associated Actor (Optional):</label>
              <select id="actor-select" class="form-input">
                <option value="">Select an actor...</option>
              </select>
            </div>
            <div class="mb-4">
              <label for="voice-samples" class="form-label">Audio Samples:</label>
              <input type="file" id="voice-samples" multiple accept="audio/*" class="form-input" required>
              <p class="text-sm text-gray-500 mt-2">For best results, provide at least 30 seconds of high-quality audio samples.</p>
            </div>
            <div class="mb-4">
              <div class="bg-gray-200 rounded-full h-2 overflow-hidden" id="clone-progress">
                <div class="bg-green-500 h-full w-0 transition-all duration-300"></div>
              </div>
              <p id="clone-status" class="text-sm text-gray-600 mt-2"></p>
            </div>
            <div class="flex justify-end">
              <button type="submit" class="btn-primary">Create Voice Clone</button>
            </div>
          </form>
        </div>
      </div>
    `;
  },
  
  attachEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tabId = e.target.dataset.tab;
        this.switchTab(tabId);
      });
    });
    
    // Create actor button
    document.getElementById('create-actor-btn').addEventListener('click', () => {
      this.openCreateActorModal();
    });
    
    // Create voice button
    document.getElementById('create-voice-btn').addEventListener('click', () => {
      this.openCreateVoiceModal();
    });
    
    // Modal close buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.target.closest('.modal-overlay').classList.add('hidden');
      });
    });
    
    // Create actor form submission
    document.getElementById('create-actor-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitCreateActorForm();
    });
    
    // Create voice form submission
    document.getElementById('create-voice-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitCreateVoiceForm();
    });
  },
  
  switchTab(tabId) {
    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(btn => {
      if (btn.dataset.tab === tabId) {
        btn.classList.add('tab-button-active');
      } else {
        btn.classList.remove('tab-button-active');
      }
    });
    
    // Update active tab content - hide all tabs
    document.querySelectorAll('[id$="-tab"]').forEach(content => {
      content.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabId}-tab`);
    if (selectedTab) {
      selectedTab.classList.remove('hidden');
    }
  },
  
  async loadActorProfiles() {
    try {
      const response = await fetch('/api/voice-management/actors');
      const data = await response.json();
      
      if (data.success && data.actors) {
        this.renderActorsList(data.actors);
      } else {
        document.getElementById('actors-list').innerHTML = 
          '<p class="text-red-600">Failed to load actor profiles.</p>';
      }
    } catch (error) {
      console.error('Error loading actor profiles:', error);
      document.getElementById('actors-list').innerHTML = 
        '<p class="text-red-600">Error loading actor profiles.</p>';
    }
  },
  
  renderActorsList(actors) {
    const actorsList = document.getElementById('actors-list');
    
    if (Object.keys(actors).length === 0) {
      actorsList.innerHTML = '<p>No actor profiles found. Create one to get started.</p>';
      return;
    }
    
    const actorsHtml = Object.values(actors).map(actor => `
      <div class="p-4 mb-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors" data-actor-id="${actor.actor_id}">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">${actor.name}</h3>
        <p class="text-sm text-gray-600">Voices: ${actor.voice_ids.length}</p>
        <p class="text-sm text-gray-600">Speakers: ${actor.speaker_ids.length}</p>
      </div>
    `).join('');
    
    actorsList.innerHTML = actorsHtml;
    
    // Add click event to actor items
    document.querySelectorAll('[data-actor-id]').forEach(item => {
      item.addEventListener('click', (e) => {
        const actorId = e.currentTarget.dataset.actorId;
        this.showActorDetail(actors[actorId]);
      });
    });
  },
  
  showActorDetail(actor) {
    const actorDetail = document.getElementById('actor-detail');
    
    actorDetail.innerHTML = `
      <h3 class="text-xl font-bold text-gray-900 mb-4">${actor.name}</h3>
      <div class="space-y-2 mb-6">
        <p class="text-sm"><span class="font-medium text-gray-700">ID:</span> ${actor.actor_id}</p>
        <p class="text-sm"><span class="font-medium text-gray-700">Created:</span> ${new Date(actor.created_at * 1000).toLocaleString()}</p>
        <p class="text-sm"><span class="font-medium text-gray-700">Updated:</span> ${new Date(actor.updated_at * 1000).toLocaleString()}</p>
      </div>
      
      <h4 class="text-lg font-semibold text-gray-900 mb-3">Voice Clones</h4>
      <div class="mb-6" id="actor-voices">
        ${actor.voice_ids.length > 0 ? 
          actor.voice_ids.map(id => `<div class="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-2 mb-2" data-voice-id="${id}">${id}</div>`).join('') :
          '<p class="text-gray-500">No voice clones associated with this actor.</p>'
        }
      </div>
      
      <h4 class="text-lg font-semibold text-gray-900 mb-3">Associated Speakers</h4>
      <div class="mb-6" id="actor-speakers">
        ${actor.speaker_ids.length > 0 ? 
          actor.speaker_ids.map(id => `<div class="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm mr-2 mb-2" data-speaker-id="${id}">${id}</div>`).join('') :
          '<p class="text-gray-500">No speakers associated with this actor.</p>'
        }
      </div>
      
      <h4 class="text-lg font-semibold text-gray-900 mb-3">Content Appearances</h4>
      <div>
        ${actor.metadata && actor.metadata.content_appearances && actor.metadata.content_appearances.length > 0 ? 
          actor.metadata.content_appearances.map(id => `<div class="inline-block bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm mr-2 mb-2">${id}</div>`).join('') :
          '<p class="text-gray-500">No content appearances tracked.</p>'
        }
      </div>
    `;
    
    // Highlight the selected actor
    document.querySelectorAll('[data-actor-id]').forEach(item => {
      if (item.dataset.actorId === actor.actor_id) {
        item.classList.add('bg-blue-50', 'border-blue-500');
        item.classList.remove('hover:bg-gray-50');
      } else {
        item.classList.remove('bg-blue-50', 'border-blue-500');
        item.classList.add('hover:bg-gray-50');
      }
    });
  },
  
  async loadAvailableVoices() {
    try {
      const response = await fetch('/api/voice-management/voices');
      const data = await response.json();
      
      if (data.success && data.voices) {
        this.renderVoicesList(data.voices);
      } else {
        document.getElementById('voices-list').innerHTML = 
          '<p class="error">Failed to load voice library.</p>';
      }
    } catch (error) {
      console.error('Error loading voice library:', error);
      document.getElementById('voices-list').innerHTML = 
        '<p class="error">Error loading voice library.</p>';
    }
  },
  
  renderVoicesList(voices) {
    const voicesList = document.getElementById('voices-list');
    
    if (Object.keys(voices).length === 0) {
      voicesList.innerHTML = '<p>No voices found in the library.</p>';
      return;
    }
    
    // Group voices by category
    const categories = {};
    Object.entries(voices).forEach(([id, voice]) => {
      const category = voice.category || voice.source || 'unknown';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push({id, ...voice});
    });
    
    let voicesHtml = '';
    
    Object.entries(categories).forEach(([category, categoryVoices]) => {
      voicesHtml += `<h3 class="category-title">${category}</h3>`;
      voicesHtml += '<div class="category-voices">';
      
      voicesHtml += categoryVoices.map(voice => `
        <div class="voice-item" data-voice-id="${voice.id}">
          <h4>${voice.name}</h4>
          <p>${voice.is_cloned ? 'Cloned' : 'Standard'} Voice</p>
          ${voice.speaker_id ? `<p>Speaker: ${voice.speaker_id}</p>` : ''}
          ${voice.quality ? `<p>Quality: ${Math.round(voice.quality * 100)}%</p>` : ''}
        </div>
      `).join('');
      
      voicesHtml += '</div>';
    });
    
    voicesList.innerHTML = voicesHtml;
    
    // Add click event to voice items
    document.querySelectorAll('.voice-item').forEach(item => {
      item.addEventListener('click', async (e) => {
        const voiceId = e.currentTarget.dataset.voiceId;
        await this.showVoiceDetail(voiceId);
      });
    });
  },
  
  async showVoiceDetail(voiceId) {
    const voiceDetail = document.getElementById('voice-detail');
    voiceDetail.innerHTML = '<p>Loading voice details...</p>';
    
    try {
      const response = await fetch(`/api/voice-management/voices/${voiceId}`);
      const data = await response.json();
      
      if (data.success && data.voice) {
        const voice = data.voice;
        
        voiceDetail.innerHTML = `
          <h3>${voice.name}</h3>
          <p><strong>ID:</strong> ${voice.voice_id}</p>
          <p><strong>Speaker ID:</strong> ${voice.speaker_id || 'N/A'}</p>
          <p><strong>Created:</strong> ${new Date(voice.creation_time * 1000).toLocaleString()}</p>
          
          <h4>Voice Settings</h4>
          <div class="voice-settings">
            <p><strong>Stability:</strong> ${(voice.voice_settings?.stability || 0).toFixed(2)}</p>
            <p><strong>Similarity Boost:</strong> ${(voice.voice_settings?.similarity_boost || 0).toFixed(2)}</p>
            <p><strong>Style:</strong> ${(voice.voice_settings?.style || 0).toFixed(2)}</p>
          </div>
          
          <h4>Quality Metrics</h4>
          <div class="quality-metrics">
            ${voice.metrics ? 
              Object.entries(voice.metrics).map(([key, value]) => 
                `<p><strong>${key.replace(/_/g, ' ')}:</strong> ${typeof value === 'number' ? value.toFixed(2) : value}</p>`
              ).join('') :
              '<p>No quality metrics available.</p>'
            }
          </div>
          
          <h4>Voice Preview</h4>
          <div class="voice-preview">
            <button class="preview-btn" data-voice-id="${voice.voice_id}">Generate Preview</button>
            <div id="preview-audio-container"></div>
          </div>
        `;
        
        // Add event listener for preview button
        document.querySelector('.preview-btn').addEventListener('click', (e) => {
          this.generateVoicePreview(e.target.dataset.voiceId);
        });
        
      } else {
        voiceDetail.innerHTML = '<p class="error">Failed to load voice details.</p>';
      }
    } catch (error) {
      console.error('Error loading voice details:', error);
      voiceDetail.innerHTML = '<p class="error">Error loading voice details.</p>';
    }
    
    // Highlight the selected voice
    document.querySelectorAll('.voice-item').forEach(item => {
      item.classList.toggle('selected', item.dataset.voiceId === voiceId);
    });
  },
  
  async generateVoicePreview(voiceId) {
    const previewContainer = document.getElementById('preview-audio-container');
    previewContainer.innerHTML = '<p>Generating preview...</p>';
    
    try {
      // This would call an API endpoint to generate a preview
      // For now, we'll just simulate it
      setTimeout(() => {
        previewContainer.innerHTML = `
          <audio controls>
            <source src="/api/speech-synthesis?voice_id=${voiceId}&text=This is a preview of my voice." type="audio/wav">
            Your browser does not support the audio element.
          </audio>
        `;
      }, 1500);
    } catch (error) {
      console.error('Error generating voice preview:', error);
      previewContainer.innerHTML = '<p class="error">Error generating preview.</p>';
    }
  },
  
  async loadSpeakerProfiles() {
    // This would call an API endpoint to get speaker profiles
    // For now, we'll just show a placeholder
    document.getElementById('speakers-list').innerHTML = 
      '<p>Speaker profile management coming soon.</p>';
  },
  
  openCreateActorModal() {
    const modal = document.getElementById('create-actor-modal');
    modal.classList.remove('hidden');
    
    // Load speaker list for selection
    this.loadSpeakersForSelection();
  },
  
  async loadSpeakersForSelection() {
    const speakerList = document.getElementById('speaker-selection-list');
    speakerList.innerHTML = '<p>Loading speakers...</p>';
    
    try {
      // This would call an API endpoint to get all speakers
      // For now, we'll just show a placeholder
      setTimeout(() => {
        speakerList.innerHTML = '<p>No speakers available for selection.</p>';
      }, 500);
    } catch (error) {
      console.error('Error loading speakers for selection:', error);
      speakerList.innerHTML = '<p class="error">Error loading speakers.</p>';
    }
  },
  
  async submitCreateActorForm() {
    const nameInput = document.getElementById('actor-name');
    const name = nameInput.value.trim();
    
    if (!name) {
      alert('Please enter an actor name.');
      return;
    }
    
    // Get selected speakers
    const selectedSpeakers = [];
    document.querySelectorAll('#speaker-selection-list input[type="checkbox"]:checked').forEach(checkbox => {
      selectedSpeakers.push(checkbox.value);
    });
    
    try {
      const response = await fetch('/api/voice-management/actors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          speaker_ids: selectedSpeakers
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Actor created successfully!');
        document.getElementById('create-actor-modal').classList.add('hidden');
        this.loadActorProfiles();  // Reload the actors list
      } else {
        alert(`Failed to create actor: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating actor:', error);
      alert('Error creating actor. Please try again.');
    }
  },
  
  openCreateVoiceModal() {
    const modal = document.getElementById('create-voice-modal');
    modal.classList.remove('hidden');
    
    // Reset form
    document.getElementById('create-voice-form').reset();
    
    // Reset progress bar
    const progressBar = document.querySelector('#clone-progress div');
    if (progressBar) {
      progressBar.style.width = '0%';
    }
    document.getElementById('clone-status').textContent = '';
    
    // Load speakers and actors for selection
    this.loadSpeakersForVoiceClone();
    this.loadActorsForVoiceClone();
  },
  
  async loadSpeakersForVoiceClone() {
    const speakerSelect = document.getElementById('speaker-select');
    
    // Clear existing options except the first one
    while (speakerSelect.options.length > 1) {
      speakerSelect.remove(1);
    }
    
    try {
      // This would call an API endpoint to get all speakers
      // For now, we'll add some placeholders
      const placeholderSpeakers = [
        { id: 'speaker_001', name: 'Speaker 1' },
        { id: 'speaker_002', name: 'Speaker 2' },
        { id: 'speaker_003', name: 'Speaker 3' }
      ];
      
      placeholderSpeakers.forEach(speaker => {
        const option = document.createElement('option');
        option.value = speaker.id;
        option.textContent = `${speaker.name} (${speaker.id})`;
        speakerSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Error loading speakers for voice clone:', error);
      const option = document.createElement('option');
      option.textContent = 'Error loading speakers';
      option.disabled = true;
      speakerSelect.appendChild(option);
    }
  },
  
  async loadActorsForVoiceClone() {
    const actorSelect = document.getElementById('actor-select');
    
    // Clear existing options except the first one
    while (actorSelect.options.length > 1) {
      actorSelect.remove(1);
    }
    
    try {
      const response = await fetch('/api/voice-management/actors');
      const data = await response.json();
      
      if (data.success && data.actors) {
        Object.values(data.actors).forEach(actor => {
          const option = document.createElement('option');
          option.value = actor.actor_id;
          option.textContent = actor.name;
          actorSelect.appendChild(option);
        });
      } else {
        const option = document.createElement('option');
        option.textContent = 'No actors available';
        option.disabled = true;
        actorSelect.appendChild(option);
      }
    } catch (error) {
      console.error('Error loading actors for voice clone:', error);
      const option = document.createElement('option');
      option.textContent = 'Error loading actors';
      option.disabled = true;
      actorSelect.appendChild(option);
    }
  },
  
  async submitCreateVoiceForm() {
    const form = document.getElementById('create-voice-form');
    const nameInput = document.getElementById('voice-name');
    const descriptionInput = document.getElementById('voice-description');
    const speakerSelect = document.getElementById('speaker-select');
    const actorSelect = document.getElementById('actor-select');
    const samplesInput = document.getElementById('voice-samples');
    
    // Validate inputs
    if (!nameInput.value.trim()) {
      alert('Please enter a voice name.');
      return;
    }
    
    if (speakerSelect.value === '') {
      alert('Please select a speaker.');
      return;
    }
    
    if (samplesInput.files.length === 0) {
      alert('Please select at least one audio sample.');
      return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('name', nameInput.value.trim());
    formData.append('speaker_id', speakerSelect.value);
    
    if (descriptionInput.value.trim()) {
      formData.append('description', descriptionInput.value.trim());
    }
    
    if (actorSelect.value) {
      formData.append('actor_id', actorSelect.value);
    }
    
    // Add audio files
    for (let i = 0; i < samplesInput.files.length; i++) {
      formData.append('audio_files', samplesInput.files[i]);
    }
    
    // Update UI
    const progressBar = document.querySelector('#clone-progress div');
    const statusText = document.getElementById('clone-status');
    progressBar.style.width = '0%';
    statusText.textContent = 'Starting voice cloning...';
    
    try {
      const response = await fetch('/api/voice-management/voice-clones', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show progress (this is simulated as the actual process happens in background)
        let progress = 0;
        const interval = setInterval(() => {
          progress += 5;
          progressBar.style.width = `${progress}%`;
          
          if (progress < 30) {
            statusText.textContent = 'Uploading and analyzing audio samples...';
          } else if (progress < 70) {
            statusText.textContent = 'Creating voice clone...';
          } else if (progress < 100) {
            statusText.textContent = 'Finalizing voice model...';
          } else {
            clearInterval(interval);
            statusText.textContent = 'Voice cloning completed successfully!';
            
            // Close modal after a delay
            setTimeout(() => {
              document.getElementById('create-voice-modal').classList.add('hidden');
              this.loadAvailableVoices();  // Reload the voices list
            }, 2000);
          }
        }, 300);
      } else {
        statusText.textContent = `Failed to start voice cloning: ${data.message || 'Unknown error'}`;
        progressBar.style.width = '0%';
      }
    } catch (error) {
      console.error('Error creating voice clone:', error);
      statusText.textContent = 'Error creating voice clone. Please try again.';
      progressBar.style.width = '0%';
    }
  }
};

// Initialize when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
  VoiceManagementUI.init();
});
