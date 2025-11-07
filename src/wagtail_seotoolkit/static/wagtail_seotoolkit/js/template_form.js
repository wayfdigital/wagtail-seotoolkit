/**
 * JavaScript for SEO Template Form (Create/Edit)
 * Handles form submission, placeholder cloud, and dynamic field updates
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('template-form');
    const contentTypeSelect = document.getElementById('id_content_type');
    const placeholderCloud = document.getElementById('placeholder-cloud');
    const templateContent = document.getElementById('id_template_content');
    
    // Set up placeholder cloud click handling
    if (placeholderCloud && templateContent) {
        setupPlaceholderCloud(placeholderCloud, templateContent);
    }
    
    // Handle content type changes - fetch new placeholders
    if (contentTypeSelect && placeholderCloud) {
        contentTypeSelect.addEventListener('change', async function() {
            const contentTypeId = this.value || null;
            
            // Show loading state
            placeholderCloud.innerHTML = '<span class="placeholder-badge" style="opacity: 0.5;">Loading...</span>';
            
            // Fetch new placeholders
            const placeholders = await fetchPlaceholders(contentTypeId);
            
            // Render new badges
            renderPlaceholderBadges(placeholderCloud, placeholders);
            
            // No need to re-setup click handling - event delegation handles it automatically
        });
    }
    
    // Handle form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = form.querySelector('button[type="submit"]');
            const originalText = submitButton.querySelector('em').textContent;
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.classList.add('button-longrunning-active');
            
            // Get form data
            const formData = new FormData(form);
            
            // Submit form
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showWagtailMessage(data.message, 'success');
                    
                    // Redirect to template list after a short delay
                    setTimeout(() => {
                        window.location.href = form.dataset.redirectUrl;
                    }, 1000);
                } else {
                    showWagtailMessage(data.error || 'Failed to save template', 'error');
                    submitButton.disabled = false;
                    submitButton.classList.remove('button-longrunning-active');
                    submitButton.querySelector('em').textContent = originalText;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showWagtailMessage('An error occurred while saving the template', 'error');
                submitButton.disabled = false;
                submitButton.classList.remove('button-longrunning-active');
                submitButton.querySelector('em').textContent = originalText;
            });
        });
    }
});
