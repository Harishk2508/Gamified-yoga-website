// Enhanced Results JavaScript - FIXED TO MATCH YOUR HTML STRUCTURE
let finalResults = null;
let currentRoomCode = null;
let resultsPollInterval = null;

// Initialize results page
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🏆 Initializing enhanced results page...');
    await initializeResults();
});

async function initializeResults() {
    console.log('🚀 Starting results initialization...');
    
    // Show loading state
    safeShowElement('loadingResults');
    safeHideElement('finalResults');
    safeHideElement('errorState');
    
    // Extract room code from multiple sources
    currentRoomCode = extractRoomCode();
    if (!currentRoomCode) {
        console.error('❌ No room code found');
        showError('Room code not provided. Please start a new game.');
        return;
    }
    
    console.log('🏠 Room code extracted:', currentRoomCode);
    
    try {
        // First check if room exists
        await checkRoomExists(currentRoomCode);
        
        // Fetch results with retry mechanism
        const response = await apiCallWithRetry(`/game-results/${currentRoomCode}`, {}, 3);
        console.log('📊 Results received:', response);
        
        // Display results
        displayEnhancedResults(response);
        
    } catch (error) {
        console.error('❌ Failed to fetch results:', error);
        handleResultsError(error);
    }
}

function extractRoomCode() {
    // Method 1: URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    let roomCode = urlParams.get('room');
    if (roomCode) {
        console.log('✅ Room code from URL params:', roomCode);
        return roomCode;
    }
    
    // Method 2: Hash parameters  
    const hash = window.location.hash;
    if (hash) {
        const hashParams = new URLSearchParams(hash.substring(1));
        roomCode = hashParams.get('room');
        if (roomCode) {
            console.log('✅ Room code from hash:', roomCode);
            return roomCode;
        }
    }
    
    // Method 3: Local storage backup
    roomCode = localStorage.getItem('currentRoomCode');
    if (roomCode) {
        console.log('✅ Room code from localStorage:', roomCode);
        return roomCode;
    }
    
    // Method 4: Session storage backup
    roomCode = sessionStorage.getItem('currentRoomCode');
    if (roomCode) {
        console.log('✅ Room code from sessionStorage:', roomCode);
        return roomCode;
    }
    
    // Method 5: Game state backup
    if (window.gameState && window.gameState.roomCode) {
        roomCode = window.gameState.roomCode;
        console.log('✅ Room code from game state:', roomCode);
        return roomCode;
    }
    
    console.error('❌ No room code found in any location');
    return null;
}

async function checkRoomExists(roomCode) {
    console.log('🔍 Checking if room exists:', roomCode);
    try {
        const response = await apiCall(`/room-status/${roomCode}`);
        console.log('✅ Room exists and is accessible');
        return response;
    } catch (error) {
        console.error('❌ Room check failed:', error);
        throw new Error('Room not found or has expired. Please start a new game.');
    }
}

function displayEnhancedResults(results) {
    finalResults = results;
    console.log('🎨 Displaying enhanced results...', results);
    
    // Hide loading, show results
    safeHideElement('loadingResults');
    safeShowElement('finalResults');
    
    try {
        // Update all result sections
        updateWinnerAnnouncement(results);
        updatePlayerScores(results);
        updateGameStatistics(results);
        updateRoundHistory(results);
        
        // ADDED: Display AI feedback in existing info-cards section
        displayAIFeedbackInInfoCards(results);
        
        // Store room code for future reference
        storeRoomCode(results.room_code);
        
        console.log('✅ Enhanced results displayed successfully');
        
    } catch (error) {
        console.error('❌ Error displaying results:', error);
        showError('Failed to display results properly: ' + error.message);
    }
}

