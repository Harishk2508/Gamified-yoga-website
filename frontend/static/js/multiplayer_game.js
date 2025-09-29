// Game state variables
let gameTimer;
let countdownTimer;
let roundPollingInterval;
let currentRoundData = null;
let hasSubmittedThisRound = false;
let referenceUsedThisRound = false;
let lastStateChange = null;

// Initialize game
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🎮 Game page initializing...');
    try {
        // Load game state from common.js
        loadGameState();
        
        if (!window.gameState || !window.gameState.roomCode) {
            throw new Error('No active game found. Please start a new game.');
        }
        
        console.log('🏠 Loading game for room:', window.gameState.roomCode);
        
        // Store room code for results page
        localStorage.setItem('currentRoomCode', window.gameState.roomCode);
        sessionStorage.setItem('currentRoomCode', window.gameState.roomCode);
        
        // Show loading state
        showElement('loadingState');
        hideElement('errorState');
        
        // Initialize the game
        await initializeGame();
        
    } catch (error) {
        console.error('❌ Game initialization failed:', error);
        showError(error.message || 'Failed to initialize game');
    }
});

async function initializeGame() {
    try {
        console.log('🚀 Initializing game...');
        
        // Get room status
        const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
        console.log('📊 Room status:', status);
        
        if (status.state !== 'playing') {
            throw new Error('Game is not active. Please start a new game.');
        }
        
        // Setup UI with player info
        setupPlayerDisplay(status.players, status.scores);
        
        // Check game state
        if (status.current_round > 0) {
            await checkCurrentRound();
        } else {
            await startNewRound();
        }
        
    } catch (error) {
        console.error('❌ Initialize game error:', error);
        showError('Failed to initialize game: ' + error.message);
    }
}

function setupPlayerDisplay(players, scores) {
    try {
        const currentPlayer = window.gameState.playerName;
        console.log('👥 Setting up players:', players);
        
        // Update player names and scores safely
        const player1NameEl = document.getElementById('player1Name');
        const player2NameEl = document.getElementById('player2Name');
        const player1ScoreEl = document.getElementById('player1Score');
        const player2ScoreEl = document.getElementById('player2Score');
        
        if (player1NameEl) player1NameEl.textContent = players[0] || 'Player 1';
        if (player2NameEl) player2NameEl.textContent = players[1] || 'Player 2';
        if (player1ScoreEl) player1ScoreEl.textContent = (scores && scores[players[0]]) || 0;
        if (player2ScoreEl) player2ScoreEl.textContent = (scores && scores[players[1]]) || 0;
        
        // Store players for later use
        window.gameState.players = players;
        updateGameState({ players: players });
        
    } catch (error) {
        console.error('❌ Setup player display error:', error);
    }
}

async function startNewRound() {
    try {
        console.log('🎯 Starting new round...');
        
        // Get current room status
        const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
        const nextRound = status.current_round + 1;
        const totalRounds = status.total_rounds;
        
        console.log(`🎯 Preparing Round ${nextRound} of ${totalRounds}`);
        
        // Show countdown
        hideElement('loadingState');
        showElement('preCountdown');
        
        // Update round text immediately
        function updateAllRoundText() {
            const possibleElements = [
                'preRoundNumber', 'roundNumber', 'round-number', 'currentRound', 
                'nextRoundText', 'countdownTitle', 'roundDisplay'
            ];
            
            possibleElements.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    if (el.textContent.includes('Round') || el.textContent.match(/\d/)) {
                        el.textContent = nextRound.toString();
                        console.log(`✅ Updated ${id} to: ${nextRound}`);
                    }
                }
            });
            
            // Update any text containing round info
            document.querySelectorAll('*').forEach(el => {
                if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                    const text = el.textContent.trim();
                    if (text.includes('pose coming up')) {
                        el.textContent = `Round ${nextRound} pose coming up...`;
                        console.log(`✅ Fixed: "${text}" → "Round ${nextRound} pose coming up..."`);
                    } else if (text.match(/^Round \d+$/)) {
                        el.textContent = `Round ${nextRound}`;
                        console.log(`✅ Fixed: "${text}" → "Round ${nextRound}"`);
                    }
                }
            });
        }
        
        // Update immediately and with delays
        updateAllRoundText();
        setTimeout(updateAllRoundText, 50);
        setTimeout(updateAllRoundText, 200);
        
        // Update countdown display
        const preRoundElement = document.getElementById('preRoundNumber');
        if (preRoundElement) preRoundElement.textContent = nextRound;
        
        // Start countdown
        let countdown = 5;
        const countdownEl = document.getElementById('countdownNumber');
        if (countdownEl) countdownEl.textContent = countdown;
        
        countdownTimer = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                if (countdownEl) countdownEl.textContent = countdown;
            } else {
                clearInterval(countdownTimer);
                startRoundFromServer();
            }
        }, 1000);
        
    } catch (error) {
        console.error('❌ Start new round error:', error);
        showError('Failed to start round: ' + error.message);
    }
}

