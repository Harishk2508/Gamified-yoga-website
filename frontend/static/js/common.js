// Common utilities and functions
function showMessage(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
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
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
    });
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function apiCall(endpoint, options = {}) {
    return fetch(endpoint, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    });
}

async function getCurrentUser() {
    try {
        const response = await apiCall('/api/current-user');
        return response.user;
    } catch (error) {
        return null;
    }
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('🧘‍♂️ Harish Yoga Platform loaded');
});
