// Player-specific functionality - FINAL FIXED VERSION
let lobbyStatusInterval;
let isJoining = false;
let currentRoomStatus = null;
let playerReadyState = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('👤 Player page initializing...');
    
    clearGameState();
    
    const roomCodeInput = document.getElementById('roomCodeInput');
    if (roomCodeInput) {
        roomCodeInput.focus();
    }
    
    if (roomCodeInput) {
        roomCodeInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 6) {
                value = value.substring(0, 6);
            }
            e.target.value = value;
        });
        
        roomCodeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                joinRoom(e);
            }
        });
    }
    
    const playerNameInput = document.getElementById('playerNameInput');
    if (playerNameInput) {
        playerNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                joinRoom(e);
            }
        });
    }
});

async function joinRoom(event) {
    event.preventDefault();
    
    if (isJoining) {
        return;
    }
    
    const roomCodeInput = document.getElementById('roomCodeInput');
    const playerNameInput = document.getElementById('playerNameInput');
    const joinBtn = document.getElementById('joinBtn');
    
    const roomCode = roomCodeInput?.value.trim() || '';
    const playerName = playerNameInput?.value.trim() || '';
    
    console.log('👤 Attempting to join room:', roomCode);
    
    if (!validateRoomCode(roomCode)) {
        showError('Please enter a valid 6-digit room code');
        if (roomCodeInput) roomCodeInput.focus();
        return;
    }
    
    if (!validatePlayerName(playerName)) {
        showError('Please enter a name between 2-20 characters');
        if (playerNameInput) playerNameInput.focus();
        return;
    }
    
    try {
        isJoining = true;
        hideElement('errorState');
        
        if (joinBtn) {
            joinBtn.disabled = true;
            joinBtn.textContent = '🔄 Joining...';
            joinBtn.classList.add('loading');
        }
        
        console.log('🚀 Calling join-room API...');
        
        const response = await apiCall('/join-room', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                room_code: roomCode,
                player_name: playerName
            })
        });
        
        console.log('✅ Successfully joined room:', response);
        
        updateGameState({
            roomCode: roomCode,
            playerName: response.players?.[1] || playerName,
            playerId: response.player_id,
            isHost: false,
            players: response.players || [response.players?.[0] || 'Host', playerName]
        });
        
        updateLobbyUI(roomCode, response);
        
        hideElement('joinForm');
        showElement('lobby');
        
        startLobbyStatusPolling();
        
        console.log('🏛️ Entered lobby successfully');
        
    } catch (error) {
        console.error('❌ Join room failed:', error);
        
        if (joinBtn) {
            joinBtn.disabled = false;
            joinBtn.textContent = '🚪 Join Game';
            joinBtn.classList.remove('loading');
        }
        
        if (error.message.includes('Room not found')) {
            showError('Room not found. Please check the room code and try again.');
        } else if (error.message.includes('Room is full')) {
            showError('Room is full. Please wait for the game to finish or try another room.');
        } else if (error.message.includes('Player name already taken')) {
            showError('Player name already taken. Please choose a different name.');
        } else if (error.message.includes('401')) {
            showError('Session expired. Please sign in again.');
            setTimeout(() => {
                window.location.href = '/signin';
            }, 2000);
        } else {
            showError('Failed to join room: ' + (error.message || 'Unknown error'));
        }
        
    } finally {
        isJoining = false;
    }
}

function updateLobbyUI(roomCode, response) {
    try {
        const roomCodeElements = document.querySelectorAll('#currentRoomCode, .room-code, [data-room-code]');
        roomCodeElements.forEach(el => {
            if (el) el.textContent = roomCode;
        });
        
        const playerNameElements = document.querySelectorAll('#playerName, .player-name');
        const actualPlayerName = response.players?.[1] || window.gameState.playerName;
        playerNameElements.forEach(el => {
            if (el) el.textContent = actualPlayerName;
        });
        
        if (response.players && response.players.length >= 1) {
            const hostNameElements = document.querySelectorAll('#hostName, .host-name');
            hostNameElements.forEach(el => {
                if (el) el.textContent = response.players[0];
            });
        }
        
        const playerCountElements = document.querySelectorAll('#playerCount, .player-count');
        playerCountElements.forEach(el => {
            if (el) el.textContent = response.players_count || response.players?.length || 2;
        });
        
        console.log('🎨 Lobby UI updated successfully');
        
    } catch (error) {
        console.warn('⚠️ Failed to update lobby UI:', error);
    }
}

