// API Configuration - UPDATED for base module integration
const API_BASE = '/api';  // Use relative paths to work with your existing module

// Global State
window.gameState = {
    roomCode: null,
    playerName: null,
    playerId: null,
    hostId: null,
    isHost: false,
    players: [],
    gameMode: null
};

// Utility Functions - FIXED: Proper show/hide functions
function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('hidden');
        element.style.display = '';
    }
}

function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('hidden');
        element.style.display = 'none';
    }
}

function showError(message, elementId = 'errorMessage') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
    }
    
    showElement('errorState');
    console.error('Error:', message);
}

// FIXED: Added missing showMessage function
function showMessage(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Set message
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        backgroundColor: type === 'error' ? '#ef4444' : '#10b981',
        color: 'white',
        borderRadius: '8px',
        zIndex: '9999',
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
        fontSize: '14px',
        fontFamily: 'Arial, sans-serif',
        maxWidth: '350px',
        wordBreak: 'break-word',
        animation: 'slideInRight 0.3s ease'
    });
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

function showSuccess(message) {
    showMessage(message, 'success');
}

// FIXED: Proper copyToClipboard function
function copyToClipboard(text) {
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        return new Promise((resolve, reject) => {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                const result = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (result) {
                    resolve();
                } else {
                    reject(new Error('Copy command failed'));
                }
            } catch (err) {
                document.body.removeChild(textArea);
                reject(err);
            }
        });
    }
}

// FIXED: API Helper with proper error handling
async function apiCall(endpoint, options = {}) {
    try {
        console.log(`🌐 API Call: ${endpoint}`, options); // Debug log
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'include',
            ...options
        });
        
        // Try to get response data
        let data;
        try {
            data = await response.json();
        } catch (parseError) {
            console.error('Failed to parse response JSON:', parseError);
            data = { detail: `Server error: ${response.status}` };
        }
        
        console.log(`📡 API Response for ${endpoint}:`, { status: response.status, data }); // Debug log
        
        if (!response.ok) {
            if (response.status === 401) {
                console.error('Authentication required - redirecting to login');
                window.location.href = '/signin';
                return;
            }
            
            // FIXED: Extract proper error message
            let errorMessage = 'Unknown server error';
            
            if (typeof data === 'string') {
                errorMessage = data;
            } else if (data && typeof data === 'object') {
                if (data.detail) {
                    if (Array.isArray(data.detail)) {
                        errorMessage = data.detail.map(err => err.msg || err).join(', ');
                    } else {
                        errorMessage = data.detail;
                    }
                } else if (data.message) {
                    errorMessage = data.message;
                } else if (data.error) {
                    errorMessage = data.error;
                } else {
                    errorMessage = JSON.stringify(data);
                }
            }
            
            throw new Error(errorMessage);
        }
        
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

async function apiCallFormData(endpoint, formData) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData,
            credentials: 'include'  // Include cookies for session auth
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle authentication errors
            if (response.status === 401) {
                console.error('Authentication required - redirecting to login');
                window.location.href = '/signin';
                return;
            }
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Game State Management
function updateGameState(updates) {
    Object.assign(window.gameState, updates);
    localStorage.setItem('yogaGameState', JSON.stringify(window.gameState));
    console.log('🔄 Game state updated:', window.gameState);
}

function loadGameState() {
    try {
        const saved = localStorage.getItem('yogaGameState');
        if (saved) {
            const state = JSON.parse(saved);
            Object.assign(window.gameState, state);
            console.log('📥 Game state loaded:', window.gameState);
        }
    } catch (error) {
        console.warn('Failed to load game state:', error);
    }
}

function clearGameState() {
    window.gameState = {
        roomCode: null,
        playerName: null,
        playerId: null,
        hostId: null,
        isHost: false,
        players: [],
        gameMode: null
    };
    localStorage.removeItem('yogaGameState');
    console.log('🗑️ Game state cleared');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadGameState();
    console.log('🎮 Multiplayer common.js initialized');
});

