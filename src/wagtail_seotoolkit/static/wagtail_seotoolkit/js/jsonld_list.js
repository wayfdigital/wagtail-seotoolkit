/**
 * JSON-LD Schema List JavaScript
 * 
 * Handles template deletion and subscription gating for the schema list view.
 */

(function () {
    'use strict';

    /**
     * Get CSRF token from the page or from Django's cookie
     */
    function getCSRFToken() {
        // First try to get from the hidden input
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }

        // Fallback: get from cookie (Django's standard approach)
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }

        return null;
    }

    /**
     * Initialize delete button handlers
     * Called after DOM is ready and content may be visible
     */
    function initDeleteButtons() {
        document.querySelectorAll('.delete-template').forEach(function (button) {
            // Avoid adding multiple event listeners
            if (button.hasAttribute('data-delete-initialized')) {
                return;
            }
            button.setAttribute('data-delete-initialized', 'true');

            button.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                const templateId = this.getAttribute('data-template-id');
                const templateName = this.getAttribute('data-template-name');

                if (!templateId) {
                    console.error('Delete button missing template ID');
                    return;
                }

                if (confirm('Are you sure you want to delete the template "' + templateName + '"?')) {
                    const csrfToken = getCSRFToken();

                    if (!csrfToken) {
                        showMessage('error', 'Security token not found. Please refresh the page and try again.');
                        return;
                    }

                    fetch('/admin/seo-toolkit/jsonld-schemas/' + templateId + '/delete/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/json'
                        }
                    })
                        .then(function (response) {
                            if (!response.ok) {
                                throw new Error('Server returned ' + response.status);
                            }
                            return response.json();
                        })
                        .then(function (data) {
                            if (data.success) {
                                // Remove the row from the table
                                const row = document.querySelector('tr[data-template-id="' + templateId + '"]');
                                if (row) {
                                    row.remove();
                                }
                                showMessage('success', data.message || 'Template deleted successfully');

                                // Check if table is now empty
                                const tbody = document.querySelector('.listing tbody');
                                if (tbody && tbody.children.length === 0) {
                                    // Reload page to show empty state
                                    window.location.reload();
                                }
                            } else {
                                showMessage('error', data.error || 'Failed to delete template');
                            }
                        })
                        .catch(function (error) {
                            console.error('Delete error:', error);
                            showMessage('error', 'An error occurred: ' + error.message);
                        });
                }
            });
        });
    }

    // Subscription gating for JSON-LD Editor (similar to bulk editor)
    function initSubscriptionGate() {
        const gate = document.getElementById('subscription-gate-jsonld-editor');
        const content = document.getElementById('jsonld-editor-protected-content');
        const noEmailBanner = document.getElementById('no-email-banner');
        const upgradeBanner = document.getElementById('upgrade-banner');

        if (!gate || !content) {
            // No subscription gate - just show content and init buttons
            initDeleteButtons();
            return;
        }

        const context = window.django && window.django.subscriptionContext;

        if (!context || !context.email) {
            // No email verified - show verification required
            noEmailBanner.style.display = 'flex';
            upgradeBanner.style.display = 'none';
            content.style.display = 'none';
            return;
        }

        // Check subscription status
        if (context.email && context.instanceId) {
            fetch('/admin/api/proxy/check-subscription/?email=' + encodeURIComponent(context.email) + '&instanceId=' + encodeURIComponent(context.instanceId))
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data.pro) {
                        // Has pro subscription - show content
                        gate.style.display = 'none';
                        content.style.display = 'block';
                        // Initialize delete buttons after content is shown
                        initDeleteButtons();
                    } else {
                        // No pro subscription - show upgrade banner
                        noEmailBanner.style.display = 'none';
                        upgradeBanner.style.display = 'flex';
                        content.style.display = 'none';
                        loadPlans();
                    }
                })
                .catch(function (error) {
                    console.error('Failed to check subscription:', error);
                    // On error, show content (fail open for better UX)
                    gate.style.display = 'none';
                    content.style.display = 'block';
                    // Initialize delete buttons after content is shown
                    initDeleteButtons();
                });
        }
    }

    function loadPlans() {
        const container = document.getElementById('plans-display-container');
        if (!container) return;

        fetch('/admin/api/proxy/get-plans/')
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success && data.plans) {
                    container.innerHTML = renderPlans(data.plans);
                } else {
                    container.innerHTML = '<p>Unable to load pricing plans. Please try again later.</p>';
                }
            })
            .catch(function (error) {
                container.innerHTML = '<p>Unable to load pricing plans. Please try again later.</p>';
            });
    }

    function renderPlans(plans) {
        let html = '<div class="plans-grid" style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">';

        plans.forEach(function (plan) {
            html += '<div class="plan-card" style="border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; text-align: center; min-width: 200px;">';
            html += '<h3 style="margin: 0 0 0.5rem 0;">' + plan.name + '</h3>';
            html += '<p style="font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0;">$' + (plan.price / 100).toFixed(2) + '</p>';
            html += '<p style="color: #666; margin: 0 0 1rem 0;">' + plan.interval + '</p>';
            html += '<button class="button" onclick="window.open(\'/admin/settings/subscription-settings/\', \'_self\')">Subscribe</button>';
            html += '</div>';
        });

        html += '</div>';
        return html;
    }

    // Utility function to show messages
    function showMessage(type, message) {
        const container = document.getElementById('message-container');
        if (!container) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'messages';

        const messageInner = document.createElement('div');
        messageInner.className = 'message ' + type;
        messageInner.textContent = message;

        messageDiv.appendChild(messageInner);
        container.innerHTML = '';
        container.appendChild(messageDiv);

        // Auto-hide after 5 seconds
        setTimeout(function () {
            messageDiv.remove();
        }, 5000);
    }

    // Initialize subscription gate on page load
    document.addEventListener('DOMContentLoaded', function () {
        initSubscriptionGate();
    });

})();
