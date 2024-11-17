document.addEventListener('DOMContentLoaded', function() {
    const prForm = document.getElementById('prForm');
    if (!prForm) return;  // Exit if form not found
    
    const submitBtn = prForm.querySelector('button[type="submit"]');
    if (!submitBtn) return;  // Exit if button not found
    
    const spinner = submitBtn.querySelector('.spinner-border');
    if (!spinner) return;  // Exit if spinner not found
    
    prForm.addEventListener('submit', function(e) {
        // Show loading state
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');
        submitBtn.textContent = ' Analyzing...';
        submitBtn.prepend(spinner);
    });
});
