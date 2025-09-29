// Pose Detector JavaScript - Updated to work with dashboard.js

// Global Variables
let currentMode = 'image';
let cameraStream = null;
let websocketConnection = null;
let isAnalyzing = false;

// DOM Elements
const imageSection = document.getElementById('imageSection');
const realtimeSection = document.getElementById('realtimeSection');
const previewSection = document.getElementById('previewSection');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const cameraFeed = document.getElementById('cameraFeed');
const analysisCanvas = document.getElementById('analysisCanvas');

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    // REMOVED: loadUserInfo() - dashboard.js handles this
});

function initializePage() {
    // Set default mode
    switchMode('image');
    
    // Add event listeners for drag and drop
    const uploadBox = document.getElementById('uploadBox');
    if (uploadBox) {
        uploadBox.addEventListener('dragover', handleDragOver);
        uploadBox.addEventListener('dragleave', handleDragLeave);
        uploadBox.addEventListener('drop', handleDrop);
    }
}

// REMOVED: loadUserInfo function - dashboard.js handles this

// Mode Switching
function switchMode(mode) {
    currentMode = mode;
    
    // Update button states
    const imageBtn = document.getElementById('imageMode');
    const realtimeBtn = document.getElementById('realtimeMode');
    
    imageBtn.classList.toggle('active', mode === 'image');
    realtimeBtn.classList.toggle('active', mode === 'realtime');
    
    // Show/hide sections
    imageSection.style.display = mode === 'image' ? 'block' : 'none';
    realtimeSection.style.display = mode === 'realtime' ? 'block' : 'none';
    
    // Clean up previous results
    hideResults();
    
    // Stop camera if switching away from realtime
    if (mode !== 'realtime' && cameraStream) {
        stopCamera();
    }
}

// Image Upload Functionality
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file.');
        return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showError('Image size should be less than 10MB.');
        return;
    }
    
    // Preview image
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImg = document.getElementById('previewImage');
        previewImg.src = e.target.result;
        previewSection.style.display = 'block';
        
        // Store file for analysis
        previewImg.dataset.file = file.name;
        window.selectedFile = file;
    };
    reader.readAsDataURL(file);
}

// Image Analysis
async function analyzeImage() {
    if (!window.selectedFile) {
        showError('Please select an image first.');
        return;
    }
    
    if (isAnalyzing) {
        return;
    }
    
    isAnalyzing = true;
    showLoading('Analyzing your pose...');
    
    const formData = new FormData();
    formData.append('file', window.selectedFile);
    
    try {
        const response = await fetch('/api/pose/detect-from-image', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            displayResults(result.data);
        } else {
            showError(result.error || 'Failed to analyze pose. Please try again.');
        }
    } catch (error) {
        hideLoading();
        showError('Network error. Please check your connection and try again.');
        console.error('Analysis error:', error);
    } finally {
        isAnalyzing = false;
    }
}

