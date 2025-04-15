export function initThemeToggle() {
    const themeToggleEl = document.querySelector('#theme-mode-toggle');
    themeToggleEl?.addEventListener('click', () => {
        document.body.classList.toggle('theme-dark');
        document.body.classList.toggle('theme-light');
    });
}