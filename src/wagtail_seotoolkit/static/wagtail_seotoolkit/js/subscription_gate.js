/**
 * Subscription Gate for Bulk Editor
 * 
 * Checks subscription status and shows upgrade banner if not subscribed.
 * Hides bulk editor content until subscription is verified.
 * 
 * Requires: subscription_status.js
 */

(function() {
    'use strict';

    const API_BASE_URL = SubscriptionStatus.API_BASE_URL;
    
    let currentEmail = null;
    let currentInstanceId = null;

    /**
     * Get email from page (from context variables)
     */
    function getEmailFromPage() {
        // Try to get from Django context (primary method)
        if (typeof window.django !== 'undefined' && 
            window.django.subscriptionContext && 
            window.django.subscriptionContext.email) {
            return window.django.subscriptionContext.email;
        }

        // Fallback: check for data attributes
        const emailSpan = document.querySelector('[data-subscription-email]');
        if (emailSpan) {
            return emailSpan.dataset.subscriptionEmail;
        }

        // Fallback: check for global variable
        if (typeof window.subscriptionEmail !== 'undefined') {
            return window.subscriptionEmail;
        }

        return null;
    }

    /**
     * Get instance ID from page
     */
    function getInstanceIdFromPage() {
        // Try to get from Django context (primary method)
        if (typeof window.django !== 'undefined' && 
            window.django.subscriptionContext && 
            window.django.subscriptionContext.instanceId) {
            return window.django.subscriptionContext.instanceId;
        }

        // Fallback: check for data attributes
        const instanceSpan = document.querySelector('[data-subscription-instance-id]');
        if (instanceSpan) {
            return instanceSpan.dataset.subscriptionInstanceId;
        }

        // Fallback: check for global variable
        if (typeof window.subscriptionInstanceId !== 'undefined') {
            return window.subscriptionInstanceId;
        }

        return null;
    }

    /**
     * Initialize subscription gate
     */
    function init() {
        // Get email and instance ID from Django context (passed via data attributes or script)
        const gateContainer = document.getElementById('subscription-gate-bulk-editor');
        if (!gateContainer) return;

        // Try to get from page context
        currentEmail = gateContainer.dataset.email || getEmailFromPage();
        currentInstanceId = gateContainer.dataset.instanceId || getInstanceIdFromPage();

        console.log('Subscription Gate Init:', {
            email: currentEmail,
            instanceId: currentInstanceId,
            hasEmail: !!currentEmail,
            hasInstanceId: !!currentInstanceId
        });

        // Check subscription status
        if (currentEmail && currentInstanceId) {
            checkSubscription();
        } else {
            console.warn('Missing email or instance ID - showing configuration required message');
            showNoEmailConfigured();
        }
    }

    /**
     * Check subscription status with API using shared module
     */
    async function checkSubscription() {
        const noEmailBanner = document.getElementById('no-email-banner');
        const upgradeBanner = document.getElementById('upgrade-banner');
        const protectedContent = document.getElementById('bulk-editor-protected-content');

        // Hide all content while checking
        if (noEmailBanner) noEmailBanner.style.display = 'none';
        if (upgradeBanner) upgradeBanner.style.display = 'none';
        if (protectedContent) protectedContent.style.display = 'none';

        try {
            // Use shared subscription checking module
            const result = await SubscriptionStatus.checkSubscription(currentEmail, currentInstanceId);

            if (result.isActive) {
                // Has active subscription and instance is registered
                // Hide banners and show protected content
                if (noEmailBanner) noEmailBanner.style.display = 'none';
                if (upgradeBanner) upgradeBanner.style.display = 'none';
                if (protectedContent) protectedContent.style.display = 'block';
            } else {
                // No subscription or not registered - show upgrade options
                showUpgradeBanner();
            }
        } catch (error) {
            console.error('Error checking subscription:', error);
            // On error, show upgrade banner to be safe
            showUpgradeBanner();
        }
    }

    /**
     * Show email verification required message (styled like SEO dashboard)
     * Explains bulk editor is pro feature requiring email verification + subscription
     */
    function showNoEmailConfigured() {
        const noEmailBanner = document.getElementById('no-email-banner');
        const upgradeBanner = document.getElementById('upgrade-banner');
        const protectedContent = document.getElementById('bulk-editor-protected-content');

        // Show email verification banner, hide others
        if (noEmailBanner) {
            noEmailBanner.style.display = 'flex'; // Use flex for email-verification-overlay
        }
        if (upgradeBanner) {
            upgradeBanner.style.display = 'none';
        }
        if (protectedContent) {
            protectedContent.style.display = 'none';
        }
    }

    /**
     * Show upgrade banner with plans (styled like email verification card)
     */
    function showUpgradeBanner() {
        const noEmailBanner = document.getElementById('no-email-banner');
        const upgradeBanner = document.getElementById('upgrade-banner');
        const protectedContent = document.getElementById('bulk-editor-protected-content');
        
        // Show upgrade banner, hide others
        if (noEmailBanner) {
            noEmailBanner.style.display = 'none';
        }
        if (upgradeBanner) {
            upgradeBanner.style.display = 'flex'; // Use flex for email-verification-overlay
        }
        if (protectedContent) {
            protectedContent.style.display = 'none';
        }

        // Load available plans
        loadPlans();
    }

    /**
     * Load available subscription plans
     */
    async function loadPlans() {
        const plansContainer = document.getElementById('plans-display-container');
        if (!plansContainer) return;

        try {
            const response = await fetch(`${API_BASE_URL}/get-plans/`, {
                headers: {
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.success && data.tiers) {
                displayPlans(data);
            } else {
                plansContainer.innerHTML = '<p style="text-align: center;">Unable to load plans. Please visit <a href="/admin/settings/subscription-settings/">Subscription Settings</a> to purchase.</p>';
            }
        } catch (error) {
            console.error('Error loading plans:', error);
            plansContainer.innerHTML = '<p style="text-align: center;">Unable to load plans. Please visit <a href="/admin/settings/subscription-settings/">Subscription Settings</a> to purchase.</p>';
        }
    }

    /**
     * Format price amount
     * Handles both pre-formatted strings and raw amounts in cents
     */
    function formatPrice(plan) {
        // If already formatted, use it
        if (plan.amountFormatted && typeof plan.amountFormatted === 'string' && plan.amountFormatted !== 'undefined') {
            return plan.amountFormatted;
        }
        
        // Otherwise format from cents
        if (plan.amount && typeof plan.amount === 'number') {
            const dollars = (plan.amount / 100).toFixed(2);
            const currency = plan.currency ? plan.currency.toUpperCase() : 'USD';
            return `$${dollars} ${currency}`;
        }
        
        // Fallback
        return 'Price not available';
    }

    /**
     * Display subscription tiers with interval toggle
     */
    function displayPlans(data) {
        const plansContainer = document.getElementById('plans-display-container');
        
        if (!data || !data.tiers || data.tiers.length === 0) {
            plansContainer.innerHTML = '<p style="text-align: center;">No plans available at this time.</p>';
            return;
        }

        let plansHtml = '<div class="plans-flex-centered">';
        
        // Display each tier as a card
        data.tiers.forEach(tier => {
            const monthlyPlan = tier.pricing.find(p => p.interval === 'month');
            const yearlyPlan = tier.pricing.find(p => p.interval === 'year');
            
            if (!monthlyPlan && !yearlyPlan) return; // Skip if no pricing
            
            // Use monthly as default
            const defaultPlan = monthlyPlan || yearlyPlan;
            
            plansHtml += `
                <div class="plan-card" data-tier-id="${tier.id}">
                    <div class="plan-header">
                        <h4>${tier.name}</h4>
                        <p class="tier-description">${tier.description || ''}</p>
                        
                        <div class="plan-pricing" data-monthly-price="${monthlyPlan ? monthlyPlan.amountFormatted : ''}" data-monthly-price-id="${monthlyPlan ? monthlyPlan.priceId : ''}" data-yearly-price="${yearlyPlan ? yearlyPlan.amountFormatted : ''}" data-yearly-price-id="${yearlyPlan ? yearlyPlan.priceId : ''}" data-yearly-savings="${yearlyPlan && yearlyPlan.savingsFormatted ? yearlyPlan.savingsFormatted : ''}">
                            <div class="plan-price">${defaultPlan.amountFormatted}</div>
                            <div class="plan-interval">per ${defaultPlan.interval}</div>
                            ${yearlyPlan && yearlyPlan.savingsFormatted && defaultPlan.interval === 'year' ? `<span class="plan-savings">Save ${yearlyPlan.savingsFormatted}</span>` : ''}
                        </div>
                        
                        ${monthlyPlan && yearlyPlan ? `
                            <div class="interval-toggle">
                                <button class="interval-btn interval-btn-active" data-interval="month">Monthly</button>
                                <button class="interval-btn" data-interval="year">Yearly</button>
                            </div>
                        ` : ''}
                    </div>
                    <div class="plan-features">
                        <ul class="email-verification-benefits-list">
                            ${tier.features.map(feature => `<li>✓ ${feature}</li>`).join('')}
                        </ul>
                    </div>
                    <button class="button button-primary purchase-plan-btn" data-price-id="${defaultPlan.priceId}">
                        Purchase Now
                    </button>
                </div>
            `;
        });
        
        plansHtml += '</div>';
        
        plansContainer.innerHTML = plansHtml;

        // Add click handlers to interval toggle buttons
        document.querySelectorAll('.interval-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const card = e.target.closest('.plan-card');
                const interval = e.target.dataset.interval;
                const pricingDiv = card.querySelector('.plan-pricing');
                const priceDisplay = card.querySelector('.plan-price');
                const intervalDisplay = card.querySelector('.plan-interval');
                const savingsDisplay = card.querySelector('.plan-savings');
                const purchaseBtn = card.querySelector('.purchase-plan-btn');
                
                // Toggle active class
                card.querySelectorAll('.interval-btn').forEach(b => b.classList.remove('interval-btn-active'));
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
                        savings.textContent = `Save ${pricingDiv.dataset.yearlySavings}`;
                        pricingDiv.appendChild(savings);
                    }
                    purchaseBtn.dataset.priceId = pricingDiv.dataset.yearlyPriceId;
                }
            });
        });

        // Add click handlers to purchase buttons
        document.querySelectorAll('.purchase-plan-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const priceId = e.target.dataset.priceId;
                handlePurchase(priceId);
            });
        });
    }

    /**
     * Handle purchase button click
     */
    function handlePurchase(priceId) {
        // Redirect to settings page with plan pre-selected
        if (currentEmail) {
            // We have email, can proceed to checkout
            window.location.href = `/admin/settings/subscription-settings/?purchase=${priceId}`;
        } else {
            // Need to configure email first
            alert('Please configure your email in Subscription Settings first.');
            window.location.href = '/admin/settings/subscription-settings/';
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Only init if we're on the bulk editor page
        if (document.getElementById('subscription-gate-bulk-editor')) {
            init();
        }
    });

})();

