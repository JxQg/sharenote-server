// 明亮模式固定设置
export class ThemeManager {
    constructor() {
        this.applyLightTheme();
    }

    applyLightTheme() {
        document.documentElement.dataset.theme = 'light';
        document.documentElement.classList.add('theme-light');
        document.documentElement.classList.remove('theme-dark');
    }
}

// 导出初始化函数，供主应用调用
export function initTheme() {
    return new ThemeManager();
}