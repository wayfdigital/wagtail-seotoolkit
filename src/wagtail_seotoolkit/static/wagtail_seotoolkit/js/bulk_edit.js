/**
 * Bulk Edit - Checkbox Selection and Action Buttons
 * 
 * Manages page selection via checkboxes and enables/disables bulk action buttons.
 * Handles AJAX updates when filters are applied.
 */

(function() {
    'use strict';

    // Configuration
    const SELECTORS = {
        form: '#bulk-edit-form',
        selectAllCheckbox: '#select-all-checkbox',
        bulkCheckbox: '.bulk-action-checkbox',
        selectedCount: '#selected-count',
        editTitleBtn: '#edit-title-btn',
        editDescBtn: '#edit-description-btn',
        resultsContainer: '#listing-results',  // Wagtail's AJAX results container
        listingContainer: '.listing'
    };

    // State
    let mutationObserver = null;
    let eventListenersAttached = false;

    /**
     * Get all bulk checkboxes (recalculated each time to handle AJAX updates)
     */
    function getBulkCheckboxes() {
        return document.querySelectorAll(SELECTORS.bulkCheckbox);
    }

    /**
     * Get count of checked checkboxes
     */
    function getCheckedCount() {
        return document.querySelectorAll(`${SELECTORS.bulkCheckbox}:checked`).length;
    }

    /**
     * Update UI based on current checkbox states
     */
    function updateUI() {
        const selectAllCheckbox = document.querySelector(SELECTORS.selectAllCheckbox);
        const selectedCount = document.querySelector(SELECTORS.selectedCount);
        const editTitleBtn = document.querySelector(SELECTORS.editTitleBtn);
        const editDescBtn = document.querySelector(SELECTORS.editDescBtn);

        if (!selectAllCheckbox) return;

        const bulkCheckboxes = getBulkCheckboxes();
        const checkedCount = getCheckedCount();
        const totalCount = bulkCheckboxes.length;

        // Update counter text
        if (selectedCount) {
            selectedCount.textContent = `${checkedCount} selected`;
        }

        // Update select all checkbox state
        if (checkedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === totalCount && totalCount > 0) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }

        // Enable/disable action buttons
        const hasSelection = checkedCount > 0;
        if (editTitleBtn) editTitleBtn.disabled = !hasSelection;
        if (editDescBtn) editDescBtn.disabled = !hasSelection;
    }

    /**
     * Handle select all checkbox change
     */
    function handleSelectAllChange(e) {
        const isChecked = e.target.checked;
        const bulkCheckboxes = getBulkCheckboxes();

        bulkCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });

        updateUI();
    }

    /**
     * Handle individual checkbox change (using event delegation)
     */
    function handleCheckboxChange(e) {
        if (e.target.classList.contains('bulk-action-checkbox')) {
            updateUI();
        }
    }

    /**
     * Remove all event listeners
     */
    function removeEventListeners() {
        if (!eventListenersAttached) return;

        const form = document.querySelector(SELECTORS.form);
        const selectAllCheckbox = document.querySelector(SELECTORS.selectAllCheckbox);

        if (form) {
            form.removeEventListener('change', handleCheckboxChange);
        }

        if (selectAllCheckbox) {
            selectAllCheckbox.removeEventListener('change', handleSelectAllChange);
        }

        eventListenersAttached = false;
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        const form = document.querySelector(SELECTORS.form);
        const selectAllCheckbox = document.querySelector(SELECTORS.selectAllCheckbox);

        if (!form || !selectAllCheckbox) {
            return false;
        }

        // Remove existing listeners to prevent duplicates
        removeEventListeners();

        // Use event delegation on form for bulk checkboxes
        form.addEventListener('change', handleCheckboxChange);

        // Select all checkbox
        selectAllCheckbox.addEventListener('change', handleSelectAllChange);

        eventListenersAttached = true;
        return true;
    }

    /**
     * Initialize mutation observer to watch for AJAX updates
     */
    function initializeMutationObserver() {
        // Clean up existing observer
        if (mutationObserver) {
            mutationObserver.disconnect();
            mutationObserver = null;
        }

        // Watch for changes to the results container or body (Wagtail replaces content during AJAX)
        let targetElement = document.querySelector(SELECTORS.resultsContainer);
        
        // Fallback to body if results container not found
        if (!targetElement) {
            targetElement = document.body;
        }

        // Watch for changes that indicate AJAX updates
        mutationObserver = new MutationObserver(function(mutations) {
            let shouldReinitialize = false;

            for (const mutation of mutations) {
                // Check if content was added (AJAX update)
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if the added content contains our form or bulk edit elements
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Check if the node itself or its descendants contain the form
                            const containsForm = node.id === 'bulk-edit-form' || 
                                               node.querySelector && node.querySelector(SELECTORS.form);
                            
                            if (containsForm) {
                                shouldReinitialize = true;
                                break;
                            }
                        }
                    }
                    
                    if (shouldReinitialize) break;
                }
            }

            if (shouldReinitialize) {
                // Small delay to ensure DOM is fully updated
                setTimeout(reinitialize, 100);
            }
        });

        // Observe with childList to catch when Wagtail replaces content
        mutationObserver.observe(targetElement, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Reinitialize after AJAX update
     */
    function reinitialize() {
        // Don't reinitialize if elements don't exist
        const form = document.querySelector(SELECTORS.form);
        if (!form) {
            return;
        }
        
        // Reattach listeners and update UI
        if (attachEventListeners()) {
            updateUI();
        }
    }

    /**
     * Initialize bulk edit UI
     */
    function initialize() {
        const form = document.querySelector(SELECTORS.form);
        if (!form) {
            // Form not found, might not be on bulk edit page
            return;
        }

        // Attach event listeners
        if (!attachEventListeners()) {
            return;
        }

        // Initialize mutation observer for AJAX updates (only once)
        if (!mutationObserver) {
            initializeMutationObserver();
        }

        // Initial UI update
        updateUI();
    }

    /**
     * Cleanup on page unload
     */
    function cleanup() {
        removeEventListeners();
        
        if (mutationObserver) {
            mutationObserver.disconnect();
            mutationObserver = null;
        }
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

    // Expose reinitialize for external use if needed
    window.BulkEdit = {
        reinitialize: reinitialize,
        updateUI: updateUI
    };

})();

