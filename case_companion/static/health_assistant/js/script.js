document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing Curo app...');

    try {
        // Navigation: Home to Login/Sign Up (index.html)
        const toLogin = document.getElementById('to-login');
        if (toLogin) {
            console.log('to-login element found');
            toLogin.addEventListener('click', (e) => {
                e.preventDefault(); // Prevent default since we're overriding the href
                console.log('Navigating to login page');
                window.location.href = '/accounts/login/'; // Use Django URL
            });
        }

        // Navigation: Landing to Profile (landing.html)
        const toProfile = document.getElementById('to-profile');
        if (toProfile) {
            console.log('to-profile element found');
            toProfile.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Navigating to profile page');
                window.location.href = '/profile/'; // Use Django URL
            });
        }

        // Navigation: Profile to Landing (profile.html)
        const backToLanding = document.getElementById('back-to-landing');
        if (backToLanding) {
            console.log('back-to-landing element found');
            backToLanding.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Navigating back to landing page');
                window.location.href = '/landing/'; // Use Django URL
            });
        }

        // Navigation: Open Chat (landing.html)
        const openChat = document.getElementById('open-chat');
        if (openChat) {
            console.log('open-chat element found');
            openChat.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Navigating to chat page');
                window.location.href = '/chat/'; // Use Django URL
            });
        }

        // Login/Sign Up Tabs (login.html)
        const loginTab = document.getElementById('login-tab');
        const signupTab = document.getElementById('signup-tab');
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        if (loginTab && signupTab && loginForm && signupForm) {
            console.log('Login/signup tabs and forms found');
            loginTab.addEventListener('click', () => {
                console.log('Switching to login tab');
                loginTab.classList.add('text-indigo-950', 'border-b-2', 'border-indigo-950');
                signupTab.classList.remove('text-indigo-950', 'border-b-2', 'border-indigo-950');
                loginForm.classList.remove('hidden');
                signupForm.classList.add('hidden');
            });
            signupTab.addEventListener('click', () => {
                console.log('Switching to signup tab');
                signupTab.classList.add('text-indigo-950', 'border-b-2', 'border-indigo-950');
                loginTab.classList.remove('text-indigo-950', 'border-b-2', 'border-indigo-950');
                signupForm.classList.remove('hidden');
                loginForm.classList.add('hidden');
            });
        }

        // Profile: Save and Logout (profile.html)
        const saveProfile = document.getElementById('save-profile');
        if (saveProfile) {
            console.log('save-profile element found');
            saveProfile.addEventListener('click', () => {
                console.log('Saving profile changes');
                const email = document.getElementById('profile-email').value;
                const password = document.getElementById('profile-password').value;
                if (email) localStorage.setItem('email', email);
                if (password) localStorage.setItem('password', password);
                alert('Profile updated!');
            });
        }
        const logout = document.getElementById('logout');
        if (logout) {
            console.log('logout element found');
            logout.addEventListener('click', () => {
                console.log('Logging out');
                localStorage.removeItem('username');
                localStorage.removeItem('email');
                window.location.href = '/'; // Redirect to index
            });
        }

        // Initialize profile data (profile.html)
        const profileUsername = document.getElementById('profile-username');
        const profileEmail = document.getElementById('profile-email');
        if (profileUsername && profileEmail) {
            console.log('Profile elements found');
            profileUsername.textContent = localStorage.getItem('username') || 'username';
            profileEmail.value = localStorage.getItem('email') || 'user@example.com';
        }
    } catch (error) {
        console.error('Error initializing app:', error);
    }
});