async function startRoundFromServer() {
    try {
        console.log('🚀 Starting round from server...');
        
        const response = await apiCall(`/start-round/${window.gameState.roomCode}`, {
            method: 'POST'
        });
        
        console.log('📊 Round started:', response);
        // REMOVED: alert message here
        
        currentRoundData = response;
        
        // Update round information safely
        const currentRoundEl = document.getElementById('currentRound');
        const totalRoundsEl = document.getElementById('totalRounds');
        const asanaNameEl = document.getElementById('asanaName');
        const refAsanaEl = document.getElementById('referenceAsanaName');
        
        if (currentRoundEl) currentRoundEl.textContent = response.round_number;
        if (totalRoundsEl) totalRoundsEl.textContent = response.total_rounds;
        if (asanaNameEl) asanaNameEl.textContent = response.asana;
        if (refAsanaEl) refAsanaEl.textContent = response.asana;
        
        // Update game mode display
        const gameMode = response.total_rounds === 3 ? 'Rapid Mode' : 'Normal Mode';
        console.log(`🎮 Game Mode: ${gameMode} (${response.total_rounds} rounds)`);
        
        setTimeout(() => {
            document.querySelectorAll('*').forEach(el => {
                if (el.textContent && (el.textContent.trim() === 'Normal Mode' || el.textContent.trim() === 'Rapid Mode')) {
                    el.textContent = gameMode;
                    console.log(`✅ Updated mode display: ${gameMode}`);
                }
            });
        }, 100);
        
        // Store asana key for reference
        window.currentAsanaKey = response.asana_key || response.asana.toLowerCase().replace(/\s+/g, '_');
        
        // Reset round state
        hasSubmittedThisRound = false;
        referenceUsedThisRound = false;
        resetUploadArea();
        
        // Switch to game interface
        hideElement('preCountdown');
        showElement('gameInterface');
        
        // Start polling for round updates
        startRoundPolling();
        
        console.log(`✅ Round ${response.round_number} started: ${response.asana}`);
        
    } catch (error) {
        console.error('❌ Start round from server error:', error);
        showError('Failed to start round: ' + error.message);
    }
}

function startRoundPolling() {
    console.log('🔄 Starting round polling...');
    
    roundPollingInterval = setInterval(async () => {
        try {
            const roundInfo = await apiCall(`/round-info/${window.gameState.roomCode}`);
            
            if (roundInfo.active) {
                // Update timer
                const minutes = Math.floor(roundInfo.time_left / 60);
                const seconds = roundInfo.time_left % 60;
                const timerText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                const timerEl = document.getElementById('timerText');
                if (timerEl) timerEl.textContent = timerText;
                
                // Update player status
                updatePlayersStatus(roundInfo.submissions_count || 0);
                
            } else {
                // Round ended
                clearInterval(roundPollingInterval);
                console.log('⏰ Round ended'); // REMOVED: alert message
                
                if (roundInfo.game_finished) {
                    console.log('🏆 Game completed!');
                    navigateToResults();
                } else {
                    console.log('📊 Round finished, showing results');
                    await showRoundResults();
                }
            }
            
        } catch (error) {
            console.error('❌ Round polling error:', error);
        }
    }, 1000);
}

function updatePlayersStatus(submissionCount) {
    const player1IndEl = document.getElementById('player1Indicator');
    const player2IndEl = document.getElementById('player2Indicator');
    
    if (submissionCount === 0) {
        if (player1IndEl) player1IndEl.textContent = '⏳ Preparing';
        if (player2IndEl) player2IndEl.textContent = '⏳ Preparing';
    } else if (submissionCount === 1) {
        if (hasSubmittedThisRound) {
            if (player1IndEl) player1IndEl.textContent = '✅ Submitted';
            if (player2IndEl) player2IndEl.textContent = '⏳ Preparing';
        } else {
            if (player1IndEl) player1IndEl.textContent = '⏳ Preparing';
            if (player2IndEl) player2IndEl.textContent = '✅ Submitted';
        }
    } else {
        if (player1IndEl) player1IndEl.textContent = '✅ Submitted';
        if (player2IndEl) player2IndEl.textContent = '✅ Submitted';
    }
}

// Image upload handling
function triggerFileInput() {
    if (hasSubmittedThisRound) {
        console.log('⚠️ Already submitted for this round'); // REMOVED: alert message
        showError('You have already submitted for this round!');
        return;
    }
    
    const fileInput = document.getElementById('imageInput');
    if (fileInput) {
        fileInput.click();
    }
}

function handleImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        console.log('⚠️ Invalid file type selected'); // REMOVED: alert message
        showError('Please select a valid image file.');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        console.log('⚠️ File too large'); // REMOVED: alert message
        showError('Image file too large. Please select an image under 10MB.');
        return;
    }
    
    console.log('📸 Image selected:', file.name);
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('uploadPreview');
        if (preview) {
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Pose preview" style="max-width: 200px; max-height: 150px; border-radius: 8px;">
                <p>${file.name}</p>
            `;
            showElement('uploadPreview');
            showElement('submitBtn');
            hideElement('uploadContent');
        }
    };
    reader.readAsDataURL(file);
}

async function submitPose() {
    if (hasSubmittedThisRound) {
        console.log('⚠️ Already submitted for this round'); // REMOVED: alert message
        showError('You have already submitted for this round!');
        return;
    }
    
    const fileInput = document.getElementById('imageInput');
    const file = fileInput?.files[0];
    
    if (!file) {
        console.log('⚠️ No image selected'); // REMOVED: alert message
        showError('Please select an image first.');
        return;
    }
    
    try {
        console.log('📤 Submitting pose...');
        
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = '📤 Uploading...';
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('player_name', window.gameState.playerName);
        
        const response = await apiCallFormData(`/upload-image/${window.gameState.roomCode}`, formData);
        
        hasSubmittedThisRound = true;
        
        if (submitBtn) {
            submitBtn.textContent = '✅ Submitted!';
            submitBtn.style.background = '#4CAF50';
        }
        
        console.log('✅ Pose submitted successfully');
        showSuccess(response.message);
        
    } catch (error) {
        console.error('❌ Submit pose error:', error);
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '✅ Submit My Pose';
        }
        showError('Failed to submit pose: ' + error.message);
    }
}

// Reference handling
function requestReference() {
    if (referenceUsedThisRound) {
        console.log('⚠️ Reference already used for this round'); // REMOVED: alert message
        showError('You have already used the reference for this round.');
        return;
    }
    
    try {
        console.log('🖼️ Opening reference modal...');
        const asanaName = document.getElementById('asanaName')?.textContent || 'Unknown Pose';
        
        const refAsanaElement = document.getElementById('referenceAsanaName');
        if (refAsanaElement) {
            refAsanaElement.textContent = asanaName;
        }
        
        showElement('referenceWarningStep');
        hideElement('referenceImageStep');
        showElement('referenceModal');
        
    } catch (error) {
        console.error('❌ Error opening reference modal:', error);
        showError('Failed to open reference modal.');
    }
}

async function acceptPenaltyAndShowImage() {
    try {
        console.log('💰 Accepting penalty...');
        
        const formData = new FormData();
        formData.append('player_name', window.gameState.playerName);
        
        await apiCallFormData(`/use-reference/${window.gameState.roomCode}`, formData);
        
        referenceUsedThisRound = true;
        
        const refBtn = document.getElementById('referenceBtn');
        if (refBtn) {
            refBtn.textContent = '✅ Reference Used (-2 points)';
            refBtn.disabled = true;
            refBtn.style.background = '#dc3545';
        }
        
        hideElement('referenceWarningStep');
        showElement('referenceImageStep');
        loadReferenceImage();
        
    } catch (error) {
        console.error('❌ Error accepting penalty:', error);
        showError('Failed to load reference: ' + error.message);
    }
}

function loadReferenceImage() {
    const imageContent = document.getElementById('referenceImageContent');
    if (!imageContent) return;
    
    const asanaKey = window.currentAsanaKey || 'unknown';
    console.log(`🖼️ Loading reference image for: ${asanaKey}`);
    
    // Updated path to match base module structure
    const imageUrl = `/api/reference-image/${asanaKey}`;
    
    imageContent.innerHTML = `
        <img src="${imageUrl}" alt="${asanaKey} reference" 
             style="max-width: 100%; height: auto; border-radius: 8px;"
             onload="console.log('✅ Reference image loaded')"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
        <div style="display: none; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <p>⚠️ Reference image not available</p>
            <p>Use the pose name as guidance</p>
        </div>
        <p style="text-align: center; margin-top: 10px; color: #666;">
            Study the pose alignment and positioning
        </p>
    `;
}

function closeReferenceModal() {
    hideElement('referenceModal');
}

// Round results handling
async function showRoundResults() {
    try {
        console.log('📊 Loading round results...');
        
        const results = await apiCall(`/round-results/${window.gameState.roomCode}`);
        console.log('📊 Round results:', results);
        
        // Update round results display
        const roundNumberEl = document.getElementById('resultRoundNumber');
        const asanaResultEl = document.getElementById('resultAsanaName');
        
        if (roundNumberEl) roundNumberEl.textContent = results.round_number;
        if (asanaResultEl) asanaResultEl.textContent = results.asana;
        
        // Update player results
        const players = window.gameState.players || [];
        updatePlayerResult(players[0], results.results[players[0]] || {}, 'player1');
        updatePlayerResult(players[1], results.results[players[1]] || {}, 'player2');
        
        // Update total scores
        const totalPlayer1El = document.getElementById('totalPlayer1Score');
        const totalPlayer2El = document.getElementById('totalPlayer2Score');
        
        if (totalPlayer1El) totalPlayer1El.textContent = results.current_totals[players[0]] || 0;
        if (totalPlayer2El) totalPlayer2El.textContent = results.current_totals[players[1]] || 0;
        
        // Switch to results view
        hideElement('gameInterface');
        showElement('roundResults');
        
    } catch (error) {
        console.error('❌ Round results error:', error);
        showError('Failed to load round results: ' + error.message);
    }
}

function updatePlayerResult(playerName, result, playerPrefix) {
    const nameEl = document.getElementById(`${playerPrefix}ResultName`);
    const scoreEl = document.getElementById(`${playerPrefix}ResultScore`);
    
    if (nameEl) nameEl.textContent = playerName || 'Player';
    if (scoreEl) scoreEl.textContent = result.final_score || 0;
}

async function nextRound() {
    try {
        console.log('➡️ Proceeding to next round...');
        
        // Reset UI
        hideElement('roundResults');
        showElement('loadingState');
        
        // Check if game is complete
        const status = await apiCall(`/room-status/${window.gameState.roomCode}`);
        
        if (status.current_round >= status.total_rounds) {
            console.log('🏆 Game completed!');
            navigateToResults();
        } else {
            await startNewRound();
        }
        
    } catch (error) {
        console.error('❌ Next round error:', error);
        showError('Failed to proceed to next round: ' + error.message);
    }
}

async function checkCurrentRound() {
    try {
        console.log('🔍 Checking current round...');
        
        const roundInfo = await apiCall(`/round-info/${window.gameState.roomCode}`);
        
        if (roundInfo.active) {
            // Round is active, join it
            currentRoundData = {
                round_number: roundInfo.round_number,
                total_rounds: roundInfo.total_rounds,
                asana: roundInfo.asana,
                asana_key: roundInfo.asana_key
            };
            
            // Update UI
            const currentRoundEl = document.getElementById('currentRound');
            const totalRoundsEl = document.getElementById('totalRounds');
            const asanaNameEl = document.getElementById('asanaName');
            
            if (currentRoundEl) currentRoundEl.textContent = roundInfo.round_number;
            if (totalRoundsEl) totalRoundsEl.textContent = roundInfo.total_rounds;
            if (asanaNameEl) asanaNameEl.textContent = roundInfo.asana;
            
            window.currentAsanaKey = roundInfo.asana_key;
            
            hideElement('loadingState');
            showElement('gameInterface');
            
            startRoundPolling();
            
        } else if (roundInfo.game_finished) {
            navigateToResults();
        } else {
            await showRoundResults();
        }
        
    } catch (error) {
        console.error('❌ Check current round error:', error);
        showError('Failed to check current round: ' + error.message);
    }
}

function navigateToResults() {
    console.log('🏆 Navigating to results...');
    updateGameState({});
    window.location.href = `/multiplayer/results?room=${window.gameState.roomCode}`;
}

function resetUploadArea() {
    const uploadContent = document.getElementById('uploadContent');
    const uploadPreview = document.getElementById('uploadPreview');
    const submitBtn = document.getElementById('submitBtn');
    const fileInput = document.getElementById('imageInput');
    
    if (uploadContent) showElement('uploadContent');
    if (uploadPreview) hideElement('uploadPreview');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '✅ Submit My Pose';
        submitBtn.style.background = '';
        hideElement('submitBtn');
    }
    if (fileInput) fileInput.value = '';
    
    // Reset reference button
    const refBtn = document.getElementById('referenceBtn');
    if (refBtn && !referenceUsedThisRound) {
        refBtn.textContent = '📷 Reference Image';
        refBtn.disabled = false;
        refBtn.style.background = '';
    }
}

function refreshGame() {
    window.location.reload();
}

// FIXED: Dashboard redirect now points to /home
function goToHome() {
    console.log('🏠 Returning to home dashboard...');
    updateGameState({});
    window.location.href = '/home'; // FIXED: Changed from '/dashboard' to '/home'
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (countdownTimer) clearInterval(countdownTimer);
    if (roundPollingInterval) clearInterval(roundPollingInterval);
    if (gameTimer) clearInterval(gameTimer);
});