function updateWinnerAnnouncement(results) {
    try {
        const player1 = results.players[0];
        const player2 = results.players[1];
        const score1 = results.scores[player1] || 0;
        const score2 = results.scores[player2] || 0;
        const winner = results.winner;
        
        console.log('🏆 Winner announcement:', { player1, player2, score1, score2, winner });
        
        const winnerCard = document.getElementById('winnerCard');
        const winnerTitle = document.getElementById('winnerTitle');
        const winnerSubtitle = document.getElementById('winnerSubtitle');
        
        if (winner === 'TIE') {
            // It's a tie
            if (winnerCard) {
                winnerCard.classList.add('tie');
                const winnerIcon = winnerCard.querySelector('.winner-icon');
                if (winnerIcon) winnerIcon.textContent = '🤝';
            }
            if (winnerTitle) winnerTitle.textContent = `It's a Tie! Both scored ${score1} points!`;
            if (winnerSubtitle) winnerSubtitle.textContent = 'Great yoga practice from both players!';
            
        } else {
            // We have a winner
            const winnerScore = winner === player1 ? score1 : score2;
            if (winnerCard) winnerCard.classList.remove('tie');
            if (winnerTitle) winnerTitle.textContent = `${winner} wins with ${winnerScore} points!`;
            if (winnerSubtitle) winnerSubtitle.textContent = `Congratulations on an excellent performance!`;
        }
        
    } catch (error) {
        console.warn('⚠️ Failed to update winner announcement:', error);
    }
}

function updatePlayerScores(results) {
    try {
        const players = results.players || [];
        const scores = results.scores || {};
        
        // Player 1
        if (players[0]) {
            safeUpdateElement('player1Name', players[0]);
            safeUpdateElement('player1Score', scores[players[0]] || 0);
            
            // Add winner styling
            const player1Card = document.getElementById('player1Card');
            if (player1Card && results.winner === players[0]) {
                player1Card.classList.add('winner-card-player');
            }
        }
        
        // Player 2
        if (players[1]) {
            safeUpdateElement('player2Name', players[1]);
            safeUpdateElement('player2Score', scores[players[1]] || 0);
            
            // Add winner styling
            const player2Card = document.getElementById('player2Card');
            if (player2Card && results.winner === players[1]) {
                player2Card.classList.add('winner-card-player');
            }
        }
        
    } catch (error) {
        console.warn('⚠️ Failed to update player scores:', error);
    }
}

function updateGameStatistics(results) {
    try {
        // Game mode display
        const gameModeDisplay = results.game_mode === 'rapid' ? 'Rapid' : 'Normal';
        safeUpdateElement('gameMode', gameModeDisplay);
        
        // Rounds played
        const roundsPlayed = results.current_rounds_played || results.total_rounds || 0;
        const totalRounds = results.total_rounds || 0;
        safeUpdateElement('roundsPlayed', `${roundsPlayed}/${totalRounds}`);
        
        // Room code
        safeUpdateElement('roomCode', results.room_code);
        safeUpdateElement('finalRoomCode', `Room: ${results.room_code}`);
        
        // ML status
        const mlStatus = results.ml_enabled ? '✅' : '⚠️';
        safeUpdateElement('mlStatus', mlStatus);
        
    } catch (error) {
        console.warn('⚠️ Failed to update game statistics:', error);
    }
}

