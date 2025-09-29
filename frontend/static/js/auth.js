// Authentication functionality
document.addEventListener('DOMContentLoaded', function() {
    const signinForm = document.getElementById('signinForm');
    const signupForm = document.getElementById('signupForm');
    
    if (signinForm) {
        signinForm.addEventListener('submit', handleSignin);
    }
    
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

function handleSignin(event) {
    const button = event.target.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Signing in...';
    
    // Form will submit normally, but we provide feedback
    setTimeout(() => {
        button.disabled = false;
        button.textContent = 'Sign In';
    }, 2000);
}

function handleSignup(event) {
    const button = event.target.querySelector('button[type="submit"]');
    const password = event.target.querySelector('#password').value;
    
    // Basic password validation
    if (password.length < 6) {
        event.preventDefault();
        showMessage('Password must be at least 6 characters long', 'error');
        return;
    }
    
    button.disabled = true;
    button.textContent = 'Creating account...';
    
    setTimeout(() => {
        button.disabled = false;
        button.textContent = 'Create Account';
    }, 2000);
}
