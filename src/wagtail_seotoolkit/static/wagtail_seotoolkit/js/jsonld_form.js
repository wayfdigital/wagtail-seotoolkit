/**
 * JSON-LD Schema Form JavaScript
 * 
 * Handles form submission and placeholder functionality for schema templates.
 */

(function () {
    'use strict';

    // Show copy feedback on the whole badge wrapper
    function showCopyFeedback(wrapper) {
        wrapper.style.backgroundColor = '#22c55e';
        wrapper.style.borderColor = '#22c55e';
        var mainBtn = wrapper.querySelector('.placeholder-badge-main');
        if (mainBtn) mainBtn.style.borderColor = '#22c55e';
        wrapper.querySelectorAll('button').forEach(function (btn) {
            btn.style.color = 'white';
        });

        setTimeout(function () {
            wrapper.style.backgroundColor = '';
            wrapper.style.borderColor = '';
            if (mainBtn) mainBtn.style.borderColor = '';
            wrapper.querySelectorAll('button').forEach(function (btn) {
                btn.style.color = '';
            });
        }, 1000);
    }

    // Handle placeholder badge clicks (copy to clipboard)
    document.querySelectorAll('.placeholder-badge-main').forEach(function (badge) {
        badge.addEventListener('click', function (e) {
            e.preventDefault();
            const wrapper = this.closest('.placeholder-badge-wrapper');
            const placeholder = this.getAttribute('data-placeholder');
            const text = '{' + placeholder + '}';

            // Copy to clipboard
            navigator.clipboard.writeText(text).then(function () {
                showCopyFeedback(wrapper);
            }).catch(function (err) {
                console.error('Failed to copy:', err);
            });
        });
    });

    // Handle truncation button clicks (copy with truncation)
    document.querySelectorAll('.placeholder-truncate-btn').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const wrapper = this.closest('.placeholder-badge-wrapper');
            const placeholder = this.getAttribute('data-placeholder');

            // Prompt for truncation length
            const length = prompt(
                'Truncate "' + placeholder + '" to how many characters?\n\n' +
                'Example: entering 60 will create {' + placeholder + '[:60]}'
            );

            if (length === null) {
                return; // User cancelled
            }

            const parsedLength = parseInt(length, 10);

            if (isNaN(parsedLength) || parsedLength <= 0) {
                alert('Please enter a valid positive number');
                return;
            }

            const text = '{' + placeholder + '[:' + parsedLength + ']}';

            // Copy to clipboard
            navigator.clipboard.writeText(text).then(function () {
                showCopyFeedback(wrapper);
            }).catch(function (err) {
                console.error('Failed to copy:', err);
            });
        });
    });

    // Handle schema form submission
    const schemaForm = document.getElementById('jsonld-schema-form');
    if (schemaForm) {
        schemaForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitButton = schemaForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<em>Saving...</em>';
            submitButton.disabled = true;

            const formData = new FormData(schemaForm);
            const redirectUrl = schemaForm.getAttribute('data-redirect-url');

            fetch(schemaForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data.success) {
                        // Show success message
                        showMessage('success', data.message || 'Saved successfully!');

                        // Redirect after a short delay
                        setTimeout(function () {
                            if (data.redirect_url) {
                                window.location.href = data.redirect_url;
                            } else if (redirectUrl) {
                                window.location.href = redirectUrl;
                            }
                        }, 500);
                    } else {
                        showMessage('error', data.error || 'An error occurred');
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                })
                .catch(function (error) {
                    showMessage('error', 'An error occurred: ' + error.message);
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                });
        });
    }

    // Handle page JSON-LD form submission
    const pageForm = document.getElementById('page-jsonld-form');
    if (pageForm) {
        pageForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitButton = pageForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<em>Saving...</em>';
            submitButton.disabled = true;

            const formData = new FormData(pageForm);
            const redirectUrl = pageForm.getAttribute('data-redirect-url');

            fetch(pageForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data.success) {
                        showMessage('success', data.message || 'Saved successfully!');

                        setTimeout(function () {
                            if (redirectUrl) {
                                window.location.href = redirectUrl;
                            }
                        }, 500);
                    } else {
                        showMessage('error', data.error || 'An error occurred');
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                })
                .catch(function (error) {
                    showMessage('error', 'An error occurred: ' + error.message);
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                });
        });
    }

    // Handle site-wide schema form submissions
    document.querySelectorAll('.site-wide-schema-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitButton = form.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = 'Saving...';
            submitButton.disabled = true;

            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data.success) {
                        showMessage('success', data.message || 'Saved successfully!');
                    } else {
                        showMessage('error', data.error || 'An error occurred');
                    }
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                })
                .catch(function (error) {
                    showMessage('error', 'An error occurred: ' + error.message);
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                });
        });
    });

    // Update placeholders when content type changes
    const contentTypeSelect = document.getElementById('id_content_type');
    if (contentTypeSelect) {
        contentTypeSelect.addEventListener('change', function () {
            const contentTypeId = this.value;
            updatePlaceholders(contentTypeId);
        });
    }

    function updatePlaceholders(contentTypeId) {
        const url = '/admin/api/jsonld/placeholders/' + (contentTypeId ? '?content_type_id=' + contentTypeId : '');

        fetch(url)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success && data.placeholders) {
                    const cloud = document.getElementById('placeholder-cloud');
                    if (cloud) {
                        cloud.innerHTML = '';
                        data.placeholders.forEach(function (placeholder) {
                            const wrapper = document.createElement('span');
                            wrapper.className = 'placeholder-badge-wrapper placeholder-badge--' + placeholder.type;

                            const button = document.createElement('button');
                            button.type = 'button';
                            button.className = 'placeholder-badge-main';
                            button.setAttribute('data-placeholder', placeholder.name);
                            button.setAttribute('title', 'Click to copy {' + placeholder.name + '}');
                            button.textContent = placeholder.label;

                            // Add click handler
                            button.addEventListener('click', function (e) {
                                e.preventDefault();
                                const text = '{' + placeholder.name + '}';
                                navigator.clipboard.writeText(text).then(function () {
                                    const originalText = button.textContent;
                                    button.textContent = 'Copied!';
                                    button.style.backgroundColor = '#22c55e';
                                    button.style.color = 'white';

                                    setTimeout(function () {
                                        button.textContent = originalText;
                                        button.style.backgroundColor = '';
                                        button.style.color = '';
                                    }, 1000);
                                });
                            });

                            wrapper.appendChild(button);
                            cloud.appendChild(wrapper);
                        });
                    }
                }
            })
            .catch(function (error) {
                console.error('Failed to load placeholders:', error);
            });
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

    // Expose showMessage globally for use by other scripts
    window.showJSONLDMessage = showMessage;


})();