function updateRoundHistory(results) {
    try {
        const roundHistoryContent = document.getElementById('roundHistoryContent');
        if (!roundHistoryContent) {
            console.warn('⚠️ Round history content element not found');
            return;
        }
        
        const roundHistory = results.round_history || {};
        const rounds = Object.keys(roundHistory).sort((a, b) => parseInt(a) - parseInt(b));
        
        if (rounds.length === 0) {
            roundHistoryContent.innerHTML = `
                <div class="round-item">
                    <div style="text-align: center; color: #666;">
                        <p>📊 Round details not available</p>
                        <p>Game completed successfully!</p>
                    </div>
                </div>
            `;
            return;
        }
        
        let historyHTML = '';
        
        rounds.forEach(roundNum => {
            const round = roundHistory[roundNum];
            const roundNumber = parseInt(roundNum);
            const asanaDisplay = round.asana_display || round.asana || 'Unknown Pose';
            const scores = round.scores || {};
            const players = results.players || [];
            
            historyHTML += `
                <div class="round-item">
                    <div class="round-header">
                        <strong>Round ${roundNumber}</strong>
                        <div class="round-asana">${asanaDisplay}</div>
                    </div>
                    <div class="round-scores">
                        <div class="score-item">
                            <div style="font-size: 0.9rem; color: #666;">${players[0] || 'Player 1'}</div>
                            <div style="font-weight: bold; color: #333;">${scores[players[0]] || 0}</div>
                        </div>
                        <div class="score-item">
                            <div style="font-size: 0.9rem; color: #666;">${players[1] || 'Player 2'}</div>
                            <div style="font-weight: bold; color: #333;">${scores[players[1]] || 0}</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        roundHistoryContent.innerHTML = historyHTML;
        
    } catch (error) {
        console.warn('⚠️ Failed to update round history:', error);
        const roundHistoryContent = document.getElementById('roundHistoryContent');
        if (roundHistoryContent) {
            roundHistoryContent.innerHTML = `
                <div class="round-item">
                    <div style="text-align: center; color: #666;">
                        <p>❌ Error loading round history</p>
                        <p>Game results are still available above</p>
                    </div>
                </div>
            `;
        }
    }
}

// CORRECTED: Display AI feedback in the existing info-cards section
function displayAIFeedbackInInfoCards(results) {
    console.log('🤖 Displaying AI feedback in info cards...');
    
    try {
        // Find the info-cards container
        const infoCardsContainer = document.querySelector('.info-cards');
        if (!infoCardsContainer) {
            console.warn('⚠️ Info cards container not found in HTML');
            return;
        }
        
        const roundHistory = results.round_history || {};
        const rounds = Object.keys(roundHistory).sort((a, b) => parseInt(a) - parseInt(b));
        const players = results.players || [];
        
        if (rounds.length === 0 || players.length === 0) {
            // Just update existing cards with proper content
            updateExistingInfoCards(results);
            return;
        }
        
        // Clear existing info cards and rebuild with feedback
        let feedbackHTML = '';
        
        // Add AI feedback cards for each round
        rounds.forEach(roundNum => {
            const round = roundHistory[roundNum];
            const roundNumber = parseInt(roundNum);
            const asanaDisplay = round.asana_display || round.asana || 'Unknown Pose';
            const detailedResults = round.detailed_results || {};
            
            feedbackHTML += `
                <div class="info-card">
                    <h4>🏃 Round ${roundNumber}: ${asanaDisplay}</h4>
                    <div style="margin-top: 10px;">
            `;
            
            // Player feedbacks
            players.forEach((player, index) => {
                if (detailedResults[player]) {
                    const playerData = detailedResults[player];
                    const feedback = playerData.feedback || 'No feedback available';
                    const score = playerData.final_score || 0;
                    const poseScore = playerData.pose_similarity || 0;
                    
                    feedbackHTML += `
                        <div style="margin-bottom: 15px; padding: 10px; background: ${index === 0 ? '#f8f9fa' : '#e3f2fd'}; border-radius: 8px;">
                            <strong>${player} (${score} pts)</strong>
                            <br><small>🎯 ${poseScore.toFixed(1)}% accuracy</small>
                            <p style="margin: 5px 0 0 0; font-size: 0.9rem; line-height: 1.4;">${feedback}</p>
                        </div>
                    `;
                }
            });
            
            feedbackHTML += `
                    </div>
                </div>
            `;
        });
        
        // Add performance summary card
        feedbackHTML += `
            <div class="info-card">
                <h4>🏆 Final Results</h4>
                <p><strong>Winner:</strong> ${results.winner}</p>
                <p><strong>Game Mode:</strong> ${results.game_mode === 'rapid' ? 'Rapid (3 rounds)' : 'Normal (5 rounds)'}</p>
                <p><strong>Total Rounds:</strong> ${results.current_rounds_played}/${results.total_rounds}</p>
                <p style="margin-top: 10px; font-style: italic;">🧘♀️ Great practice session! Keep improving your form.</p>
            </div>
        `;
        
        // Add AI analysis summary
        feedbackHTML += `
            <div class="info-card">
                <h4>🤖 AI Analysis Summary</h4>
                <p>Advanced pose detection and similarity analysis provided personalized feedback for each pose.</p>
                <p><strong>ML Status:</strong> ${results.ml_enabled ? '✅ Active' : '⚠️ Fallback'}</p>
                <p style="margin-top: 10px;"><strong>Room:</strong> ${results.room_code}</p>
            </div>
        `;
        
        // Add practice tips
        feedbackHTML += `
            <div class="info-card">
                <h4>🎯 Practice Tips</h4>
                <p>• Focus on proper alignment and form</p>
                <p>• Hold poses steadily for better scores</p>
                <p>• Practice regularly to improve flexibility</p>
                <p>• Use the reference images when needed</p>
            </div>
        `;
        
        infoCardsContainer.innerHTML = feedbackHTML;
        
        console.log('✅ AI feedback displayed successfully in info cards');
        
    } catch (error) {
        console.error('❌ Error displaying AI feedback:', error);
        
        // Fallback: just update existing cards
        updateExistingInfoCards(results);
    }
}

// Update existing info cards with proper content
function updateExistingInfoCards(results) {
    try {
        const infoCards = document.querySelectorAll('.info-card');
        
        if (infoCards.length >= 4) {
            // Update first card - AI Analysis
            infoCards[0].querySelector('h4').textContent = '🤖 AI-Powered Analysis';
            infoCards[0].querySelector('p').textContent = `Advanced pose detection with ${results.ml_enabled ? 'active' : 'fallback'} ML processing`;
            
            // Update second card - Scoring System
            infoCards[1].querySelector('h4').textContent = '📊 Scoring System';
            infoCards[1].querySelector('p').textContent = 'Pose similarity: 50%+ = 1-10 pts, Below 50% = 0 pts';
            
            // Update third card - Speed Bonus
            infoCards[2].querySelector('h4').textContent = '⚡ Speed Bonus';
            infoCards[2].querySelector('p').textContent = 'First correct submissions earn speed bonus points';
            
            // Update fourth card - Results
            infoCards[3].querySelector('h4').textContent = '🎯 Game Results';
            infoCards[3].querySelector('p').textContent = `Winner: ${results.winner} | Mode: ${results.game_mode} | Room: ${results.room_code}`;
        }
        
    } catch (error) {
        console.warn('⚠️ Could not update existing info cards:', error);
    }
}

function storeRoomCode(roomCode) {
    if (roomCode) {
        localStorage.setItem('lastGameRoom', roomCode);
        sessionStorage.setItem('lastGameRoom', roomCode);
    }
}

function handleResultsError(error) {
    console.error('🚨 Results error:', error);
    
    if (error.message && error.message.includes('401')) {
        showError('Session expired. Please sign in again.');
        setTimeout(() => {
            window.location.href = '/signin';
        }, 2000);
    } else if (error.message && error.message.includes('Room not found')) {
        showError('Room has expired or does not exist. Game results may no longer be available.');
    } else if (error.message && error.message.includes('network')) {
        showError('Network error. Please check your connection and try again.');
    } else {
        showError(error.message || 'Failed to load game results. Please try again.');
    }
}

// Navigation functions integrated with base module
function playAgain() {
    console.log('🎮 Starting new game...');
    clearGameState();
    window.location.href = '/multiplayer';
}

function viewDashboard() {
    console.log('📊 Navigating to dashboard...');
    clearGameState();
    window.location.href = '/home';
}

function goToMultiplayerHome() {
    console.log('🏠 Returning to multiplayer home...');
    clearGameState();
    window.location.href = '/multiplayer';
}

// Retry functionality
function retryLoadResults() {
    console.log('🔄 Retrying results load...');
    hideElement('errorState');
    initializeResults();
}

// Share functionality
function shareResults() {
    if (!finalResults) {
        showError('No results to share');
        return;
    }
    
    try {
        const shareText = generateShareText(finalResults);
        
        if (navigator.share) {
            navigator.share({
                title: '🧘♀️ AI Yoga Challenge Results',
                text: shareText
            }).then(() => {
                console.log('Results shared successfully!');
            }).catch((error) => {
                console.log('Share cancelled or failed:', error);
                fallbackCopyShare(shareText);
            });
        } else {
            fallbackCopyShare(shareText);
        }
        
    } catch (error) {
        console.error('❌ Share error:', error);
        showError('Failed to share results: ' + error.message);
    }
}

function generateShareText(results) {
    const winner = results.winner;
    const players = results.players || [];
    const scores = results.scores || {};
    const gameMode = results.game_mode === 'rapid' ? 'Rapid (3 rounds)' : 'Normal (5 rounds)';
    
    let shareText = `🧘♀️ AI Yoga Challenge Results!\n\n`;
    
    if (winner === 'TIE') {
        shareText += `🤝 It's a Tie!\n`;
    } else {
        shareText += `🏆 Winner: ${winner}\n`;
    }
    
    shareText += `\n📊 Final Scores:\n`;
    players.forEach(player => {
        shareText += `• ${player}: ${scores[player] || 0} points\n`;
    });
    
    shareText += `\n🎮 Mode: ${gameMode}\n`;
    shareText += `🤖 AI-Powered Pose Analysis\n`;
    shareText += `🏠 Room: ${results.room_code}\n\n`;
    shareText += `Join us for an AI yoga challenge! 🧘♂️✨`;
    
    return shareText;
}

function fallbackCopyShare(text) {
    copyToClipboard(text).then(() => {
        console.log('Results copied to clipboard! Share with your friends! 📋');
    }).catch(() => {
        showError('Could not copy results. Please copy manually.');
    });
}

// Enhanced error handling with user-friendly messages
function showError(message) {
    console.error('🚨 Error:', message);
    
    const errorMessageEl = document.getElementById('errorMessage');
    if (errorMessageEl) {
        errorMessageEl.textContent = message;
    }
    
    safeHideElement('loadingResults');
    safeHideElement('finalResults');
    safeShowElement('errorState');
}

// Safe DOM manipulation functions
function safeUpdateElement(elementId, content) {
    try {
        const element = document.getElementById(elementId);
        if (element) {
            if (typeof content === 'string' || typeof content === 'number') {
                element.textContent = content;
            } else {
                element.innerHTML = content;
            }
        } else {
            console.warn(`⚠️ Element not found: ${elementId}`);
        }
    } catch (error) {
        console.warn(`⚠️ Failed to update element ${elementId}:`, error);
    }
}

function safeShowElement(elementId) {
    try {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('hidden');
        } else {
            console.warn(`⚠️ Element not found for show: ${elementId}`);
        }
    } catch (error) {
        console.warn(`⚠️ Failed to show element ${elementId}:`, error);
    }
}

function safeHideElement(elementId) {
    try {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
        } else {
            console.warn(`⚠️ Element not found for hide: ${elementId}`);
        }
    } catch (error) {
        console.warn(`⚠️ Failed to hide element ${elementId}:`, error);
    }
}

