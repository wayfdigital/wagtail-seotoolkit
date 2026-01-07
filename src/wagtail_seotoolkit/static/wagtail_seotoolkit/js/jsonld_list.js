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

        const csrfToken = getCSRFToken();

        fetch('/admin/api/proxy/get-plans/', {
            headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success && data.tiers) {
                    displayPlans(data, container);
                } else {
                    container.innerHTML = '<p style="text-align: center;">Unable to load plans. Please visit <a href="/admin/settings/subscription-settings/">Subscription Settings</a> to purchase.</p>';
                }
            })
            .catch(function (error) {
                console.error('Error loading plans:', error);
                container.innerHTML = '<p style="text-align: center;">Unable to load plans. Please visit <a href="/admin/settings/subscription-settings/">Subscription Settings</a> to purchase.</p>';
            });
    }

    /**
     * Display subscription tiers with interval toggle (matches bulk editor)
     */
    function displayPlans(data, plansContainer) {
        if (!data || !data.tiers || data.tiers.length === 0) {
            plansContainer.innerHTML = '<p style="text-align: center;">No plans available at this time.</p>';
            return;
        }

        let plansHtml = '<div class="plans-flex-centered">';

        // Display each tier as a card
        data.tiers.forEach(function (tier) {
            const monthlyPlan = tier.pricing.find(function (p) { return p.interval === 'month'; });
            const yearlyPlan = tier.pricing.find(function (p) { return p.interval === 'year'; });

            if (!monthlyPlan && !yearlyPlan) return; // Skip if no pricing

            // Use monthly as default
            const defaultPlan = monthlyPlan || yearlyPlan;

            plansHtml += '\
                <div class="plan-card" data-tier-id="' + tier.id + '">\
                    <div class="plan-header">\
                        <h4>' + tier.name + '</h4>\
                        <p class="tier-description">' + (tier.description || '') + '</p>\
                        \
                        <div class="plan-pricing" data-monthly-price="' + (monthlyPlan ? monthlyPlan.amountFormatted : '') + '" data-monthly-price-id="' + (monthlyPlan ? monthlyPlan.priceId : '') + '" data-yearly-price="' + (yearlyPlan ? yearlyPlan.amountFormatted : '') + '" data-yearly-price-id="' + (yearlyPlan ? yearlyPlan.priceId : '') + '" data-yearly-savings="' + (yearlyPlan && yearlyPlan.savingsFormatted ? yearlyPlan.savingsFormatted : '') + '">\
                            <div class="plan-price">' + defaultPlan.amountFormatted + '</div>\
                            <div class="plan-interval">per ' + defaultPlan.interval + '</div>\
                            ' + (yearlyPlan && yearlyPlan.savingsFormatted && defaultPlan.interval === 'year' ? '<span class="plan-savings">Save ' + yearlyPlan.savingsFormatted + '</span>' : '') + '\
                        </div>\
                        \
                        ' + (monthlyPlan && yearlyPlan ? '\
                            <div class="interval-toggle">\
                                <button class="interval-btn interval-btn-active" data-interval="month">Monthly</button>\
                                <button class="interval-btn" data-interval="year">Yearly</button>\
                            </div>\
                        ' : '') + '\
                    </div>\
                    <div class="plan-features">\
                        <ul class="email-verification-benefits-list">\
                            ' + tier.features.map(function (feature) { return '<li>✓ ' + feature + '</li>'; }).join('') + '\
                        </ul>\
                    </div>\
                    <button class="button button-primary purchase-plan-btn" data-price-id="' + defaultPlan.priceId + '">\
                        Purchase Now\
                    </button>\
                </div>\
            ';
        });

        plansHtml += '</div>';

        plansContainer.innerHTML = plansHtml;

        // Add click handlers to interval toggle buttons
        document.querySelectorAll('.interval-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                const card = e.target.closest('.plan-card');
                const interval = e.target.dataset.interval;
                const pricingDiv = card.querySelector('.plan-pricing');
                const priceDisplay = card.querySelector('.plan-price');
                const intervalDisplay = card.querySelector('.plan-interval');
                const savingsDisplay = card.querySelector('.plan-savings');
                const purchaseBtn = card.querySelector('.purchase-plan-btn');

                // Toggle active class
                card.querySelectorAll('.interval-btn').forEach(function (b) { b.classList.remove('interval-btn-active'); });
                e.target.classList.add('interval-btn-active');

                // Update pricing display
                if (interval === 'month') {
                    priceDisplay.textContent = pricingDiv.dataset.monthlyPrice;
                    intervalDisplay.textContent = 'per month';
                    if (savingsDisplay) savingsDisplay.remove();
                    purchaseBtn.dataset.priceId = pricingDiv.dataset.monthlyPriceId;
                } else {
                    priceDisplay.textContent = pricingDiv.dataset.yearlyPrice;
                    intervalDisplay.textContent = 'per year';
                    if (pricingDiv.dataset.yearlySavings && !savingsDisplay) {
                        const savings = document.createElement('span');
                        savings.className = 'plan-savings';
                        savings.textContent = 'Save ' + pricingDiv.dataset.yearlySavings;
                        pricingDiv.appendChild(savings);
                    }
                    purchaseBtn.dataset.priceId = pricingDiv.dataset.yearlyPriceId;
                }
            });
        });

        // Add click handlers to purchase buttons
        document.querySelectorAll('.purchase-plan-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                const priceId = e.target.dataset.priceId;
                handlePurchase(priceId);
            });
        });
    }

    /**
     * Handle purchase button click
     */
    function handlePurchase(priceId) {
        const context = window.django && window.django.subscriptionContext;
        // Redirect to settings page with plan pre-selected
        if (context && context.email) {
            // We have email, can proceed to checkout
            window.location.href = '/admin/settings/subscription-settings/?purchase=' + priceId;
        } else {
            // Need to configure email first
            alert('Please configure your email in Subscription Settings first.');
            window.location.href = '/admin/settings/subscription-settings/';
        }
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
