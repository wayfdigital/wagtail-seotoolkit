/**
 * Subscription Status Module
 * 
 * Centralized subscription checking logic that can be reused across all pages.
 * Provides utilities for checking subscription status and determining access levels.
 */

(function(window) {
    'use strict';

    const API_BASE_URL = '/admin/api/proxy';

    /**
     * Get CSRF token from Django
     */
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));

        if (cookieValue) {
            return cookieValue.split('=')[1];
        }

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        return null;
    }

    /**
     * Get email and instance ID from backend
     * 
     * @returns {Promise<{email: string, instanceId: string}>}
     */
    async function getEmailAndInstanceId() {
        try {
            const response = await fetch('/admin/api/email-verification/get/', {
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.success && data.email && data.instance_id) {
                return {
                    email: data.email,
                    instanceId: data.instance_id
                };
            }
            
            return null;
        } catch (error) {
            console.error('Error getting email and instance ID:', error);
            return null;
        }
    }

    /**
     * Check if subscription is active and instance is registered
     * 
     * @param {string} email - User's email address
     * @param {string} instanceId - Current instance ID
     * @returns {Promise<{isActive: boolean, isPro: boolean, isRegistered: boolean, data: object}>}
     */
    async function checkSubscription(email, instanceId) {
        if (!email || !instanceId) {
            return {
                isActive: false,
                isPro: false,
                isRegistered: false,
                data: null
            };
        }

        try {
            const response = await fetch(
                `${API_BASE_URL}/check-subscription/?email=${encodeURIComponent(email)}&instanceId=${encodeURIComponent(instanceId)}`,
                {
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                }
            );

            const data = await response.json();

            // Check if subscription is active
            // A subscription is considered active if:
            // 1. pro === true (has a pro subscription)
            // 2. status === 'active' (subscription is not cancelled/past due)
            // 3. instanceId matches current instance (instance is registered)
            const isPro = data.pro === true;
            const isActiveStatus = data.status === 'active';
            const isRegistered = data.instanceId === instanceId;
            const isActive = isPro && isActiveStatus && isRegistered;

            return {
                isActive: isActive,
                isPro: isPro,
                isRegistered: isRegistered,
                data: data
            };

        } catch (error) {
            console.error('Error checking subscription:', error);
            return {
                isActive: false,
                isPro: false,
                isRegistered: false,
                data: null,
                error: error
            };
        }
    }

    /**
     * Check subscription with automatic email/instance fetching
     * 
     * @returns {Promise<{isActive: boolean, isPro: boolean, isRegistered: boolean, data: object, email: string, instanceId: string}>}
     */
    async function checkSubscriptionAuto() {
        const credentials = await getEmailAndInstanceId();
        
        if (!credentials) {
            return {
                isActive: false,
                isPro: false,
                isRegistered: false,
                data: null,
                email: null,
                instanceId: null
            };
        }

        const result = await checkSubscription(credentials.email, credentials.instanceId);
        
        return {
            ...result,
            email: credentials.email,
            instanceId: credentials.instanceId
        };
    }

    /**
     * Get badge HTML for displaying subscription status
     * 
     * @param {object} subscriptionResult - Result from checkSubscriptionAuto()
     * @param {object} options - Display options
     * @returns {string} HTML string for badge
     */
    function getBadgeHTML(subscriptionResult, options = {}) {
        const {
            showManageLink = true,
            inline = true,
            style = 'default'
        } = options;

        const { isActive, isPro, isRegistered, data } = subscriptionResult;

        let badgeClass = 'subscription-badge';
        let badgeStyle = '';
        let badgeText = '';
        let icon = '';

        if (isActive) {
            // Active subscription
            const planTier = (data && data.planTier) ? data.planTier.toUpperCase() : 'PRO';
            icon = '✓';
            badgeText = `${planTier} Active`;
            badgeStyle = 'background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white;';
        } else if (isPro && !isRegistered) {
            // Has subscription but not registered
            icon = '⚠️';
            badgeText = 'Not Registered';
            badgeStyle = 'background: #fbbf24; color: white;';
        } else {
            // No subscription
            icon = '';
            badgeText = 'Free Plan';
            badgeStyle = 'background: #e5e7eb; color: #374151;';
        }

        const displayStyle = inline ? 'inline-flex' : 'flex';
        const manageLink = showManageLink ? 
            `<a href="/admin/settings/subscription-settings/" style="color: ${isActive ? 'white' : '#667eea'}; text-decoration: none; font-weight: 600;">Manage →</a>` : 
            '';

        return `
            <div style="display: ${displayStyle}; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9rem; ${badgeStyle}">
                <span><strong>${icon} ${badgeText}</strong></span>
                ${manageLink}
            </div>
        `;
    }

    /**
     * Display subscription badge in a container
     * 
     * @param {string} containerId - ID of container element
     * @param {object} options - Display options
     */
    async function displayBadge(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        // Show loading state
        container.innerHTML = `
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: #f3f4f6; border-radius: 6px; font-size: 0.9rem;">
                <span>⏳ Checking subscription...</span>
            </div>
        `;

        try {
            const result = await checkSubscriptionAuto();
            container.innerHTML = getBadgeHTML(result, options);
        } catch (error) {
            console.error('Error displaying badge:', error);
            container.innerHTML = `
                <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: #fee2e2; color: #991b1b; border-radius: 6px; font-size: 0.9rem;">
                    <span>⚠️ Error checking status</span>
                </div>
            `;
        }
    }

    /**
     * Clear subscription cache (force fresh check on next request)
     * 
     * @param {string} email - User's email address
     * @param {string} instanceId - Instance ID
     */
    async function clearCache(email, instanceId) {
        // The cache is server-side, so we just make a request that will clear it
        // For now, this is a placeholder - implement if needed
        console.log('Cache clearing not yet implemented client-side');
    }

    // Export public API
    window.SubscriptionStatus = {
        getCSRFToken: getCSRFToken,
        getEmailAndInstanceId: getEmailAndInstanceId,
        checkSubscription: checkSubscription,
        checkSubscriptionAuto: checkSubscriptionAuto,
        getBadgeHTML: getBadgeHTML,
        displayBadge: displayBadge,
        clearCache: clearCache,
        API_BASE_URL: API_BASE_URL
    };

})(window);