// Page redirect with state - UPDATED for base module integration
function redirectToGame() {
    updateGameState({});
    window.location.href = '/multiplayer/game';  // Updated path
}

function redirectToResults() {
    window.location.href = '/multiplayer/results';  // Updated path
}

function redirectToHost() {
    window.location.href = '/multiplayer/host';  // Updated path
}

function redirectToPlayer() {
    window.location.href = '/multiplayer/player';  // Updated path
}

function redirectToMultiplayerHome() {
    clearGameState();
    window.location.href = '/multiplayer';  // Updated path
}

function redirectToDashboard() {
    clearGameState();
    window.location.href = '/home';  // Navigate to base module dashboard
}

// Validation Helpers
function validateRoomCode(code) {
    return /^[0-9]{6}$/.test(code.trim());
}

function validatePlayerName(name) {
    const trimmed = name.trim();
    return trimmed.length >= 2 && trimmed.length <= 20;
}

// Room code display helpers
function formatRoomCode(code) {
    return code ? code.toString().padStart(6, '0') : '000000';
}

function copyRoomCode() {
    const roomCode = window.gameState.roomCode;
    if (roomCode) {
        copyToClipboard(roomCode).then(() => {
            showSuccess('Room code copied to clipboard!');
        }).catch(() => {
            showError('Failed to copy room code');
        });
    }
}

// Safe element helpers for better error handling
function safeShowElement(elementId) {
    try {
        showElement(elementId);
    } catch (error) {
        console.warn(`Could not show element ${elementId}:`, error);
    }
}

function safeHideElement(elementId) {
    try {
        hideElement(elementId);
    } catch (error) {
        console.warn(`Could not hide element ${elementId}:`, error);
    }
}

function safeUpdateElement(elementId, content) {
    try {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = content;
        }
    } catch (error) {
        console.warn(`Could not update element ${elementId}:`, error);
    }
}

// Network status monitoring
let isOnline = navigator.onLine;

window.addEventListener('online', () => {
    isOnline = true;
    showSuccess('Connection restored');
});

window.addEventListener('offline', () => {
    isOnline = false;
    showError('Connection lost. Please check your internet.');
});

function checkOnlineStatus() {
    return isOnline;
}

// Enhanced error handling with retry mechanism
async function apiCallWithRetry(endpoint, options = {}, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await apiCall(endpoint, options);
        } catch (error) {
            lastError = error;
            console.warn(`API call attempt ${attempt} failed:`, error);
            
            if (attempt < maxRetries && checkOnlineStatus()) {
                // Wait before retry (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
            }
        }
    }
    
    throw lastError;
}

// Room management helpers
function isValidGameState() {
    return window.gameState && 
           window.gameState.roomCode && 
           window.gameState.playerName;
}

function getCurrentPlayer() {
    return window.gameState.playerName;
}

function isCurrentUserHost() {
    return window.gameState.isHost === true;
}

// Debug helpers (only in development)
function debugGameState() {
    console.table(window.gameState);
}

function logAPICall(endpoint, options) {
    console.log(`🌐 API Call: ${endpoint}`, options);
}

// REMOVED: Error boundary that causes the alerts - THIS WAS THE PROBLEM!
// The global error listeners were causing the annoying alerts

// Cleanup function for page unload
window.addEventListener('beforeunload', () => {
    // Clean up any active intervals or timeouts
    if (window.roomStatusPolling) {
        clearInterval(window.roomStatusPolling);
    }
    if (window.gamePolling) {
        clearInterval(window.gamePolling);
    }
});

// Make key functions globally available
window.updateGameState = updateGameState;
window.loadGameState = loadGameState;
window.clearGameState = clearGameState;
window.apiCall = apiCall;
window.apiCallFormData = apiCallFormData;
window.showElement = showElement;
window.hideElement = hideElement;
window.showError = showError;
window.showSuccess = showSuccess;
window.showMessage = showMessage; // ADDED: Make showMessage globally available
window.copyToClipboard = copyToClipboard; // ADDED: Make copyToClipboard globally available

console.log('✅ Multiplayer Common.js loaded successfully - ALERTS REMOVED');
