// dashboard.js - FIXED VERSION using old strategy
console.log('🏠 Dashboard script loaded');

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Initializing dashboard...');
    await loadUserInfo();
    await loadBrainScore();
    await loadGamesPlayed(); // NEW: Load games played
    initializeProfileDropdown();
});

// FIXED: Use old working strategy for user loading
async function loadUserInfo() {
    try {
        console.log('👤 Loading user info...');
        const user = await getCurrentUser();
        if (user) {
            // FIXED: Use full_name first, then fallback to username
            const displayName = user.full_name || user.username;
            console.log('✅ Display name:', displayName);
            
            // Update all user name elements
            document.querySelectorAll('#userName, #profileName').forEach(element => {
                if (element) {
                    element.textContent = displayName;
                    console.log('✅ Updated element:', element.id);
                }
            });
            
            // Update user initial in avatar
            const initialElement = document.getElementById('userInitial');
            if (initialElement) {
                initialElement.textContent = displayName.charAt(0).toUpperCase();
                console.log('✅ Updated initial:', displayName.charAt(0).toUpperCase());
            }
            
            // FIXED: Update welcome message in h1
            const welcomeH1 = document.querySelector('section.dashboard-hero h1');
            if (welcomeH1) {
                welcomeH1.textContent = `Welcome back, ${displayName}!`;
                console.log('✅ Updated welcome message');
            }
        }
    } catch (error) {
        console.error('❌ Failed to load user info:', error);
        // Don't redirect immediately, let other loading continue
        setTimeout(() => {
            window.location.href = '/signin';
        }, 2000);
    }
}

// FIXED: Use old working strategy for getCurrentUser
async function getCurrentUser() {
    try {
        console.log('📡 Fetching current user...');
        const response = await fetch('/api/current-user', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ User data received:', data);
            
            // FIXED: Handle the nested user structure from your API
            if (data.user) {
                return data.user; // Return the nested user object
            } else {
                return data; // Fallback if data is already the user object
            }
        } else {
            console.error('❌ Failed to get user:', response.status);
            return null;
        }
    } catch (error) {
        console.error('❌ Error getting current user:', error);
        return null;
    }
}

// FIXED: Load brain score using old strategy
async function loadBrainScore() {
    try {
        console.log('🧠 Loading brain score...');
        const response = await fetch('/api/user/brain_score', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Brain score data:', data);
            
            const brainScoreElem = document.getElementById('brainScore');
            if (brainScoreElem && data.brain_score !== undefined) {
                brainScoreElem.textContent = data.brain_score;
                console.log('✅ Updated brain score:', data.brain_score);
                
                // Update knowledge level based on brain score
                updateKnowledgeLevel(data.brain_score);
            }
        }
    } catch (error) {
        console.error('❌ Failed to load brain score:', error);
    }
}

// NEW: Load games played using same strategy
async function loadGamesPlayed() {
    try {
        console.log('🎮 Loading games played...');
        const response = await fetch('/api/user/games_played', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Games played data:', data);
            
            // Update first stat card (games played)
            const statCards = document.querySelectorAll('.stat-card');
            if (statCards.length > 0) {
                const gamesCard = statCards[0]; // First card is games played
                const h3 = gamesCard.querySelector('h3');
                if (h3) {
                    h3.textContent = data.games_played || 0;
                    console.log('✅ Updated games played:', data.games_played);
                }
            }
        }
    } catch (error) {
        console.error('❌ Failed to load games played:', error);
    }
}

// Update knowledge level based on brain score
function updateKnowledgeLevel(brainScore) {
    let level = 'Beginner';
    
    if (brainScore >= 90) {
        level = 'Advanced';
    } else if (brainScore >= 70) {
        level = 'Intermediate';
    } else if (brainScore >= 50) {
        level = 'Beginner+';
    }
    
    // Update third stat card (knowledge level)
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length > 2) {
        const knowledgeCard = statCards[2]; // Third card is knowledge level
        const h3 = knowledgeCard.querySelector('h3');
        if (h3) {
            h3.textContent = level;
            console.log('✅ Updated knowledge level:', level);
        }
    }
}

// Initialize profile dropdown
function initializeProfileDropdown() {
    const profileBtn = document.getElementById('profileBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');
    
    if (profileBtn && dropdownMenu) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileBtn.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
        
        console.log('✅ Profile dropdown initialized');
    } else {
        console.warn('⚠️ Profile dropdown elements not found');
    }
}

// Navigation functions
function navigateToMultiplayer() {
    window.location.href = '/multiplayer';
}

function navigateToGame() {
    window.location.href = '/game';
}

function navigateToQuiz() {
    window.location.href = '/quiz';
}

function navigateToAI() {
    window.location.href = '/aianalyzer';
}

// Make functions available globally
window.loadBrainScore = loadBrainScore;
window.navigateToMultiplayer = navigateToMultiplayer;
window.navigateToGame = navigateToGame;
window.navigateToQuiz = navigateToQuiz;
window.navigateToAI = navigateToAI;

console.log('✅ Dashboard script ready');
