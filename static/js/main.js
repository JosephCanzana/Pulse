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


/**
 * Shows reusable modal for non-form confirmation actions
 * e.g., restore data, delete, reset, etc.
 * @param {string} title - Modal title
 * @param {string} message - Modal message
 * @param {function} onConfirm - Function to execute on confirm
 */
function openConfirmActionModal(title, message, onConfirm) {
  openConfirmModal(title, message); // open existing modal structure

  const modalForm = document.getElementById('confirm-modal-form');
  modalForm.innerHTML = ''; // clear previous content

  // Create the Confirm button
  const confirmBtn = document.createElement('button');
  confirmBtn.type = 'button';
  confirmBtn.className =
    'px-6 py-3 rounded-lg bg-[var(--clr-primary)] text-white hover:bg-[var(--clr-secondary)] transition-colors font-medium';
  confirmBtn.textContent = 'Confirm';

  // Attach click handler
  confirmBtn.addEventListener('click', () => {
    confirmModal.classList.add('hidden'); // close modal
    if (typeof onConfirm === 'function') onConfirm();
  });

  // Append Confirm button
  modalForm.appendChild(confirmBtn);
}


/**
 * Reusable auto-save form handler
 * @param {string} formSelector - CSS selector of the form (e.g., '#studentForm')
 * @param {string} storageKey - Unique sessionStorage key name
 */
function autoSaveForm(formSelector, storageKey) {
  const form = document.querySelector(formSelector);
  if (!form) return console.warn(`Form ${formSelector} not found`);

  // Restore saved data if available
  const saved = sessionStorage.getItem(storageKey);
  if (saved) {
    const data = JSON.parse(saved);
    for (const [name, value] of Object.entries(data)) {
      const input = form.querySelector(`[name="${name}"]`);
      if (input) input.value = value;
    }
  }

  // Auto-save inputs on change
  form.addEventListener('input', () => {
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.name) data[el.name] = el.value;
    });
    sessionStorage.setItem(storageKey, JSON.stringify(data));
  });
}



/**
 * Dynamically creates and shows a flash modal (client-side only)
 * @param {string} message - The message to display
 * @param {'success'|'error'|'warning'|'info'} [type='info'] - Flash category
 */
function showFlashMessage(message, type = 'info') {
  const titles = {
    success: 'Success',
    error: 'Something went wrong',
    warning: 'Warning',
    info: 'Information'
  };

  const colors = {
    success: 'var(--clr-success)',
    error: 'var(--clr-error)',
    warning: 'var(--clr-warning)',
    info: 'var(--clr-info)'
  };

  const color = colors[type] || colors.info;
  const title = titles[type] || titles.info;

  // Remove any existing flash modal first
  const existing = document.getElementById('flashModal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'flashModal';
  modal.className = 'fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-50 animate-fadeIn';

  modal.innerHTML = `
    <div
      class="relative p-8 max-w-sm w-full rounded-3xl border shadow-2xl transition-all duration-300 overflow-hidden"
      style="background: var(--clr-glass-light); border-color: var(--clr-glass-border); backdrop-filter: blur(20px) saturate(180%);"
    >
      <div class="absolute inset-0 rounded-3xl opacity-20 blur-3xl pointer-events-none"
           style="background: radial-gradient(circle at top left, ${color}, transparent 70%);"></div>

      <div class="relative z-10 text-center space-y-4 flex flex-col items-center">
        <h1 class="text-2xl font-semibold tracking-tight drop-shadow-sm" style="color: ${color};">${title}</h1>
        <p class="text-sm leading-relaxed max-w-xs" style="color: var(--clr-txt-secondary);">${message}</p>
      </div>

      <button id="flashOkBtn"
        class="mt-8 w-full px-6 py-2.5 rounded-xl font-medium border shadow-md transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2"
        style="border-color: ${color}40; background: ${color}20; color: var(--clr-txt-primary); box-shadow: 0 0 8px ${color}25;">
        OK
      </button>

      <div class="absolute inset-0 rounded-3xl opacity-10 blur-3xl pointer-events-none" style="background: ${color};"></div>
    </div>
  `;

  document.body.appendChild(modal);

  const btn = modal.querySelector('#flashOkBtn');
  btn.addEventListener('click', () => {
    modal.classList.add('opacity-0', 'pointer-events-none', 'transition', 'duration-200');
    setTimeout(() => modal.remove(), 250);
  });

  // Close when clicking outside
  modal.addEventListener('click', e => {
    if (e.target === modal) {
      modal.classList.add('opacity-0');
      setTimeout(() => modal.remove(), 250);
    }
  });
}



/**
 * Restore function for manual trigger
 * (Used by the Restore Last Entry button)
 */
function restoreLastEntry(formSelector, storageKey) {
  const form = document.querySelector(formSelector);
  const saved = sessionStorage.getItem(storageKey);

  openConfirmActionModal(
    'Restore Form',
    'Are you sure you want to restore the last saved form data?',
    () => {
      const prevURL = document.referrer;
      const currentURL = window.location.href;

      try {
        const prev = new URL(prevURL);
        const current = new URL(currentURL);

        // ✅ Only go back if same path (same route)
        if (prev.pathname === current.pathname) {
          showFlashMessage('Form data successfully restored.', 'success');
          window.history.back();
        } else {
          showFlashMessage('Form not found.', 'error');
        }
      } catch {
        // if referrer is empty or invalid
        showFlashMessage('Form not found.', 'error');
      }
    }
  );
}