// Real-time Camera Functionality
async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 }, 
                height: { ideal: 480 } 
            } 
        });
        
        cameraFeed.srcObject = cameraStream;
        
        // Update UI
        document.getElementById('startCamera').style.display = 'none';
        document.getElementById('stopCamera').style.display = 'inline-block';
        document.getElementById('captureBtn').style.display = 'inline-block';
        
        // Initialize WebSocket connection
        initializeWebSocket();
        
    } catch (error) {
        console.error('Camera access error:', error);
        showError('Unable to access camera. Please ensure camera permissions are granted.');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    if (websocketConnection) {
        websocketConnection.close();
        websocketConnection = null;
    }
    
    // Update UI
    document.getElementById('startCamera').style.display = 'inline-block';
    document.getElementById('stopCamera').style.display = 'none';
    document.getElementById('captureBtn').style.display = 'none';
    
    // Clear camera feed
    cameraFeed.srcObject = null;
}

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/pose/realtime-detection`;
    
    websocketConnection = new WebSocket(wsUrl);
    
    websocketConnection.onopen = function() {
        console.log('WebSocket connected for real-time detection');
    };
    
    websocketConnection.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.success) {
            displayResults(data.data);
        } else {
            showError(data.error || 'Real-time detection error');
        }
    };
    
    websocketConnection.onerror = function(error) {
        console.error('WebSocket error:', error);
        showError('Real-time connection error. Please try again.');
    };
    
    websocketConnection.onclose = function() {
        console.log('WebSocket connection closed');
    };
}

async function captureFrame() {
    if (!cameraStream || isAnalyzing) {
        return;
    }
    
    isAnalyzing = true;
    showLoading('Analyzing current frame...');
    
    try {
        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        canvas.width = cameraFeed.videoWidth;
        canvas.height = cameraFeed.videoHeight;
        
        context.drawImage(cameraFeed, 0, 0);
        
        // Convert to blob and send for analysis
        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('file', blob, 'camera_capture.jpg');
            
            try {
                const response = await fetch('/api/pose/detect-from-image', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                hideLoading();
                
                if (result.success) {
                    displayResults(result.data);
                } else {
                    showError(result.error || 'Failed to analyze captured frame.');
                }
            } catch (error) {
                hideLoading();
                showError('Failed to analyze captured frame. Please try again.');
                console.error('Capture analysis error:', error);
            } finally {
                isAnalyzing = false;
            }
        }, 'image/jpeg', 0.8);
        
    } catch (error) {
        hideLoading();
        isAnalyzing = false;
        showError('Failed to capture frame. Please try again.');
        console.error('Frame capture error:', error);
    }
}

// Results Display
function displayResults(data) {
    if (!data.pose_detected) {
        showError(data.message || 'No pose detected in the image.');
        return;
    }
    
    // Update main result
    document.getElementById('detectedPose').textContent = data.best_asana.replace(/_/g, ' ').toUpperCase();
    document.getElementById('similarityScore').textContent = data.similarity;
    document.getElementById('feedbackText').textContent = data.feedback;
    
    // Update confidence badge
    const confidenceBadge = document.getElementById('confidenceBadge');
    confidenceBadge.textContent = data.confidence_level;
    confidenceBadge.className = `confidence-badge ${data.confidence_level.toLowerCase()}`;
    
    // Display suggestions
    if (data.suggestions && data.suggestions.length > 0) {
        const suggestionsList = document.getElementById('suggestionsList');
        suggestionsList.innerHTML = '';
        data.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
        document.getElementById('suggestionsCard').style.display = 'block';
    } else {
        document.getElementById('suggestionsCard').style.display = 'none';
    }
    
    // Display top matches
    if (data.all_matches && data.all_matches.length > 0) {
        const matchesList = document.getElementById('matchesList');
        matchesList.innerHTML = '';
        data.all_matches.slice(0, 5).forEach(match => {
            const matchItem = document.createElement('div');
            matchItem.className = 'match-item';
            matchItem.innerHTML = `
                <span class="match-name">${match.asana.replace(/_/g, ' ').toUpperCase()}</span>
                <span class="match-score">${match.similarity.toFixed(1)}%</span>
            `;
            matchesList.appendChild(matchItem);
        });
        document.getElementById('topMatches').style.display = 'block';
    } else {
        document.getElementById('topMatches').style.display = 'none';
    }
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Utility Functions
function showLoading(message = 'Processing...') {
    loadingOverlay.style.display = 'flex';
    const loadingText = loadingOverlay.querySelector('p');
    if (loadingText) {
        loadingText.textContent = message;
    }
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showError(message) {
    // Use the showMessage function from common.js if available
    if (typeof showMessage === 'function') {
        showMessage(message, 'error');
        return;
    }
    
    // Fallback error display
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.innerHTML = `
        <div class="error-content">
            <span class="error-icon">⚠️</span>
            <span class="error-message">${message}</span>
            <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fee2e2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        max-width: 400px;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
}

function hideResults() {
    resultsSection.style.display = 'none';
    previewSection.style.display = 'none';
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (cameraStream) {
        stopCamera();
    }
});

// Export functions for global access
window.switchMode = switchMode;
window.handleFileSelect = handleFileSelect;
window.analyzeImage = analyzeImage;
window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.captureFrame = captureFrame;
window.handleDrop = handleDrop;
window.handleDragOver = handleDragOver;