// Connection status monitoring
function updateConnectionStatus(isConnected) {
    const statusElements = document.querySelectorAll('.connection-status');
    statusElements.forEach(element => {
        if (element) {
            element.textContent = isConnected ? '🟢 Connected' : '🔴 Disconnected';
            element.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
        }
    });
}

// Monitor network status
window.addEventListener('online', () => {
    updateConnectionStatus(true);
    console.log('Connection restored');
    
    // Retry loading if we failed due to network
    const errorState = document.getElementById('errorState');
    if (errorState && !errorState.classList.contains('hidden')) {
        setTimeout(() => {
            retryLoadResults();
        }, 1000);
    }
});

window.addEventListener('offline', () => {
    updateConnectionStatus(false);
    console.error('Connection lost. Results may not load properly.');
});

// Debug helper for development
function debugResults() {
    console.table({
        'Room Code': currentRoomCode,
        'Results Loaded': finalResults !== null,
        'Players': finalResults?.players?.join(', ') || 'None',
        'Winner': finalResults?.winner || 'Unknown',
        'Game Mode': finalResults?.game_mode || 'Unknown',
        'ML Enabled': finalResults?.ml_enabled || false,
        'Has Feedback': finalResults?.round_history ? 'Yes' : 'No'
    });
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (resultsPollInterval) {
        clearInterval(resultsPollInterval);
    }
    
    // Store room code for backup
    if (currentRoomCode) {
        localStorage.setItem('currentRoomCode', currentRoomCode);
        sessionStorage.setItem('currentRoomCode', currentRoomCode);
    }
});

// Make debug function available globally in development
if (typeof window !== 'undefined') {
    window.debugResults = debugResults;
    window.finalResults = finalResults;
}

console.log('✅ Multiplayer Results.js loaded successfully - CORRECTED FOR HTML STRUCTURE');