function startLobbyStatusPolling() {
    console.log('🔄 Starting lobby status polling...');
    
    lobbyStatusInterval = setInterval(async () => {
        try {
            const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
            currentRoomStatus = status;
            
            if (status.state === 'suspended') {
                clearInterval(lobbyStatusInterval);
                showError('Game suspended due to inactivity. Please join again.');
                setTimeout(() => {
                    goToMultiplayerHome();
                }, 3000);
                return;
            }
            
            if (!status || status.error) {
                clearInterval(lobbyStatusInterval);
                showError('Room no longer exists. It may have expired.');
                setTimeout(() => {
                    goToMultiplayerHome();
                }, 3000);
                return;
            }
            
            updateReadyStatus(status);
            
            if (status.state === 'all_ready') {
                console.log('🚀 Both players ready - waiting for host to start');
                showElement('waitingHost');
                if (!playerReadyState) {
                    hideElement('readySection');
                }
            } else {
                hideElement('waitingHost');
                if (!playerReadyState) {
                    showElement('readySection');
                }
            }
            
            if (status.state === 'playing') {
                console.log('🎮 Game started - redirecting to game');
                clearInterval(lobbyStatusInterval);
                redirectToGame();
            }
            
        } catch (error) {
            console.error('❌ Lobby polling error:', error);
            
            if (error.message && error.message.includes('401')) {
                clearInterval(lobbyStatusInterval);
                showError('Session expired. Please sign in again.');
                setTimeout(() => {
                    window.location.href = '/signin';
                }, 2000);
                return;
            }
            
            if (error.message && (error.message.includes('fetch') || error.message.includes('network'))) {
                console.warn('⚠️ Network error during polling, continuing...');
                return;
            }
            
            clearInterval(lobbyStatusInterval);
            showError('Connection lost. Please refresh and try again.');
        }
    }, 750);
    
    window.lobbyStatusPolling = lobbyStatusInterval;
}

// FIXED: Update ready status but preserve self-acknowledgment
// FIXED: Remove playerReadyState blocking - exact copy from working player.js 
function startLobbyStatusPolling() {
    lobbyStatusInterval = setInterval(async () => {
        try {
            const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
            
            if (status.state === 'suspended') {
                clearInterval(lobbyStatusInterval);
                showError('Game suspended due to inactivity. Please join again.');
                return;
            }
            
            // Update ready status - FIXED: No blocking flags
            const readyStatus = status.ready_status || {};
            const players = status.players || [];
            
            // Update host status - ALWAYS update from server
            if (players[0]) {
                const hostReady = readyStatus[players[0]];
                document.getElementById('hostStatus').textContent = hostReady ? '✅ Ready!' : '⏳ Not Ready';
            }
            
            // Update own status - ALWAYS update from server
            if (players[1]) {
                const playerReady = readyStatus[players[1]];
                document.getElementById('playerStatus').textContent = playerReady ? '✅ Ready!' : '⏳ Not Ready';
            }
            
            // Show waiting for host if both ready
            if (status.state === 'all_ready') {
                showElement('waitingHost');
            }
            
            // Redirect to game if started
            if (status.state === 'playing') {
                clearInterval(lobbyStatusInterval);
                redirectToGame();
            }
            
        } catch (error) {
            console.error('Lobby polling error:', error);
            clearInterval(lobbyStatusInterval);
            showError('Connection lost. Please refresh and try again.');
        }
    }, 750);
}

