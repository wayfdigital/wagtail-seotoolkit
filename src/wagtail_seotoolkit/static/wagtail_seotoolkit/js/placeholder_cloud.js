/**
 * Reusable Placeholder Cloud Utilities
 * Shared code for handling placeholder insertion and dynamic loading
 */

/**
 * Insert placeholder at cursor position in textarea
 * @param {HTMLTextAreaElement} textarea - The textarea element
 * @param {string} placeholder - The placeholder name (without braces)
 * @param {number|null} truncateLength - Optional truncation length
 */
function insertPlaceholderAtCursor(textarea, placeholder, truncateLength = null) {
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const before = text.substring(0, start);
    const after = text.substring(end, text.length);

    // Insert placeholder with braces and optional truncation
    let placeholderText;
    if (truncateLength && truncateLength > 0) {
        placeholderText = `{${placeholder}[:${truncateLength}]}`;
    } else {
        placeholderText = `{${placeholder}}`;
    }

    textarea.value = before + placeholderText + after;

    // Move cursor to after the inserted placeholder
    const newCursorPos = start + placeholderText.length;
    textarea.selectionStart = newCursorPos;
    textarea.selectionEnd = newCursorPos;

    // Focus back on textarea
    textarea.focus();

    // Trigger input event for any listeners
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
}

/**
 * Render placeholder badges into a container
 * @param {HTMLElement} container - Container element for badges
 * @param {Array} placeholders - Array of placeholder objects
 */
function renderPlaceholderBadges(container, placeholders) {
    if (!container) return;

    container.innerHTML = '';

    placeholders.forEach(placeholder => {
        // Create wrapper for badge and truncate button
        const wrapper = document.createElement('span');
        wrapper.className = `placeholder-badge-wrapper placeholder-badge--${placeholder.type}`;

        // Create the main badge button
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'placeholder-badge-main';
        button.dataset.placeholder = placeholder.name;
        button.title = `Click to insert {${placeholder.name}}`;
        button.textContent = placeholder.label;

        // Create truncate icon button
        const truncateBtn = document.createElement('button');
        truncateBtn.type = 'button';
        truncateBtn.className = 'placeholder-truncate-btn';
        truncateBtn.dataset.placeholder = placeholder.name;
        truncateBtn.title = 'Insert with truncation';
        truncateBtn.textContent = '[:N]';

        wrapper.appendChild(button);
        wrapper.appendChild(truncateBtn);
        container.appendChild(wrapper);
    });
}

/**
 * Fetch placeholders for a content type
 * @param {number|null} contentTypeId - Content type ID or null for universal
 * @returns {Promise<Array>} Promise resolving to placeholders array
 */
async function fetchPlaceholders(contentTypeId) {
    const url = `/admin/api/get-placeholders/${contentTypeId ? `?content_type_id=${contentTypeId}` : ''}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            return data.placeholders;
        } else {
            console.error('Failed to fetch placeholders:', data.error);
            return [];
        }
    } catch (error) {
        console.error('Error fetching placeholders:', error);
        return [];
    }
}

/**
 * Show truncation dialog and return the length
 * @param {string} placeholderName - The placeholder name for display
 * @returns {number|null} The truncation length or null if cancelled
 */
function promptForTruncation(placeholderName) {
    const length = prompt(
        `Truncate "${placeholderName}" to how many characters?\n\n`
    );

    if (length === null) {
        return null; // User cancelled
    }

    const parsedLength = parseInt(length, 10);

    if (isNaN(parsedLength) || parsedLength <= 0) {
        alert('Please enter a valid positive number');
        return null;
    }

    return parsedLength;
}

/**
 * Set up placeholder cloud with click handling
 * @param {HTMLElement} cloudContainer - Container with placeholder badges
 * @param {HTMLTextAreaElement} targetTextarea - Textarea to insert into
 * @returns {Function} The click handler function (for potential cleanup)
 */
function setupPlaceholderCloud(cloudContainer, targetTextarea) {
    if (!cloudContainer || !targetTextarea) return null;

    // Check if already set up to prevent duplicate listeners
    if (cloudContainer.dataset.placeholderCloudInitialized === 'true') {
        return null;
    }

    // Create click handler function
    const clickHandler = function(e) {
        // Handle truncate button clicks
        const truncateBtn = e.target.closest('.placeholder-truncate-btn');
        if (truncateBtn) {
            e.stopPropagation(); // Prevent badge click from firing
            const placeholder = truncateBtn.dataset.placeholder;
            if (placeholder) {
                const truncateLength = promptForTruncation(placeholder);
                if (truncateLength !== null) {
                    insertPlaceholderAtCursor(targetTextarea, placeholder, truncateLength);
                }
            }
            return;
        }

        // Handle regular badge clicks
        const badge = e.target.closest('.placeholder-badge-main');
        if (badge) {
            const placeholder = badge.dataset.placeholder;
            if (placeholder) {
                insertPlaceholderAtCursor(targetTextarea, placeholder);
            }
        }
    };

    // Use event delegation for badge clicks
    cloudContainer.addEventListener('click', clickHandler);
    
    // Mark as initialized to prevent duplicate setup
    cloudContainer.dataset.placeholderCloudInitialized = 'true';
    
    return clickHandler;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        insertPlaceholderAtCursor,
        renderPlaceholderBadges,
        fetchPlaceholders,
        promptForTruncation,
        setupPlaceholderCloud
    };
}

