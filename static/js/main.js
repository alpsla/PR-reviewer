document.addEventListener('DOMContentLoaded', function() {
    const prForm = document.querySelector('#prForm');
    if (!prForm) return; // Exit if form doesn't exist
    
    const submitBtn = prForm.querySelector('button[type="submit"]');
    const spinner = submitBtn?.querySelector('.spinner-border');
    
    if (submitBtn && spinner) {
        prForm.addEventListener('submit', function(e) {
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            submitBtn.innerHTML = '';
            submitBtn.appendChild(spinner);
            submitBtn.appendChild(document.createTextNode(' Analyzing...'));
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
