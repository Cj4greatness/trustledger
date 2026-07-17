// Theme handling
function initTheme() {
    const saved = localStorage.getItem('trustledger-theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateToggleIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('trustledger-theme', next);
    updateToggleIcon(next);
}

function updateToggleIcon(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = theme === 'dark' ? '☀' : '☾';
}

// Profile dropdown
function toggleProfileMenu() {
    document.getElementById('profileDropdown').classList.toggle('show');
}

document.addEventListener('click', function(e) {
    const menu = document.getElementById('profileDropdown');
    const btn = document.getElementById('profileBtn');
    if (menu && btn && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('show');
    }
});

initTheme();
