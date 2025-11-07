/**
 * JavaScript for SEO Template List page
 * Handles template deletion with confirmation
 */

document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-template');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const templateId = this.dataset.templateId;
            const templateName = this.dataset.templateName;
            
            if (!confirm(`Are you sure you want to delete the template "${templateName}"? This action cannot be undone.`)) {
                return;
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<svg class="icon icon-spinner"><use href="#icon-spinner"></use></svg>';
            
            // Make delete request
            fetch(`/admin/seo-toolkit/templates/${templateId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    showWagtailMessage(data.message, 'success');
                    
                    // Remove the row from the table
                    const row = button.closest('tr');
                    row.style.opacity = '0';
                    setTimeout(() => row.remove(), 300);
                } else {
                    showWagtailMessage(data.error || 'Failed to delete template', 'error');
                    button.disabled = false;
                    button.innerHTML = '<svg class="icon icon-bin"><use href="#icon-bin"></use></svg>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showWagtailMessage('An error occurred while deleting the template', 'error');
                button.disabled = false;
                button.innerHTML = '<svg class="icon icon-bin"><use href="#icon-bin"></use></svg>';
            });
        });
    });
});

