/**
 * Wagtail Messages Utility
 * Creates messages using Wagtail's native message system styling
 */

/**
 * Show a message using Wagtail's message system
 * @param {string} message - The message text to display
 * @param {string} type - Message type: 'success', 'error', 'warning', 'info'
 * @param {HTMLElement} container - Optional container element (defaults to #message-container)
 */
function showWagtailMessage(message, type = 'info', container = null) {
    // Get or create message container
    if (!container) {
        container = document.getElementById('message-container');
    }
    
    if (!container) {
        console.error('Message container not found');
        return;
    }
    
    // Map type to icon name
    const iconMap = {
        'success': 'success',
        'error': 'warning',
        'warning': 'warning',
        'info': 'help'
    };
    
    const iconName = iconMap[type] || 'help';
    
    // Create Wagtail-style message structure
    const messagesHtml = `
        <div class="messages" role="status">
            <ul>
                <li class="${type}">
                    <svg class="icon icon-${iconName} messages-icon" aria-hidden="true">
                        <use href="#icon-${iconName}"></use>
                    </svg>
                    ${message}
                </li>
            </ul>
        </div>
    `;
    
    // Clear previous messages and add new one
    container.innerHTML = messagesHtml;
    
    // Auto-dismiss success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            const messagesDiv = container.querySelector('.messages');
            if (messagesDiv) {
                messagesDiv.style.opacity = '0';
                messagesDiv.style.transition = 'opacity 0.3s';
                setTimeout(() => {
                    container.innerHTML = '';
                }, 300);
            }
        }, 5000);
    }
}

/**
 * Clear all messages from container
 * @param {HTMLElement} container - Optional container element
 */
function clearWagtailMessages(container = null) {
    if (!container) {
        container = document.getElementById('message-container');
    }
    
    if (container) {
        container.innerHTML = '';
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showWagtailMessage,
        clearWagtailMessages
    };
}

