// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    initializeTooltips();
});

// Initialize form handling
function initializeForm() {
    const prForm = document.querySelector('#prForm');
    if (!prForm) {
        console.debug('PR form not found - likely on a different page');
        return;
    }
    
    const submitBtn = prForm.querySelector('button[type="submit"]');
    const spinner = submitBtn?.querySelector('.spinner-border');
    
    if (submitBtn && spinner) {
        prForm.addEventListener('submit', function() {
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            submitBtn.innerHTML = '';
            submitBtn.appendChild(spinner);
            submitBtn.appendChild(document.createTextNode(' Analyzing...'));
        });
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            if (tooltipTriggerEl) {
                new bootstrap.Tooltip(tooltipTriggerEl);
            }
        });
    }
}

// Save review function
async function saveReview() {
    const saveBtn = document.querySelector('.btn-success');
    if (!saveBtn) return;
    
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Saving...';
    
    try {
        const response = await fetch('/save-review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}) // Empty object as required by Flask
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Review saved successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to save review');
        }
    } catch (error) {
        showAlert('Failed to save review: ' + error.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-save me-2"></i>Save';
    }
}

// Post comment function
async function postComment() {
    const commentBtn = document.querySelector('.btn-primary');
    if (!commentBtn) return;
    
    commentBtn.disabled = true;
    commentBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Posting...';
    
    try {
        const response = await fetch('/post-comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}) // Empty object as required by Flask
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Comment posted successfully!', 'success');
            if (data.comment_url) {
                setTimeout(() => {
                    if (confirm('Would you like to view your comment on GitHub?')) {
                        window.open(data.comment_url, '_blank');
                    }
                }, 1000);
            }
        } else {
            throw new Error(data.error || 'Failed to post comment');
        }
    } catch (error) {
        showAlert('Failed to post comment: ' + error.message, 'error');
    } finally {
        commentBtn.disabled = false;
        commentBtn.innerHTML = '<i class="bi bi-chat-text me-2"></i>Comment';
    }
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.style.zIndex = '1050'; // Ensure alert is visible
    alertDiv.innerHTML = `
        ${type === 'error' ? '<i class="bi bi-exclamation-triangle-fill me-2"></i>' : 
          type === 'success' ? '<i class="bi bi-check-circle-fill me-2"></i>' : 
          '<i class="bi bi-info-circle-fill me-2"></i>'}
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (!container) {
        console.debug('Cannot show alert: container not found');
        return;
    }
    
    // Insert alert at the beginning of the container
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode === container) {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === container) {
                    container.removeChild(alertDiv);
                }
            }, 150);
        }
    }, 5000);
}
