// Host-specific functionality - FINAL FIXED VERSION
let roomStatusInterval;
let lobbyStatusInterval;
let isGameStarted = false;
let currentRoomState = null;
let hostReadyState = false;

// Initialize host interface
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🏠 Host page initializing...');
    try {
        clearGameState();
        await createRoom();
    } catch (error) {
        console.error('❌ Host initialization failed:', error);
        showError('Failed to initialize host: ' + error.message);
    }
});

async function createRoom() {
    try {
        console.log('🏗️ Creating room...');
        showElement('roomCreation');
        hideElement('roomReady');
        hideElement('lobby');
        hideElement('errorState');
        
        const response = await apiCall('/create-room', {
            method: 'POST'
        });
        
        console.log('✅ Room created:', response);
        
        updateGameState({
            roomCode: response.room_code,
            hostId: response.host_id,
            isHost: true,
            playerName: 'Host'
        });
        
        const roomCodeElements = document.querySelectorAll('#roomCode, .room-code, [data-room-code]');
        roomCodeElements.forEach(el => {
            if (el) el.textContent = response.room_code;
        });
        
        console.log(`🎯 Room ${response.room_code} ready for players`);
        
        hideElement('roomCreation');
        showElement('roomReady');
        startRoomStatusPolling();
        
    } catch (error) {
        console.error('❌ Create room error:', error);
        showError('Failed to create room: ' + error.message);
        
        setTimeout(() => {
            const retryBtn = document.getElementById('retryCreateBtn');
            if (retryBtn) {
                showElement('retryCreateBtn');
            }
        }, 2000);
    }
}

function startRoomStatusPolling() {
    console.log('🔄 Starting room status polling...');
    
    roomStatusInterval = setInterval(async () => {
        try {
            const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
            
            currentRoomState = status;
            
            const playerCountElements = document.querySelectorAll('#playerCount, .player-count');
            playerCountElements.forEach(el => {
                if (el) el.textContent = status.players_count;
            });
            
            if (status.state === 'suspended') {
                clearInterval(roomStatusInterval);
                showError('Game suspended due to inactivity. Please start again.');
                return;
            }
            
            if (status.players_count === 2 && !isGameStarted) {
                console.log('👥 Both players joined - transitioning to lobby');
                
                clearInterval(roomStatusInterval);
                
                updateGameState({ 
                    players: status.players,
                    playerName: status.players[0] || 'Host'
                });
                
                const playerNameElements = document.querySelectorAll('#playerName, .other-player-name');
                playerNameElements.forEach(el => {
                    if (el) el.textContent = status.players[1] || 'Player 2';
                });
                
                hideElement('roomReady');
                showElement('lobby');
                startLobbyStatusPolling();
            }
            
        } catch (error) {
            console.error('❌ Room status polling error:', error);
        }
    }, 2000);
    
    window.roomStatusPolling = roomStatusInterval;
}

function startLobbyStatusPolling() {
    console.log('🏛️ Starting lobby status polling...');
    
    lobbyStatusInterval = setInterval(async () => {
        try {
            const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
            updateLobbyStatus(status);
            
            if (status.state === 'playing') {
                console.log('🎮 Game started - redirecting to game');
                clearInterval(lobbyStatusInterval);
                isGameStarted = true;
                redirectToGame();
            }
            
        } catch (error) {
            console.error('❌ Lobby polling error:', error);
        }
    }, 750);
    
    window.lobbyStatusPolling = lobbyStatusInterval;
}

