/**
 * Dashboard Message Module
 * Fetches and displays messages from the external API
 */

(function() {
    'use strict';

    /**
     * Fetches dashboard message from the proxy endpoint
     */
    async function fetchDashboardMessage() {
        try {
            const response = await fetch('/admin/api/proxy/get-dashboard-message/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                console.error('Failed to fetch dashboard message:', response.statusText);
                return null;
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching dashboard message:', error);
            return null;
        }
    }

    /**
     * Displays the dashboard message in a styled box
     */
    function displayMessage(message) {
        const container = document.getElementById('dashboard-message-container');
        if (!container) return;

        container.innerHTML = `
            <div class="dashboard-message-box">
                <div class="dashboard-message-icon">
                    <svg class="icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="dashboard-message-content">
                    ${message}
                </div>
            </div>
        `;
        container.style.display = 'block';
    }

    /**
     * Initializes the dashboard message fetching
     */
    async function init() {
        const data = await fetchDashboardMessage();
        
        if (data && data.success && data.hasMessage && data.message) {
            displayMessage(data.message);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

