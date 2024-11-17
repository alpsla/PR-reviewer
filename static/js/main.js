document.addEventListener('DOMContentLoaded', function() {
    // Only initialize form handling if we're on the review form page
    const prForm = document.getElementById('prForm');
    const submitBtn = prForm?.querySelector('button[type="submit"]');
    const spinner = submitBtn?.querySelector('.spinner-border');
    
    if (prForm && submitBtn && spinner) {
        prForm.addEventListener('submit', function(e) {
            // Show loading state
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            // Keep the spinner and add text after it
            submitBtn.innerHTML = '';
            submitBtn.appendChild(spinner);
            submitBtn.appendChild(document.createTextNode(' Analyzing...'));
        });
    }

    // Initialize tooltips if they exist on the page
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
