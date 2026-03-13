const STORAGE_KEY = 'sharenote-theme';

export class ThemeManager {
    constructor() {
        this._theme = this._resolveInitialTheme();
        this._apply(this._theme);
    }

    _resolveInitialTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === 'dark' || saved === 'light') return saved;
        // 跟随系统偏好
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    _apply(theme) {
        document.documentElement.dataset.theme = theme;
        document.documentElement.classList.toggle('theme-dark', theme === 'dark');
        document.documentElement.classList.toggle('theme-light', theme === 'light');
    }

    toggle() {
        this._theme = this._theme === 'dark' ? 'light' : 'dark';
        this._apply(this._theme);
        localStorage.setItem(STORAGE_KEY, this._theme);
    }

    get current() {
        return this._theme;
    }
}

export function initTheme() {
    const manager = new ThemeManager();

    // 绑定页面上所有带 data-theme-toggle 属性的按钮
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
        btn.addEventListener('click', () => manager.toggle());
    });

    // 监听系统主题变化（仅当用户未手动设置时跟随系统）
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem(STORAGE_KEY)) {
                manager._theme = e.matches ? 'dark' : 'light';
                manager._apply(manager._theme);
            }
        });
    }

    return manager;
}
