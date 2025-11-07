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
        previewTable: '#preview-table',
        templateSelect: '#id_template'
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
     * Show success message using Wagtail's native message system
     */
    function showSuccessMessage(message, redirectUrl, data) {
        const messageContainer = document.querySelector(SELECTORS.messageContainer);
        if (!messageContainer) return;

        let detailsHtml = '';

        // Show detailed information about published vs draft pages
        if (data && (data.published > 0 || data.draft > 0)) {
            detailsHtml = '<ul style="margin-top: 10px; margin-left: 20px;">';

            if (data.published > 0) {
                detailsHtml += `<li><strong>${data.published}</strong> page(s) published immediately</li>`;
            }

            if (data.draft > 0) {
                detailsHtml += `<li><strong>${data.draft}</strong> page(s) saved as draft (had unpublished changes or were not live)</li>`;
            }

            detailsHtml += '</ul>';
        }

        // Show warning section for skipped pages if any
        let skippedPagesHtml = '';
        if (data && data.skipped > 0 && data.skipped_pages) {
            skippedPagesHtml = `
                <div style="margin-top: 20px; padding: 15px; background-color: #fef0cd; border-left: 4px solid #f0ad4e; border-radius: 4px;">
                    <h3 style="margin-top: 0; color: #8a6d3b; font-size: 16px;">
                        <svg style="width: 18px; height: 18px; vertical-align: middle; margin-right: 5px;" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                        </svg>
                        ${data.skipped} page(s) skipped
                    </h3>
                    <p style="margin-bottom: 10px; color: #8a6d3b;">The following pages could not be updated and require manual attention:</p>
                    <ul style="margin: 10px 0; padding-left: 20px; max-height: 300px; overflow-y: auto;">
                        ${data.skipped_pages.map(page => `
                            <li style="margin-bottom: 8px;">
                                <strong><a href="/admin/pages/${page.id}/edit/" target="_blank" style="text-decoration: underline;">${escapeHtml(page.title)}</a></strong>
                                <br>
                                <span style="color: #666; font-size: 13px;">${escapeHtml(page.reason)}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Add optional back button if redirect URL provided
        let backButtonHtml = '';
        if (redirectUrl) {
            backButtonHtml = `
                <p style="margin-top: 15px;">
                    <a href="${redirectUrl}" class="button button-small button-secondary">
                        Back to pages
                    </a>
                </p>
            `;
        }

        messageContainer.innerHTML = `
            <div class="messages" role="status">
                <ul>
                    <li class="success">
                        <svg class="icon icon-success messages-icon" aria-hidden="true">
                            <use href="#icon-success"></use>
                        </svg>
                        ${message}
                        ${detailsHtml}
                        ${skippedPagesHtml}
                        ${backButtonHtml}
                    </li>
                </ul>
            </div>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show error message using Wagtail's native message system
     */
    function showErrorMessage(message) {
        const messageContainer = document.querySelector(SELECTORS.messageContainer);
        if (!messageContainer) return;

        messageContainer.innerHTML = `
            <div class="messages" role="status">
                <ul>
                    <li class="error">
                        <svg class="icon icon-warning messages-icon" aria-hidden="true">
                            <use href="#icon-warning"></use>
                        </svg>
                        ${message}
                    </li>
                </ul>
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
                showSuccessMessage(data.message, redirectUrl, data);

                // Re-enable submit button so user can make another edit
                submitBtn.disabled = false;
                submitBtn.classList.remove('button-longrunning-active');
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
        
        // If empty, show placeholder text and reset validation
        if (!template) {
            const rows = previewTable.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const newValueCell = row.querySelector('.new-value');
                if (newValueCell) {
                    newValueCell.innerHTML = '<span class="preview-placeholder muted">Enter template above...</span>';
                }

                // Reset validation to waiting state
                const validationCell = row.querySelector('.validation-status');
                if (validationCell) {
                    validationCell.innerHTML = '<span class="validation-loading muted"><svg class="icon w-w-4 w-h-4" aria-hidden="true"><use href="#icon-spinner"></use></svg> Waiting...</span>';
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

            // Also trigger validation update
            await updateValidation();
        } catch (error) {
            console.error('Preview update error:', error);
        }
    }

    /**
     * Update validation results for all pages
     */
    async function updateValidation() {
        const textarea = document.querySelector(SELECTORS.textarea);
        const form = document.querySelector(SELECTORS.form);
        const previewTable = document.querySelector(SELECTORS.previewTable);

        if (!textarea || !form || !previewTable) return;

        const template = textarea.value.trim();

        // If empty, reset validation to waiting
        if (!template) {
            const validationCells = previewTable.querySelectorAll('.validation-status');
            validationCells.forEach(cell => {
                cell.innerHTML = '<span class="validation-loading muted"><svg class="icon w-w-4 w-h-4" aria-hidden="true"><use href="#icon-spinner"></use></svg> Waiting...</span>';
            });
            return;
        }

        try {
            const formData = new FormData(form);
            formData.set('template', template);

            const response = await fetch('/admin/api/validate-metadata-bulk/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success && data.validations) {
                // Update each row with validation results
                data.validations.forEach(validation => {
                    const validationCell = previewTable.querySelector(`.validation-status[data-page-id="${validation.page_id}"]`);
                    if (validationCell) {
                        renderValidationResult(validationCell, validation);
                    }
                });
            }
        } catch (error) {
            console.error('Validation update error:', error);
        }
    }

    /**
     * Render validation result in cell
     */
    function renderValidationResult(cell, validation) {
        cell.innerHTML = '';

        if (validation.is_valid) {
            // Valid - show success without character count
            cell.innerHTML = `
                <div class="validation-success">
                    <svg class="icon icon-success" aria-hidden="true"><use href="#icon-success"></use></svg>
                    <span>Valid</span>
                </div>
            `;
        } else {
            // Has issues - show them directly without character count
            let issuesHTML = '<div class="validation-issues-direct">';

            // Show all issues directly without collapsing
            issuesHTML += '<ul class="validation-issue-list">';
            validation.issues.forEach(issue => {
                const iconName = issue.severity === 'high' ? 'warning' : (issue.severity === 'medium' ? 'warning' : 'help');
                issuesHTML += `
                    <li class="validation-issue severity-${issue.severity}">
                        <svg class="icon icon-${iconName}" aria-hidden="true"><use href="#icon-${iconName}"></use></svg>
                        <span>${issue.message}</span>
                    </li>`;
            });
            issuesHTML += '</ul>';

            issuesHTML += '</div>';

            cell.innerHTML = issuesHTML;
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
    function insertPlaceholder(placeholder, truncateLength = null) {
        const textarea = document.querySelector(SELECTORS.textarea);
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

        // Trigger input event for any listeners (like character count and preview)
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    /**
     * Show truncation dialog and return the length
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
     * Handle placeholder badge click
     */
    function handlePlaceholderClick(e) {
        // Handle truncate button clicks
        const truncateBtn = e.target.closest('.placeholder-truncate-btn');
        if (truncateBtn) {
            e.stopPropagation(); // Prevent badge click from firing
            const placeholder = truncateBtn.dataset.placeholder;
            if (placeholder) {
                const truncateLength = promptForTruncation(placeholder);
                if (truncateLength !== null) {
                    insertPlaceholder(placeholder, truncateLength);
                }
            }
            return;
        }

        // Handle regular badge clicks (both old .placeholder-badge and new .placeholder-badge-main)
        const badge = e.target.closest('.placeholder-badge-main, .placeholder-badge');
        if (badge) {
            const placeholder = badge.dataset.placeholder;
            if (placeholder) {
                insertPlaceholder(placeholder);
            }
        }
    }

    /**
     * Handle template selection
     */
    function handleTemplateSelect(e) {
        const select = e.target;
        const selectedOption = select.options[select.selectedIndex];
        const textarea = document.querySelector(SELECTORS.textarea);

        if (!textarea) return;

        // Get template content from data attribute
        const templateContent = selectedOption.dataset.templateContent || '';

        // Set textarea value
        if (templateContent) {
            textarea.value = templateContent;

            // Trigger input event to update preview and character count
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    /**
     * Handle save as template button click
     */
    function handleSaveAsTemplate() {
        const textarea = document.querySelector(SELECTORS.textarea);
        const saveButton = document.getElementById('save-as-template');

        if (!textarea || !saveButton) return;

        const content = textarea.value.trim();

        if (!content) {
            alert('Please enter some content before saving as template.');
            return;
        }

        // Prompt for template name
        const templateName = prompt('Enter a name for this template:');

        if (!templateName || !templateName.trim()) {
            return; // User cancelled or entered empty name
        }

        const templateType = saveButton.dataset.templateType;
        const contentTypeId = saveButton.dataset.contentTypeId;

        // Show loading state
        saveButton.disabled = true;
        const originalHTML = saveButton.innerHTML;
        saveButton.innerHTML = '<svg class="icon"><use href="#icon-spinner"></use></svg> Saving...';

        // Prepare form data
        const formData = new FormData();
        formData.append('name', templateName.trim());
        formData.append('template_type', templateType);
        formData.append('template_content', content);
        if (contentTypeId) {
            formData.append('content_type_id', contentTypeId);
        }
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // Submit to save endpoint
        fetch('/admin/api/save-as-template/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);

                    // Reset button
                    saveButton.disabled = false;
                    saveButton.innerHTML = originalHTML;

                    // Optionally reload to show new template in dropdown
                    // window.location.reload();
                } else {
                    throw new Error(data.error || 'Failed to save template');
                }
            })
            .catch(error => {
                console.error('Save template error:', error);
                alert('Error: ' + error.message);

                // Reset button
                saveButton.disabled = false;
                saveButton.innerHTML = originalHTML;
            });
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        const form = document.querySelector(SELECTORS.form);
        const textarea = document.querySelector(SELECTORS.textarea);
        const placeholderCloud = document.querySelector('.placeholder-cloud');
        const templateSelect = document.querySelector(SELECTORS.templateSelect);
        const saveAsTemplateBtn = document.getElementById('save-as-template');

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

        // Template selection
        if (templateSelect) {
            templateSelect.addEventListener('change', handleTemplateSelect);
        }

        // Save as template button
        if (saveAsTemplateBtn) {
            saveAsTemplateBtn.addEventListener('click', handleSaveAsTemplate);
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