// FIXED: Remove hostReadyState blocking - exact copy from working host.js
function startLobbyStatusPolling() {
    console.log('🏛️ Starting lobby status polling...');
    lobbyStatusInterval = setInterval(async () => {
        try {
            const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
            
            // Update ready status - FIXED: No blocking flags
            const readyStatus = status.ready_status || {};
            const players = status.players || [];
            
            // Update host status - ALWAYS update from server
            if (players[0]) {
                const hostReady = readyStatus[players[0]];
                document.getElementById('hostStatus').textContent = hostReady ? '✅ Ready!' : '⏳ Not Ready';
            }
            
            // Update player status - ALWAYS update from server  
            if (players[1]) {
                const playerReady = readyStatus[players[1]];
                document.getElementById('playerStatus').textContent = playerReady ? '✅ Ready!' : '⏳ Not Ready';
            }
            
            // Show game start controls if both ready
            if (status.state === 'all_ready') {
                showElement('gameStartSection');
            }
            
            // Check if game started
            if (status.state === 'playing') {
                clearInterval(lobbyStatusInterval);
                isGameStarted = true;
                redirectToGame();
            }
            
        } catch (error) {
            console.error('❌ Lobby polling error:', error);
        }
    }, 750);
}

// FIXED: Host ready with immediate self-acknowledgment
// FIXED: Use correct button ID - hostReadyBtn
async function setReady() {
    try {
        console.log('👑 Host setReady called');
        
        // FIXED: Use the correct ID from your HTML
        const readyBtn = document.getElementById('hostReadyBtn');
        
        if (!readyBtn) {
            console.error('❌ hostReadyBtn not found!');
            showError('Ready button not available');
            return;
        }
        
        console.log('✅ Found ready button:', readyBtn);
        
        readyBtn.disabled = true;
        readyBtn.textContent = 'Setting Ready...';
        
        await apiCall('/player-ready', {
            method: 'POST',
            body: JSON.stringify({
                room_code: window.gameState.roomCode,
                player_name: window.gameState.players?.[0] || 'Host'
            })
        });
        
        readyBtn.textContent = '✅ Ready!';
        readyBtn.classList.remove('btn-success');
        readyBtn.classList.add('btn-warning');
        
        // FIXED: Update host status
        const hostStatus = document.getElementById('hostStatus');
        if (hostStatus) {
            hostStatus.textContent = '✅ Ready!';
        }
        
        console.log('✅ Host ready status set successfully');
        
    } catch (error) {
        console.error('❌ Host setReady error:', error);
        
        const readyBtn = document.getElementById('hostReadyBtn');
        if (readyBtn) {
            readyBtn.disabled = false;
            readyBtn.textContent = '✅ I\'m Ready!';
        }
        
        showError('Failed to set ready status: ' + error.message);
    }
}


function toggleHostReady() {
    setReady();
}

async function startGame() {
    try {
        console.log('🚀 Starting game...');
        
        const startBtn = document.getElementById('startGameBtn');
        const gameModeSelect = document.getElementById('gameModeSelect');
        
        const gameMode = gameModeSelect ? gameModeSelect.value : 'normal';
        
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = 'Starting Game...';
        }
        
        const response = await apiCall('/start-game', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                room_code: window.gameState.roomCode,
                game_mode: gameMode
            })
        });
        
        console.log('✅ Game started:', response);
        
        updateGameState({ gameMode });
        redirectToGame();
        
    } catch (error) {
        console.error('❌ Start game error:', error);
        
        const startBtn = document.getElementById('startGameBtn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = '🚀 START GAME';
        }
        
        showError('Failed to start game: ' + error.message);
    }
}

// FIXED: Copy room code function
function copyRoomCode() {
    const code = window.gameState.roomCode;
    
    if (!code) {
        showError('No room code available to copy');
        return;
    }
    
    // FIXED: Use proper copyToClipboard function
    navigator.clipboard.writeText(code).then(() => {
        console.log('📋 Room code copied:', code);
        
        const copyBtn = document.getElementById('copyBtn');
        if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '✅ Copied!';
            copyBtn.classList.add('btn-success');
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('btn-success');
            }, 2000);
        }
        
        // FIXED: Use showMessage instead of showSuccess
        showMessage('Room code copied to clipboard!');
        
    }).catch((error) => {
        console.error('❌ Copy failed:', error);
        showError('Failed to copy room code. Please copy manually: ' + code);
    });
}

