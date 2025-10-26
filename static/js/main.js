// Show password
document.addEventListener("DOMContentLoaded", () => {
  const passwordFields = document.querySelectorAll('input[data-toggle="password"]');

  passwordFields.forEach(field => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `
      absolute right-3 top-1/2 -translate-y-1/2
      text-[var(--clr-txt-secondary)] hover:text-[var(--clr-primary)]
      transition duration-200
    `;
    btn.setAttribute("aria-label", "Show password");

    // simple lock & unlock icons
    const locked = `
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        class="icon-lock block">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
      </svg>
    `;
    const unlocked = `
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        class="icon-unlock hidden">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
        <path d="M7 11V7a5 5 0 0 1 9 0"></path>
      </svg>
    `;

    btn.innerHTML = locked + unlocked;
    field.parentElement.appendChild(btn);

    btn.addEventListener("click", () => {
      const isHidden = field.type === "password";
      field.type = isHidden ? "text" : "password";

      btn.querySelector(".icon-lock").classList.toggle("hidden", isHidden);
      btn.querySelector(".icon-unlock").classList.toggle("hidden", !isHidden);
      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
  });
});

// Flash modal
document.addEventListener("DOMContentLoaded", () => {
  const flashModal = document.getElementById("flashModal");
  const flashOkBtn = document.getElementById("flashOkBtn");

  if (flashModal && flashOkBtn) {
    const closeModal = () => {
      flashModal.classList.add("opacity-0");
      // Wait for animation to complete before removing
      setTimeout(() => {
        flashModal.remove();
      }, 200);
    };

    // Close modal when OK is clicked
    flashOkBtn.addEventListener("click", closeModal);

    // Close when clicking outside modal
    flashModal.addEventListener("click", (e) => {
      if (e.target === flashModal) {
        closeModal();
      }
    });

  }
});


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
function openConfirmFormModal(e, form, title, message) {
    e.preventDefault(); // Stop immediate submission

    // Optional: customize title and message dynamically
    openConfirmModal(
        title,
        message,
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
