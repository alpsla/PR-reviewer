document.addEventListener('DOMContentLoaded', function() {
    const prForm = document.getElementById('prForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = submitBtn.querySelector('.spinner-border');

    if (prForm) {
        prForm.addEventListener('submit', function(e) {
            // Show loading state
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            submitBtn.textContent = ' Analyzing...';
            submitBtn.prepend(spinner);
        });
    }
});