// FIXED: Professional toggle ready button functionality
// FIXED: Use correct button ID - playerReadyBtn
async function setReady() {
    try {
        console.log('👤 Player setReady called');
        
        // FIXED: Use the correct ID from your HTML
        const readyBtn = document.getElementById('playerReadyBtn');
        
        if (!readyBtn) {
            console.error('❌ playerReadyBtn not found!');
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
                player_name: window.gameState.playerName
            })
        });
        
        readyBtn.textContent = '✅ Ready!';
        readyBtn.classList.remove('btn-success');
        readyBtn.classList.add('btn-warning');
        
        // FIXED: Update player status
        const playerStatus = document.getElementById('playerStatus');
        if (playerStatus) {
            playerStatus.textContent = '✅ Ready!';
        }
        
        console.log('✅ Player ready status set successfully');
        
    } catch (error) {
        console.error('❌ Player setReady error:', error);
        
        const readyBtn = document.getElementById('playerReadyBtn');
        if (readyBtn) {
            readyBtn.disabled = false;
            readyBtn.textContent = '✅ I\'m Ready!';
        }
        
        showError('Failed to set ready status: ' + error.message);
    }
}

function setPlayerReady() {
    setReady();
}

function validateRoomCode(code) {
    return code && code.length === 6 && /^\d+$/.test(code);
}

function validatePlayerName(name) {
    return !name || (name.length >= 2 && name.length <= 20);
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

function shareRoomCode() {
    const roomCode = currentRoomStatus?.room_code || window.gameState.roomCode;
    
    if (!roomCode) {
        showError('No room code available to share');
        return;
    }
    
    const shareText = `Join my yoga challenge! Room code: ${roomCode}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Join My Yoga Challenge',
            text: shareText
        }).then(() => {
            showMessage('Room code shared successfully!');
        }).catch((error) => {
            console.log('Share cancelled or failed:', error);
            fallbackShare(shareText);
        });
    } else {
        fallbackShare(shareText);
    }
}

function fallbackShare(text) {
    navigator.clipboard.writeText(text).then(() => {
        showMessage('Room code copied to clipboard!');
    }).catch(() => {
        showError('Failed to copy room code');
    });
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
    showMessage('Connection restored');
    
    if (!lobbyStatusInterval && currentRoomStatus) {
        startLobbyStatusPolling();
    }
});

window.addEventListener('offline', () => {
    updateConnectionStatus(false);
    showError('Connection lost. Waiting for network...');
});

function handlePlayerError(error, context = '') {
    console.error(`❌ Player error ${context}:`, error);
    
    if (error.message && error.message.includes('401')) {
        showError('Session expired. Please sign in again.');
        setTimeout(() => {
            window.location.href = '/signin';
        }, 2000);
    } else if (error.message && error.message.includes('Room not found')) {
        showError('Room no longer exists. Returning to multiplayer home...');
        setTimeout(() => {
            goToMultiplayerHome();
        }, 2000);
    } else {
        showError(context + ': ' + (error.message || 'Unknown error occurred'));
    }
}

function highlightValidationError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('error');
        element.focus();
        
        setTimeout(() => {
            element.classList.remove('error');
        }, 3000);
    }
    showError(message);
}

function debugPlayerState() {
    console.table({
        'Room Code': window.gameState.roomCode,
        'Player Name': window.gameState.playerName,
        'Player ID': window.gameState.playerId,
        'Is Host': window.gameState.isHost,
        'Players': window.gameState.players?.join(', ') || 'None',
        'Player Ready': playerReadyState,
        'Room Status': currentRoomStatus?.state || 'Unknown',
        'Is Joining': isJoining
    });
}

window.addEventListener('beforeunload', function() {
    console.log('🧹 Cleaning up player intervals...');
    
    if (lobbyStatusInterval) {
        clearInterval(lobbyStatusInterval);
    }
    
    if (window.lobbyStatusPolling) {
        clearInterval(window.lobbyStatusPolling);
    }
});

if (typeof window !== 'undefined') {
    window.debugPlayerState = debugPlayerState;
}

console.log('✅ Multiplayer Player.js loaded successfully - COMPLETELY FIXED');
