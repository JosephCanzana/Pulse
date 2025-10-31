//Sidebar
const menuBtn = document.getElementById('menu-btn');
const sidebarExpand = document.getElementById('sidebar-expand');
const sidebarCollapsed = document.getElementById('sidebar-collapsed');
const mainContent = document.getElementById('wrapper');

if (menuBtn && sidebarExpand && sidebarCollapsed && mainContent) {
    // For maintaining the sidebar open even if the page is refreshed 
    // NAVBAR EXPANDED
    if (localStorage.getItem('sidebarOpen') === 'true') {
        sidebarExpand.classList.remove('-translate-x-full');
        sidebarCollapsed.classList.add('translate-y-full');
        mainContent.classList.add('md:ml-60');
    }
    
    // NAVBAR COLLAPSED
    menuBtn.addEventListener('click', () => {
        const isCurrentlyOpen = !sidebarExpand.classList.contains('-translate-x-full');

        if (isCurrentlyOpen) {
            // Closing sidebar
            sidebarExpand.classList.add('-translate-x-full');
            sidebarCollapsed.classList.remove('translate-y-full'); 
            mainContent.classList.remove('md:ml-60');
            localStorage.setItem('sidebarOpen', false);
        } else {
            // Opening sidebar
            sidebarExpand.classList.remove('-translate-x-full');
            sidebarCollapsed.classList.add('translate-y-full');
            mainContent.classList.add('md:ml-60');
            localStorage.setItem('sidebarOpen', true);
        }
    });
}

//Theme change
const themeToggles = document.querySelectorAll('.theme-toggle');
const root = document.documentElement;

// === Load saved theme from localStorage ===
const savedTheme = localStorage.getItem('theme');

// Default to light mode if nothing is saved
if (savedTheme === 'dark') {
    root.setAttribute('data-theme', 'dark');
    themeToggles.forEach(btn => {
        btn.querySelector('.material-symbols-outlined').textContent = 'dark_mode';
    });
} else {
    root.removeAttribute('data-theme');
    themeToggles.forEach(btn => {
        btn.querySelector('.material-symbols-outlined').textContent = 'light_mode';
    });
}

// === Toggle theme when any button is clicked ===
themeToggles.forEach(btn => {
    btn.addEventListener('click', () => {
        const isDark = root.getAttribute('data-theme') === 'dark';
        
        if (isDark) {
            // Switch to light mode
            root.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            themeToggles.forEach(b => {
                b.querySelector('.material-symbols-outlined').textContent = 'light_mode';
            });
        } else {
            // Switch to dark mode
            root.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            themeToggles.forEach(b => {
                b.querySelector('.material-symbols-outlined').textContent = 'dark_mode';
            });
        }
    });
});

// Mobile Sidebar Toggle
const mobileMenuBtn = document.getElementById('mobile-menu-btn');

if (mobileMenuBtn && sidebarExpand && sidebarCollapsed) {
  mobileMenuBtn.addEventListener('click', () => {
    const isOpen = !sidebarExpand.classList.contains('-translate-x-full');

    if (isOpen) {
      sidebarExpand.classList.add('-translate-x-full');
      sidebarCollapsed.classList.remove('translate-y-full');
      localStorage.setItem('sidebarOpen', false);
    } else {
      sidebarExpand.classList.remove('-translate-x-full');
      sidebarCollapsed.classList.add('translate-y-full');
      localStorage.setItem('sidebarOpen', true);
    }
  });
}

