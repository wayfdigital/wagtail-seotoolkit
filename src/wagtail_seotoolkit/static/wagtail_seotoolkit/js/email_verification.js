/**
 * Email Verification Gate
 * 
 * Locks SEO Toolkit features behind email verification.
 * Integrates with external verification API.
 */

(function() {
    'use strict';

    // Use Django proxy endpoints to avoid CORS issues
    const PROXY_BASE_URL = '/admin/api/proxy';
    const POLL_INTERVAL = 30000; // 30 seconds
    
    let pollTimeout = null;
    let currentEmail = null;

    /**
     * Get CSRF token from Django
     * Tries to get from cookie first, then from DOM
     */
    function getCSRFToken() {
        // Try to get from cookie first
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));

        if (cookieValue) {
            return cookieValue.split('=')[1];
        }

        // Fallback: try to get from DOM (input or meta tag)
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.content;
        }

        return null;
    }

    /**
     * Fetch stored email from Django backend
     */
    async function getStoredEmail() {
        try {
            const response = await fetch('/admin/api/email-verification/get/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success && data.email) {
                return data.email;
            }
            return null;
        } catch (error) {
            console.error('Failed to fetch stored email:', error);
            return null;
        }
    }

    /**
     * Save email to Django backend
     * Verification status is not stored locally - always checked via external API
     */
    async function saveEmail(email) {
        try {
            const response = await fetch('/admin/api/email-verification/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Failed to save email:', error);
            return false;
        }
    }

    /**
     * Check if email is verified via Django proxy
     */
    async function checkVerificationStatus(email) {
        try {
            const response = await fetch(`${PROXY_BASE_URL}/check-verified/?email=${encodeURIComponent(email)}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to check verification status:', error);
            return { verified: false, pending: false };
        }
    }

    /**
     * Send verification email via Django proxy
     */
    async function sendVerificationEmail(email) {
        try {
            const response = await fetch(`${PROXY_BASE_URL}/send-verification/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to send verification email:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * Resend verification email via Django proxy
     */
    async function resendVerificationEmail(email) {
        try {
            const response = await fetch(`${PROXY_BASE_URL}/resend-verification/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to resend verification email:', error);
            return { success: false, message: error.message };
        }
    }

    /**
     * Check if we're in a sidepanel context
     */
    function isSidepanel() {
        // Check if we're in the sidepanel by looking for sidepanel-specific classes/elements
        const gateContainer = document.getElementById('verification-gate');
        return gateContainer && gateContainer.closest('.w-side-panel, .seo-sidepanel');
    }

    /**
     * Show verification button for sidepanel
     */
    function showSidepanelButton() {
        const gateContainer = document.getElementById('verification-gate');
        if (!gateContainer) return;

        gateContainer.innerHTML = `
            <div class="email-verification-sidepanel">
                <svg class="email-verification-sidepanel__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <h3 class="email-verification-sidepanel__title">Verification Required</h3>
                <p class="email-verification-sidepanel__text">
                    Please verify your email to access SEO insights.
                </p>
                <a href="/admin/seo-dashboard/" class="email-verification-sidepanel__button">
                    Go to Dashboard to Verify
                </a>
            </div>
        `;
    }

    /**
     * Show verification form
     */
    function showVerificationForm() {
        const gateContainer = document.getElementById('verification-gate');
        if (!gateContainer) return;

        // If in sidepanel, show button instead
        if (isSidepanel()) {
            showSidepanelButton();
            return;
        }

        gateContainer.innerHTML = `
            <div class="email-verification-overlay">
                <div class="email-verification-card">
                    <div class="email-verification-header">
                        <svg class="email-verification-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <h2 class="email-verification-title">Activate Wagtail SEO Toolkit</h2>
                        <p class="email-verification-subtitle">
                            Free forever. Takes 10 seconds.
                        </p>
                    </div>
                    
                    <form id="verification-form" class="email-verification-form">
                        <div class="email-verification-input-group">
                            <label for="verification-email" class="email-verification-label">
                                Email Address
                            </label>
                            <input 
                                type="email" 
                                id="verification-email" 
                                class="email-verification-input"
                                placeholder="your@email.com"
                                required
                            />
                        </div>
                        
                        <div class="email-verification-benefits">
                            <p class="email-verification-benefits-title">We'll send you:</p>
                            <ul class="email-verification-benefits-list">
                                <li>• Update notifications</li>
                                <li>• Feature announcements</li>
                                <li>• Early access to Pro features</li>
                            </ul>
                        </div>
                        
                        <button type="submit" class="email-verification-button">
                            Send Verification Email
                        </button>
                        
                        <div id="verification-message" class="email-verification-message"></div>
                        
                        <p class="email-verification-privacy">
                            <a href="https://wagtail-seotoolkit-license-server.vercel.app/privacy-policy.html" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
                        </p>
                    </form>
                </div>
            </div>
        `;

        // Attach form handler
        const form = document.getElementById('verification-form');
        form.addEventListener('submit', handleVerificationSubmit);
    }

    /**
     * Show waiting for verification state
     */
    function showWaitingState(email) {
        const gateContainer = document.getElementById('verification-gate');
        if (!gateContainer) return;

        // If in sidepanel, just show button
        if (isSidepanel()) {
            showSidepanelButton();
            return;
        }

        gateContainer.innerHTML = `
            <div class="email-verification-overlay">
                <div class="email-verification-card">
                    <div class="email-verification-header">
                        <svg class="email-verification-icon email-verification-icon--pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <h2 class="email-verification-title">Waiting for Verification</h2>
                        <p class="email-verification-subtitle">
                            We've sent a verification link to <strong>${email}</strong>
                        </p>
                    </div>
                    
                    <div class="email-verification-waiting">
                        <div class="email-verification-spinner"></div>
                        <p class="email-verification-text">
                            Please check your inbox and click the verification link.
                            <br>
                            We'll check your status automatically every 30 seconds.
                        </p>
                        
                        <button id="resend-verification" class="email-verification-button-secondary">
                            Resend Verification Email
                        </button>
                        
                        <button id="change-email" class="email-verification-link">
                            Use a different email
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Attach handlers
        document.getElementById('resend-verification')?.addEventListener('click', () => {
            handleResendVerification(email);
        });
        
        document.getElementById('change-email')?.addEventListener('click', () => {
            stopPolling();
            showVerificationForm();
        });

        // Start polling
        startPolling(email);
    }

    /**
     * Show verified state and unlock content
     */
    function showVerifiedState() {
        const gateContainer = document.getElementById('verification-gate');
        const protectedContent = document.getElementById('protected-content');
        
        if (gateContainer) {
            gateContainer.style.display = 'none';
        }
        
        if (protectedContent) {
            protectedContent.style.display = 'block';
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        const messageEl = document.getElementById('verification-message');
        if (messageEl) {
            messageEl.innerHTML = `
                <div class="email-verification-error">
                    <svg class="email-verification-error-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                    ${message}
                </div>
            `;
        }
    }

    /**
     * Handle verification form submission
     */
    async function handleVerificationSubmit(e) {
        e.preventDefault();
        
        const emailInput = document.getElementById('verification-email');
        const email = emailInput.value.trim();
        
        if (!email) {
            showError('Please enter a valid email address');
            return;
        }

        // Disable form
        const submitButton = e.target.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.textContent = 'Checking...';

        // First, check if email is already verified
        const status = await checkVerificationStatus(email);
        
        if (status.verified) {
            // Email is already verified, save and show verified state
            await saveEmail(email);
            currentEmail = email;
            showVerifiedState();
            return;
        }

        // If not verified, proceed to send verification email
        submitButton.textContent = 'Sending...';
        const result = await sendVerificationEmail(email);
        
        if (result.success) {
            // Save email to backend
            await saveEmail(email);
            currentEmail = email;
            
            // Show waiting state
            showWaitingState(email);
        } else {
            showError(result.message || 'Failed to send verification email. Please try again.');
            submitButton.disabled = false;
            submitButton.textContent = 'Send Verification Email';
        }
    }

    /**
     * Handle resend verification
     */
    async function handleResendVerification(email) {
        const button = document.getElementById('resend-verification');
        if (!button) return;

        button.disabled = true;
        button.textContent = 'Sending...';

        const result = await resendVerificationEmail(email);
        
        if (result.success) {
            button.textContent = 'Email Sent!';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Resend Verification Email';
            }, 3000);
        } else {
            button.textContent = 'Failed to Resend';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Resend Verification Email';
            }, 3000);
        }
    }

    /**
     * Start polling for verification status
     * Checks external API - does not store verification status locally
     */
    function startPolling(email) {
        stopPolling(); // Clear any existing polling
        
        async function poll() {
            const status = await checkVerificationStatus(email);
            
            if (status.verified) {
                // Verification confirmed via external API
                stopPolling();
                showVerifiedState();
            } else {
                // Continue polling
                pollTimeout = setTimeout(poll, POLL_INTERVAL);
            }
        }
        
        // Start first poll after interval
        pollTimeout = setTimeout(poll, POLL_INTERVAL);
    }

    /**
     * Stop polling
     */
    function stopPolling() {
        if (pollTimeout) {
            clearTimeout(pollTimeout);
            pollTimeout = null;
        }
    }

    /**
     * Initialize verification check
     */
    async function initializeVerification() {
        // If in sidepanel, simplify the logic
        if (isSidepanel()) {
            const storedEmail = await getStoredEmail();
            
            if (storedEmail) {
                const status = await checkVerificationStatus(storedEmail);
                
                if (status.verified) {
                    // Email is verified, show content
                    showVerifiedState();
                } else {
                    // Not verified, show button
                    showSidepanelButton();
                }
            } else {
                // No stored email, show button
                showSidepanelButton();
            }
            return;
        }

        // Full verification flow for dashboard/reports
        const storedEmail = await getStoredEmail();
        
        if (storedEmail) {
            currentEmail = storedEmail;
            
            // Check verification status
            const status = await checkVerificationStatus(storedEmail);
            
            if (status.verified) {
                // Email is verified, show content
                showVerifiedState();
            } else if (status.pending) {
                // Verification is pending, show waiting state
                showWaitingState(storedEmail);
            } else {
                // Not verified and not pending, show form
                showVerificationForm();
            }
        } else {
            // No stored email, show form
            showVerificationForm();
        }
    }

    /**
     * Initialize on page load
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeVerification);
    } else {
        initializeVerification();
    }

    /**
     * Cleanup on page unload
     */
    window.addEventListener('beforeunload', stopPolling);

})();

