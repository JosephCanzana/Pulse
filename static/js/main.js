
// Reusable Confirmation Modal
const confirmModal = document.getElementById("confirm-modal");
const confirmTitle = document.getElementById("confirm-modal-title");
const confirmMessage = document.getElementById("confirm-modal-message");
const confirmForm = document.getElementById("confirm-modal-form");
const confirmCancel = document.getElementById("confirm-modal-cancel");

/**
 * Opens the modal
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {string} action - Form action URL
 * @param {string} [method="post"] - Form method
 */
function openConfirmModal(title, message, action, method = "post") {
    confirmTitle.textContent = title;
    confirmMessage.textContent = message;
    confirmForm.action = action;
    confirmForm.method = method;
    confirmModal.classList.remove("hidden");
}

// Close modal
confirmCancel.addEventListener("click", () => {
    confirmModal.classList.add("hidden");
});

// Optional: close modal if clicking outside content
confirmModal.addEventListener("click", (e) => {
    if (e.target === confirmModal) {
        confirmModal.classList.add("hidden");
    }
});

/**
 * Shows reusable modal for form confirmation
 * @param {Event} e - Form submit event
 * @param {HTMLFormElement} form - The form being submitted
 */
function openConfirmFormModal(e, form) {
    e.preventDefault(); // Stop immediate submission

    // Optional: customize title and message dynamically
    openConfirmModal(
        'Confirm Account Activation',
        'Are you sure you want to activate your account?',
        form.action,
        form.method
    );

    // Update the modal form to submit this form's data
    const modalForm = document.getElementById('confirm-modal-form');
    
    // Clone the original form fields into modal form
    modalForm.innerHTML = '';
    for (let element of form.elements) {
        if (element.name && !element.disabled) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = element.name;
            input.value = element.value;
            modalForm.appendChild(input);
        }
    }

    // Add Confirm button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.id = 'confirm-modal-submit';
    submitBtn.className = 'px-6 py-3 rounded-lg bg-[var(--clr-primary)] text-white hover:bg-[var(--clr-secondary)] transition-colors font-medium';
    submitBtn.textContent = 'Confirm';
    modalForm.appendChild(submitBtn);

    return false; // Prevent normal submission
}
