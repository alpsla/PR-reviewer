document.addEventListener('DOMContentLoaded', function() {
    // Form handling
    const prForm = document.getElementById('prForm');
    if (prForm) {
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
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Helper function to get main container
function getMainContainer() {
    return document.querySelector('.container');
}

// Save review function
async function saveReview() {
    const container = getMainContainer();
    const reviewContent = document.querySelector('.review-content');
    if (!container || !reviewContent) return;
    
    try {
        const response = await fetch('/save-review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Review saved successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to save review');
        }
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// Post comment function
async function postComment() {
    const container = getMainContainer();
    const reviewContent = document.querySelector('.review-content');
    if (!container || !reviewContent) return;
    
    try {
        const response = await fetch('/post-comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Comment posted successfully!', 'success');
            
            // If comment URL is available, offer to open it
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
        showAlert(error.message, 'error');
    }
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    const container = getMainContainer();
    if (!container) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${type === 'error' ? '<i class="bi bi-exclamation-triangle-fill me-2"></i>' : 
          type === 'success' ? '<i class="bi bi-check-circle-fill me-2"></i>' : 
          '<i class="bi bi-info-circle-fill me-2"></i>'}
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode === container) {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode === container) {
                    alertDiv.remove();
                }
            }, 150);
        }
    }, 5000);
}