async function retryCreateRoom() {
    console.log('🔄 Retrying room creation...');
    hideElement('retryCreateBtn');
    await createRoom();
}

function goToMultiplayerHome() {
    console.log('🏠 Returning to multiplayer home...');
    clearGameState();
    window.location.href = '/multiplayer';
}

function goToDashboard() {
    console.log('🏠 Returning to dashboard...');
    clearGameState();
    window.location.href = '/home';
}

function handleHostError(error, context = '') {
    console.error(`❌ Host error ${context}:`, error);
    
    if (error.message && error.message.includes('401')) {
        showError('Session expired. Please sign in again.');
        setTimeout(() => {
            window.location.href = '/signin';
        }, 2000);
    } else if (error.message && error.message.includes('Room not found')) {
        showError('Room has expired. Creating a new room...');
        setTimeout(() => {
            retryCreateRoom();
        }, 2000);
    } else {
        showError(context + ': ' + (error.message || 'Unknown error occurred'));
    }
}

function safeUpdateRoomDisplay() {
    try {
        if (currentRoomState) {
            const playerCountElements = document.querySelectorAll('#playerCount, .player-count');
            playerCountElements.forEach(el => {
                if (el) el.textContent = currentRoomState.players_count;
            });
        }
    } catch (error) {
        console.warn('Failed to update room display:', error);
    }
}

function updateConnectionStatus(isConnected) {
    const statusIndicators = document.querySelectorAll('.connection-status');
    statusIndicators.forEach(indicator => {
        if (indicator) {
            indicator.textContent = isConnected ? '🟢 Connected' : '🔴 Disconnected';
            indicator.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
        }
    });
}

window.addEventListener('online', () => {
    updateConnectionStatus(true);
    console.log('🟢 Connection restored');
});

window.addEventListener('offline', () => {
    updateConnectionStatus(false);
    showError('Connection lost. Game may not function properly.');
});

window.addEventListener('beforeunload', function() {
    console.log('🧹 Cleaning up host intervals...');
    
    if (roomStatusInterval) {
        clearInterval(roomStatusInterval);
    }
    
    if (lobbyStatusInterval) {
        clearInterval(lobbyStatusInterval);
    }
    
    if (window.roomStatusPolling) {
        clearInterval(window.roomStatusPolling);
    }
    
    if (window.lobbyStatusPolling) {
        clearInterval(window.lobbyStatusPolling);
    }
});

function debugHostState() {
    console.table({
        'Room Code': window.gameState.roomCode,
        'Is Host': window.gameState.isHost,
        'Players': window.gameState.players?.join(', ') || 'None',
        'Host Ready': hostReadyState,
        'Game Started': isGameStarted,
        'Current State': currentRoomState?.state || 'Unknown'
    });
}

if (typeof window !== 'undefined') {
    window.debugHostState = debugHostState;
}

// FIXED: Prevent "Leave site?" alerts completely
window.addEventListener('beforeunload', function(e) {
    // DON'T prevent default - just cleanup silently
    console.log('🧹 Page unloading - cleaning up...');
    
    // Clean up intervals
    if (roomStatusInterval) {
        clearInterval(roomStatusInterval);
    }
    if (lobbyStatusInterval) {
        clearInterval(lobbyStatusInterval);
    }
    
    // DON'T set returnValue or preventDefault - this causes the alert
    // delete e.returnValue;  // Remove any existing returnValue
});

// FIXED: Also prevent any forms from triggering beforeunload
document.addEventListener('DOMContentLoaded', function() {
    // Remove beforeunload from all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Allow form submission without beforeunload
            window.removeEventListener('beforeunload', arguments.callee);
        });
    });
});


console.log('✅ Multiplayer Host.js loaded successfully - COMPLETELY FIXED');
