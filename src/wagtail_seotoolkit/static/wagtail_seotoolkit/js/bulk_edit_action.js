/**
 * Bulk Edit Action - Form Handler
 * 
 * Handles the bulk edit form submission via AJAX and character counting.
 */

(function() {
    'use strict';

    // Configuration
    const SELECTORS = {
        form: '#bulk-edit-form',
        textarea: '#id_content',
        charCount: '#char-count',
        messageContainer: '#message-container',
        submitButton: 'button[type="submit"]',
        previewTable: '#preview-table'
    };

    // State
    let isInitialized = false;
    let previewDebounceTimer = null;
    const PREVIEW_DEBOUNCE_MS = 500;

    /**
     * Update character count display
     */
    function updateCharCount() {
        const textarea = document.querySelector(SELECTORS.textarea);
        const charCount = document.querySelector(SELECTORS.charCount);
        
        if (!textarea || !charCount) return;
        
        charCount.textContent = textarea.value.length;
    }

    /**
     * Show success message
     */
    function showSuccessMessage(message, redirectUrl) {
        const messageContainer = document.querySelector(SELECTORS.messageContainer);
        if (!messageContainer) return;

        messageContainer.innerHTML = `
            <div class="help-block help-info">
                <p>${message}</p>
            </div>
        `;

        // Redirect after short delay
        if (redirectUrl) {
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 1500);
        }
    }

    /**
     * Show error message
     */
    function showErrorMessage(message) {
        const messageContainer = document.querySelector(SELECTORS.messageContainer);
        if (!messageContainer) return;

        messageContainer.innerHTML = `
            <div class="help-block help-critical">
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Get CSRF token from form
     */
    function getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        // Fallback: try to get from cookie
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));

        if (cookieValue) {
            return cookieValue.split('=')[1];
        }

        return null;
    }

    /**
     * Handle form submission
     */
    async function handleFormSubmit(e) {
        e.preventDefault();

        const form = e.target;
        const submitBtn = form.querySelector(SELECTORS.submitButton);
        const messageContainer = document.querySelector(SELECTORS.messageContainer);
        
        // Use getAttribute to avoid name collision with <input name="action">
        const actionUrl = form.getAttribute('action');

        if (!submitBtn) {
            return;
        }

        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.classList.add('button-longrunning-active');
        
        // Clear previous messages
        if (messageContainer) {
            messageContainer.innerHTML = '';
        }

        try {
            const formData = new FormData(form);
            
            const response = await fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                // Get the redirect URL from the form's data attribute or use default
                const redirectUrl = form.dataset.redirectUrl || '/admin/reports/bulk-edit/';
                showSuccessMessage(data.message, redirectUrl);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Bulk edit error:', error);
            showErrorMessage(`Error: ${error.message}`);
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.classList.remove('button-longrunning-active');
        }
    }

    /**
     * Update preview table with processed values
     */
    async function updatePreview() {
        const textarea = document.querySelector(SELECTORS.textarea);
        const form = document.querySelector(SELECTORS.form);
        const previewTable = document.querySelector(SELECTORS.previewTable);
        
        if (!textarea || !form || !previewTable) return;

        const template = textarea.value.trim();
        
        // If empty, show placeholder text
        if (!template) {
            const rows = previewTable.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const newValueCell = row.querySelector('.new-value');
                if (newValueCell) {
                    newValueCell.innerHTML = '<span class="preview-placeholder muted">Enter template above...</span>';
                }
            });
            return;
        }

        try {
            const formData = new FormData(form);
            formData.set('template', template);
            
            const response = await fetch('/admin/api/preview-metadata/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success && data.previews) {
                // Update each row with preview data
                data.previews.forEach(preview => {
                    const row = previewTable.querySelector(`tr[data-page-id="${preview.page_id}"]`);
                    if (row) {
                        const newValueCell = row.querySelector('.new-value');
                        if (newValueCell) {
                            newValueCell.textContent = preview.new_value;
                            newValueCell.classList.remove('muted');
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Preview update error:', error);
        }
    }

    /**
     * Debounced preview update
     */
    function debouncedUpdatePreview() {
        // Clear existing timer
        if (previewDebounceTimer) {
            clearTimeout(previewDebounceTimer);
        }
        
        // Set new timer
        previewDebounceTimer = setTimeout(updatePreview, PREVIEW_DEBOUNCE_MS);
    }

    /**
     * Insert placeholder at cursor position in textarea
     */
    function insertPlaceholder(placeholder) {
        const textarea = document.querySelector(SELECTORS.textarea);
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const before = text.substring(0, start);
        const after = text.substring(end, text.length);

        // Insert placeholder with braces
        const placeholderText = `{${placeholder}}`;
        textarea.value = before + placeholderText + after;

        // Move cursor to after the inserted placeholder
        const newCursorPos = start + placeholderText.length;
        textarea.selectionStart = newCursorPos;
        textarea.selectionEnd = newCursorPos;

        // Focus back on textarea
        textarea.focus();

        // Trigger input event for any listeners (like character count and preview)
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    /**
     * Handle placeholder badge click
     */
    function handlePlaceholderClick(e) {
        if (e.target.classList.contains('placeholder-badge')) {
            const placeholder = e.target.dataset.placeholder;
            if (placeholder) {
                insertPlaceholder(placeholder);
            }
        }
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        const form = document.querySelector(SELECTORS.form);
        const textarea = document.querySelector(SELECTORS.textarea);
        const placeholderCloud = document.querySelector('.placeholder-cloud');

        if (!form) {
            return false;
        }

        // Character count and preview update on input
        if (textarea) {
            textarea.addEventListener('input', function() {
                updateCharCount();
                debouncedUpdatePreview();
            });
            updateCharCount(); // Initial count
        }

        // Placeholder badge clicks (using event delegation)
        if (placeholderCloud) {
            placeholderCloud.addEventListener('click', handlePlaceholderClick);
        }

        // Form submission
        form.addEventListener('submit', handleFormSubmit);

        return true;
    }

    /**
     * Remove event listeners
     */
    function removeEventListeners() {
        const form = document.querySelector(SELECTORS.form);
        const textarea = document.querySelector(SELECTORS.textarea);

        if (form) {
            form.removeEventListener('submit', handleFormSubmit);
        }

        if (textarea) {
            textarea.removeEventListener('input', updateCharCount);
        }
    }

    /**
     * Initialize bulk edit action form
     */
    function initialize() {
        // Prevent multiple initializations
        if (isInitialized) {
            return;
        }

        const form = document.querySelector(SELECTORS.form);
        if (!form) {
            // Form not found, might not be on bulk edit action page
            return;
        }

        // Attach event listeners
        if (!attachEventListeners()) {
            return;
        }

        isInitialized = true;
    }

    /**
     * Cleanup on page unload
     */
    function cleanup() {
        removeEventListeners();
        isInitialized = false;
    }

    /**
     * Initialize on page load
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    /**
     * Cleanup on page unload
     */
    window.addEventListener('beforeunload', cleanup);

    // Expose API for external use if needed
    window.BulkEditAction = {
        showSuccessMessage: showSuccessMessage,
        showErrorMessage: showErrorMessage
    };

})();

