// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    initializeTooltips();
    initializeTheme();
});

// Initialize form handling
function initializeForm() {
    const prForm = document.getElementById('prForm');
    if (!prForm) {
        console.debug('No PR form found on current page');
        return;
    }
    
    const submitBtn = prForm.querySelector('button[type="submit"]');
    const spinner = submitBtn?.querySelector('.spinner-border');
    const buttonText = submitBtn?.querySelector('.button-text');
    
    if (submitBtn && spinner && buttonText) {
        prForm.addEventListener('submit', function(e) {
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            buttonText.textContent = 'Analyzing...';
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

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const html = document.documentElement;
    const body = document.body;
    const themeIcon = document.querySelector('#themeToggle i');
    
    html.setAttribute('data-bs-theme', savedTheme);
    
    // Update body classes
    if (savedTheme === 'light') {
        body.classList.remove('bg-dark');
        body.classList.add('bg-light');
        // Show moon icon in light mode
        if (themeIcon) {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-fill');
        }
    } else {
        body.classList.remove('bg-light');
        body.classList.add('bg-dark');
        // Show sun icon in dark mode
        if (themeIcon) {
            themeIcon.classList.remove('bi-moon-fill');
            themeIcon.classList.add('bi-sun-fill');
        }
    }
}

// Toggle theme function
function toggleTheme() {
    const html = document.documentElement;
    const body = document.body;
    const themeIcon = document.querySelector('#themeToggle i');
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Update theme
    html.setAttribute('data-bs-theme', newTheme);
    
    // Update body classes
    if (newTheme === 'light') {
        body.classList.remove('bg-dark');
        body.classList.add('bg-light');
        // Show moon icon in light mode
        themeIcon.classList.remove('bi-sun-fill');
        themeIcon.classList.add('bi-moon-fill');
    } else {
        body.classList.remove('bg-light');
        body.classList.add('bg-dark');
        // Show sun icon in dark mode
        themeIcon.classList.remove('bi-moon-fill');
        themeIcon.classList.add('bi-sun-fill');
    }
    
    // Store preference
    localStorage.setItem('theme', newTheme);
}

// Show export modal
function showExportModal() {
    const modal = new bootstrap.Modal(document.getElementById('exportModal'));
    modal.show();
}

// Copy to clipboard function
async function copyToClipboard() {
    const reviewContent = document.querySelector('.review-content')?.innerText;
    if (!reviewContent) return;
    
    try {
        await navigator.clipboard.writeText(reviewContent);
        showAlert('Review copied to clipboard!', 'success');
    } catch (error) {
        showAlert('Failed to copy: ' + error.message, 'error');
    }
}

// Download as markdown function
function downloadMarkdown() {
    const reviewContent = document.querySelector('.review-content')?.innerText;
    if (!reviewContent) return;
    
    const blob = new Blob([reviewContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pr-review.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showAlert('Review downloaded as Markdown!', 'success');
}

// Save review function with clipboard functionality
async function saveReview() {
    const saveBtn = document.querySelector('.btn-success');
    if (!saveBtn) return;
    
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Saving...';
    
    try {
        // Copy review content to clipboard
        const reviewContent = document.querySelector('.review-content')?.innerText;
        if (reviewContent) {
            await navigator.clipboard.writeText(reviewContent);
        }

        const response = await fetch('/save-review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Review saved successfully and copied to clipboard!', 'success');
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
            body: JSON.stringify({})
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
    alertDiv.style.zIndex = '1050';
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
    
    container.insertBefore(alertDiv, container.firstChild);
    
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