/**
 * Subscription Settings Page
 * 
 * Manages subscription status display, plan selection, and instance management.
 * 
 * Requires: subscription_status.js
 */

(function() {
    'use strict';

    const API_BASE_URL = SubscriptionStatus.API_BASE_URL;
    
    let currentEmail = null;
    let currentInstanceId = null;
    let subscriptionData = null;

    /**
     * Initialize the subscription settings page
     */
    function init() {
        // Get email and instance ID from page
        const emailElement = document.getElementById('registered-email');
        const instanceIdElement = document.getElementById('instance-id');
        
        if (emailElement) {
            currentEmail = emailElement.textContent.trim();
        }
        
        if (instanceIdElement) {
            const instanceText = instanceIdElement.textContent.trim();
            if (instanceText !== 'Not yet configured') {
                currentInstanceId = instanceText;
            }
        }

        // Set up event listeners
        setupEventListeners();

        // Check subscription status if we have email and instance ID
        if (currentEmail && currentInstanceId) {
            checkSubscriptionStatus();
        } else if (!currentEmail) {
            // Show email registration form (already visible)
            showNoSubscription();
        }
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Email registration form
        const emailForm = document.getElementById('email-registration-form');
        if (emailForm) {
            emailForm.addEventListener('submit', handleEmailRegistration);
        }

        // Refresh status button
        const refreshBtn = document.getElementById('refresh-status-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (currentEmail && currentInstanceId) {
                    checkSubscriptionStatus();
                }
            });
        }

        // Manage subscription button (Stripe portal)
        const manageBtn = document.getElementById('manage-subscription-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', openStripePortal);
        }

        // Register instance button
        const registerBtn = document.getElementById('register-instance-btn');
        if (registerBtn) {
            registerBtn.addEventListener('click', registerInstance);
        }
    }

    /**
     * Handle email registration form submission
     */
    async function handleEmailRegistration(e) {
        e.preventDefault();
        
        const emailInput = document.getElementById('registration-email');
        const email = emailInput.value.trim();
        
        if (!email) {
            showMessage('registration-message', 'Please enter a valid email address', 'error');
            return;
        }

        try {
            // Save email to backend
            const response = await fetch('/admin/api/email-verification/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();
            
            if (data.success) {
                showMessage('registration-message', 'Email saved! Reloading...', 'success');
                // Reload page to show new state
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showMessage('registration-message', data.error || 'Failed to save email', 'error');
            }
        } catch (error) {
            showMessage('registration-message', 'Error: ' + error.message, 'error');
        }
    }

    /**
     * Check subscription status via API using shared module
     */
    async function checkSubscriptionStatus() {
        if (!currentEmail || !currentInstanceId) return;

        const statusContainer = document.getElementById('subscription-status-content');
        statusContainer.innerHTML = '<div class="loading-spinner"><p>Checking subscription status...</p></div>';

        try {
            // Use shared subscription checking module
            const result = await SubscriptionStatus.checkSubscription(currentEmail, currentInstanceId);
            subscriptionData = result.data;

            // Check if user has any active subscriptions
            const hasSubscription = result.data.subscriptionsCount > 0 || 
                                   result.data.activeSubscriptionsCount > 0;

            if (result.isActive) {
                // Has active subscription AND instance is activated
                showActiveSubscription(result.data);
            } else if (hasSubscription && !result.isRegistered) {
                // Has subscription but instance not registered
                showUnregisteredInstance(result.data);
            } else if (hasSubscription && result.isRegistered && !result.isActive) {
                // Has subscription and instance is registered but not activated
                showNotActivatedInstance(result.data);
            } else {
                // No subscription found
                showNoSubscription();
            }
        } catch (error) {
            statusContainer.innerHTML = `
                <div class="error-message">
                    <p>Error checking subscription: ${error.message}</p>
                </div>
            `;
            showNoSubscription();
        }
    }

    /**
     * Show active subscription status
     */
    function showActiveSubscription(data) {
        const statusContainer = document.getElementById('subscription-status-content');
        
        const tierDisplay = data.planTier || 'pro';
        const statusDisplay = data.status || 'active';
        const statusClass = statusDisplay === 'active' ? 'status-active' : 'status-warning';
        
        let expiryHtml = '';
        if (data.currentPeriodEnd) {
            const expiryDate = new Date(data.currentPeriodEnd);
            expiryHtml = `
                <div class="info-row">
                    <strong>Renews:</strong>
                    <span>${expiryDate.toLocaleDateString()}</span>
                </div>
            `;
        }

        let cancelHtml = '';
        if (data.cancelAtPeriodEnd) {
            cancelHtml = `
                <div class="info-row warning">
                    <strong>⚠️ Cancellation Scheduled:</strong>
                    <span>Subscription will cancel on ${new Date(data.cancelAt).toLocaleDateString()}</span>
                </div>
            `;
        }

        // Show multiple subscriptions info if available
        let subscriptionsHtml = '';
        if (data.subscriptions && data.subscriptions.length > 0) {
            subscriptionsHtml = `
                <div class="subscriptions-list">
                    <strong>Active Subscriptions (${data.subscriptionsCount || data.subscriptions.length}):</strong>
                    <ul class="subscription-items">
            `;
            data.subscriptions.forEach(sub => {
                subscriptionsHtml += `
                    <li>
                        <span class="sub-name">${sub.planName || sub.planTier}</span>
                        <span class="sub-seats">(${sub.maxInstances} seat${sub.maxInstances > 1 ? 's' : ''})</span>
                    </li>
                `;
            });
            subscriptionsHtml += `
                    </ul>
                </div>
            `;
        }

        // Seats information
        const totalSeats = data.totalSeats || data.seats?.max || 0;
        const usedSeats = data.activeInstancesCount || data.seats?.used || 0;
        const availableSlots = data.availableSlots || data.seats?.available || 0;

        statusContainer.innerHTML = `
            <div class="subscription-active">
                <div class="status-badge ${statusClass}">
                    ✓ ${tierDisplay.toUpperCase()} - ${statusDisplay.toUpperCase()}
                </div>
                <div class="subscription-details">
                    ${subscriptionsHtml || `
                        <div class="info-row">
                            <strong>Plan:</strong>
                            <span>${data.planName || 'Pro Plan'}</span>
                        </div>
                        <div class="info-row">
                            <strong>Billing:</strong>
                            <span>${data.interval || 'monthly'}</span>
                        </div>
                    `}
                    ${expiryHtml}
                    ${cancelHtml}
                    ${totalSeats > 0 ? `
                        <div class="info-row">
                            <strong>Total Seats:</strong>
                            <span class="seats-badge">${totalSeats}</span>
                        </div>
                        <div class="info-row">
                            <strong>Active Instances:</strong>
                            <span class="${usedSeats > totalSeats ? 'warning-text' : ''}">${usedSeats} / ${totalSeats}</span>
                        </div>
                        <div class="info-row">
                            <strong>Available Slots:</strong>
                            <span class="${availableSlots < 0 ? 'error-text' : 'success-text'}">${availableSlots}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        // Show manage subscription button
        document.getElementById('manage-subscription-btn').style.display = 'inline-block';
        
        // Hide register button
        document.getElementById('register-instance-btn').style.display = 'none';

        // Show available plans for purchasing additional subscriptions
        if (currentEmail) {
            loadAvailablePlans();
        }

        // Always show instance management if has subscription
        loadInstancesList();
    }

    /**
     * Show unregistered instance message
     */
    function showUnregisteredInstance(data) {
        const statusContainer = document.getElementById('subscription-status-content');
        
        statusContainer.innerHTML = `
            <div class="subscription-warning">
                <div class="status-badge status-warning">
                    ⚠️ INSTANCE NOT REGISTERED
                </div>
                <div class="subscription-details">
                    <p>You have an active subscription, but this instance is not registered.</p>
                    ${data.maxInstances ? `
                        <p><strong>Available slots:</strong> ${data.maxInstances - (data.currentInstanceCount || 0)} of ${data.maxInstances}</p>
                    ` : ''}
                    <p>Click "Register This Instance" below to activate pro features.</p>
                </div>
            </div>
        `;

        // Show register button
        document.getElementById('register-instance-btn').style.display = 'inline-block';
        
        // Show manage button
        document.getElementById('manage-subscription-btn').style.display = 'inline-block';

        // Show available plans for purchasing additional subscriptions
        if (currentEmail) {
            loadAvailablePlans();
        }

        // Show instance management even if instance not registered
        loadInstancesList();
    }

    /**
     * Show not activated instance message
     */
    function showNotActivatedInstance(data) {
        const statusContainer = document.getElementById('subscription-status-content');
        
        const totalSeats = data.totalSeats || 0;
        const activeInstancesCount = data.activeInstancesCount || 0;
        const availableSlots = data.availableSlots || 0;

        statusContainer.innerHTML = `
            <div class="subscription-warning">
                <div class="status-badge status-warning">
                    ⚠️ INSTANCE NOT ACTIVATED
                </div>
                <div class="subscription-details">
                    <p>You have an active subscription, but this instance is not activated.</p>
                    ${totalSeats > 0 ? `
                        <div class="info-row">
                            <strong>Total Seats:</strong> <span>${totalSeats}</span>
                        </div>
                        <div class="info-row">
                            <strong>Active Instances:</strong> <span>${activeInstancesCount} / ${totalSeats}</span>
                        </div>
                        <div class="info-row">
                            <strong>Available Slots:</strong> <span class="${availableSlots > 0 ? 'success-text' : 'error-text'}">${availableSlots}</span>
                        </div>
                    ` : ''}
                    <p>Please activate this instance below to enable pro features.</p>
                </div>
            </div>
        `;

        // Show manage button
        document.getElementById('manage-subscription-btn').style.display = 'inline-block';
        
        // Hide register button (already registered)
        document.getElementById('register-instance-btn').style.display = 'none';

        // Show available plans for purchasing additional subscriptions
        if (currentEmail) {
            loadAvailablePlans();
        }

        // Show instance management to allow activation
        loadInstancesList();
    }

    /**
     * Show no subscription state
     */
    function showNoSubscription() {
        const statusContainer = document.getElementById('subscription-status-content');
        
        statusContainer.innerHTML = `
            <div class="subscription-inactive">
                <div class="status-badge status-inactive">
                    FREE TIER
                </div>
                <p>No active subscription found. Purchase a plan below to unlock pro features.</p>
            </div>
        `;

        // Hide action buttons
        document.getElementById('manage-subscription-btn').style.display = 'none';
        document.getElementById('register-instance-btn').style.display = 'none';

        // Show available plans
        if (currentEmail) {
            loadAvailablePlans();
        }
    }

    /**
     * Load available subscription plans
     */
    async function loadAvailablePlans() {
        const plansSection = document.getElementById('available-plans-section');
        const plansContainer = document.getElementById('plans-container');
        const plansSectionHeading = plansSection.querySelector('h2');
        
        plansSection.style.display = 'block';
        plansContainer.innerHTML = '<div class="loading-spinner"><p>Loading plans...</p></div>';

        // Update heading based on whether user has subscription
        if (subscriptionData && (subscriptionData.subscriptionsCount > 0 || subscriptionData.activeSubscriptionsCount > 0)) {
            plansSectionHeading.textContent = 'Purchase Additional Subscriptions';
        } else {
            plansSectionHeading.textContent = 'Available Plans';
        }

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
                plansContainer.innerHTML = '<p>Unable to load plans. Please try again later.</p>';
            }
        } catch (error) {
            plansContainer.innerHTML = `<p>Error loading plans: ${error.message}</p>`;
        }
    }

    /**
     * Display subscription tiers with interval toggle
     */
    function displayPlans(data) {
        const plansContainer = document.getElementById('plans-container');
        
        if (!data || !data.tiers || data.tiers.length === 0) {
            plansContainer.innerHTML = '<p>No plans available at this time.</p>';
            return;
        }

        let plansHtml = '<div class="plans-flex">';
        
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
                        Purchase
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
                purchasePlan(priceId);
            });
        });
    }


    /**
     * Purchase a plan (redirect to Stripe checkout)
     */
    async function purchasePlan(priceId) {
        if (!currentEmail) {
            alert('Please register your email first');
            return;
        }

        try {
            const returnUrl = window.location.origin + window.location.pathname + '?purchase=success';
            
            const response = await fetch(`${API_BASE_URL}/create-checkout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail,
                    priceId: priceId,
                    returnUrl: returnUrl
                })
            });

            const data = await response.json();
            
            if (data.success && data.url) {
                // Redirect to Stripe checkout
                window.location.href = data.url;
            } else {
                alert('Failed to create checkout session: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    /**
     * Register this instance to the subscription
     */
    async function registerInstance() {
        if (!currentEmail || !currentInstanceId) {
            alert('Missing email or instance ID');
            return;
        }

        const registerBtn = document.getElementById('register-instance-btn');
        registerBtn.disabled = true;
        registerBtn.textContent = 'Registering...';

        try {
            const siteUrl = window.location.origin;
            
            const response = await fetch(`${API_BASE_URL}/register-instance/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail,
                    instanceId: currentInstanceId,
                    siteUrl: siteUrl
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('Instance registered successfully!');
                // Reload to show updated status
                window.location.reload();
            } else {
                alert('Failed to register instance: ' + (data.error || data.message || 'Unknown error'));
                registerBtn.disabled = false;
                registerBtn.textContent = 'Register This Instance';
            }
        } catch (error) {
            alert('Error: ' + error.message);
            registerBtn.disabled = false;
            registerBtn.textContent = 'Register This Instance';
        }
    }

    /**
     * Open Stripe customer portal
     */
    async function openStripePortal() {
        if (!currentEmail || !currentInstanceId) {
            alert('Missing email or instance ID');
            return;
        }

        try {
            const returnUrl = window.location.href;
            
            const response = await fetch(`${API_BASE_URL}/create-portal/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail,
                    instanceId: currentInstanceId,
                    returnUrl: returnUrl
                })
            });

            const data = await response.json();
            
            if (data.success && data.url) {
                // Redirect to Stripe portal
                window.location.href = data.url;
            } else {
                alert('Failed to open portal: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    /**
     * Load instances list for multi-seat subscriptions
     */
    async function loadInstancesList() {
        if (!currentEmail) return;

        const section = document.getElementById('instance-management-section');
        const container = document.getElementById('instances-list-container');
        
        section.style.display = 'block';
        container.innerHTML = '<div class="loading-spinner"><p>Loading instances...</p></div>';

        try {
            const response = await fetch(
                `${API_BASE_URL}/list-instances/?email=${encodeURIComponent(currentEmail)}`,
                {
                    headers: {
                        'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                    }
                }
            );

            const data = await response.json();
            
            if (data.success && data.instances) {
                displayInstancesList(data);
            } else {
                container.innerHTML = '<p>No instances found</p>';
            }
        } catch (error) {
            container.innerHTML = `<p>Error loading instances: ${error.message}</p>`;
        }
    }

    /**
     * Display instances list with active/inactive status and selection
     */
    function displayInstancesList(data) {
        const container = document.getElementById('instances-list-container');
        const instances = data.instances || [];
        const totalSeats = data.totalSeats || 0;
        const currentCount = data.currentCount || 0;
        const activeInstancesCount = data.activeInstancesCount || 0;
        const availableSlots = data.availableSlots || 0;
        
        let html = `
            <div class="instances-summary">
                <div class="summary-row">
                    <strong>Total Seats:</strong> <span class="seats-badge">${totalSeats}</span>
                </div>
                <div class="summary-row">
                    <strong>Registered Instances:</strong> <span>${currentCount}</span>
                </div>
                <div class="summary-row">
                    <strong>Active Instances:</strong> <span class="${activeInstancesCount > totalSeats ? 'warning-text' : ''}">${activeInstancesCount} / ${totalSeats}</span>
                </div>
                <div class="summary-row">
                    <strong>Available Slots:</strong> <span class="${availableSlots < 0 ? 'error-text' : 'success-text'}">${availableSlots}</span>
                </div>
            </div>
        `;
        
        if (activeInstancesCount > totalSeats) {
            html += `
                <div class="warning-box">
                    <strong>⚠️ Warning:</strong> You have more active instances (${activeInstancesCount}) than available seats (${totalSeats}). 
                    Please deactivate some instances to restore pro access.
                </div>
            `;
        }
        
        html += `
            <div class="instances-actions">
                <button id="save-active-instances-btn" class="button button-primary">
                    Save Active Instances
                </button>
                <button id="clear-all-instances-btn" class="button button-secondary">
                    Deactivate All
                </button>
            </div>
            <div class="instances-table-container">
                <table class="instances-table">
                    <thead>
                        <tr>
                            <th class="checkbox-col">
                                <input type="checkbox" id="select-all-instances" title="Select All">
                            </th>
                            <th>Active</th>
                            <th>Site URL</th>
                            <th>Instance ID</th>
                            <th>Registered</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        instances.forEach(instance => {
            const isCurrent = instance.instanceId === currentInstanceId;
            const isActive = instance.isActive || false;
            const registeredDate = new Date(instance.registeredAt).toLocaleDateString();
            
            html += `
                <tr class="instance-row ${isCurrent ? 'current-instance-row' : ''}" data-instance-id="${instance.instanceId}">
                    <td class="checkbox-col">
                        <input type="checkbox" class="instance-checkbox" data-instance-id="${instance.instanceId}" ${isActive ? 'checked' : ''}>
                    </td>
                    <td>
                        <span class="status-badge ${isActive ? 'status-active' : 'status-inactive'}">
                            ${isActive ? '✓ Active' : '○ Inactive'}
                        </span>
                    </td>
                    <td>
                        <div class="site-info">
                            <strong>${instance.siteUrl || 'Unknown Site'}</strong>
                            ${isCurrent ? '<span class="badge-current">This Instance</span>' : ''}
                        </div>
                    </td>
                    <td>
                        <code class="instance-id-short">${instance.instanceId.substring(0, 12)}...</code>
                    </td>
                    <td>${registeredDate}</td>
                    <td>
                        ${!isCurrent ? `
                            <button class="button button-small button-secondary remove-instance-btn" data-instance-id="${instance.instanceId}">
                                Remove
                            </button>
                        ` : '<span class="text-muted">—</span>'}
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = html;

        // Add event handlers
        setupInstancesEventHandlers();
    }

    /**
     * Set up event handlers for instances list
     */
    function setupInstancesEventHandlers() {
        // Select all checkbox
        const selectAllCheckbox = document.getElementById('select-all-instances');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                const checkboxes = document.querySelectorAll('.instance-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
            });
        }

        // Save active instances button
        const saveBtn = document.getElementById('save-active-instances-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveActiveInstances);
        }

        // Clear all instances button
        const clearBtn = document.getElementById('clear-all-instances-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', clearAllInstances);
        }

        // Remove instance buttons
        document.querySelectorAll('.remove-instance-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const instanceId = e.target.dataset.instanceId;
                if (confirm('Are you sure you want to remove this instance? This action cannot be undone.')) {
                    removeInstance(instanceId);
                }
            });
        });
    }

    /**
     * Save active instances selection
     */
    async function saveActiveInstances() {
        const checkboxes = document.querySelectorAll('.instance-checkbox:checked');
        const activeInstanceIds = Array.from(checkboxes).map(cb => cb.dataset.instanceId);

        if (activeInstanceIds.length === 0) {
            if (!confirm('No instances selected. This will deactivate all instances. Continue?')) {
                return;
            }
        }

        try {
            const response = await fetch(`${API_BASE_URL}/set-active-instances/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail,
                    instanceIds: activeInstanceIds
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('✓ Active instances updated successfully! Changes will take effect immediately.');
                loadInstancesList(); // Reload list
                checkSubscriptionStatus(); // Refresh subscription status
            } else {
                alert('Failed to update active instances: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    /**
     * Clear all active instances
     */
    async function clearAllInstances() {
        if (!confirm('This will deactivate ALL instances. Pro features will be unavailable until you activate instances again. Continue?')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/clear-active-instances/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('✓ All instances deactivated successfully.');
                loadInstancesList(); // Reload list
                checkSubscriptionStatus(); // Refresh subscription status
            } else {
                alert('Failed to clear active instances: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    /**
     * Remove an instance
     */
    async function removeInstance(instanceId) {
        try {
            const response = await fetch(`${API_BASE_URL}/remove-instance/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SubscriptionStatus.getCSRFToken()
                },
                body: JSON.stringify({
                    email: currentEmail,
                    instanceId: instanceId
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('Instance removed successfully');
                loadInstancesList(); // Reload list
            } else {
                alert('Failed to remove instance: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    /**
     * Show message
     */
    function showMessage(containerId, message, type) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const className = type === 'error' ? 'error-message' : 'success-message';
        container.innerHTML = `<div class="${className}"><p>${message}</p></div>`;
    }

    /**
     * Check for purchase success in URL
     */
    function checkPurchaseSuccess() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('purchase') === 'success') {
            // Auto-register instance after purchase
            if (currentEmail && currentInstanceId) {
                setTimeout(() => {
                    registerInstance();
                }, 1000);
            }
        }
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        init();
        checkPurchaseSuccess();
    });

})();

