const CALLOUT_TYPES = {
    note: {
        icon: 'info',
        color: 'var(--theme-accent)',
        background: 'rgba(141, 70, 231, 0.1)'
    },
    tip: {
        icon: 'lightbulb',
        color: '#0ea5e9',
        background: 'rgba(14, 165, 233, 0.1)'
    },
    warning: {
        icon: 'alert-triangle',
        color: '#f59e0b',
        background: 'rgba(245, 158, 11, 0.1)'
    },
    error: {
        icon: 'x-octagon',
        color: '#ef4444',
        background: 'rgba(239, 68, 68, 0.1)'
    },
    danger: {
        icon: 'zap',
        color: '#ef4444',
        background: 'rgba(239, 68, 68, 0.1)'
    },
    success: {
        icon: 'check-circle',
        color: '#10b981',
        background: 'rgba(16, 185, 129, 0.1)'
    }
};

export function initCallouts() {
    // 查找所有blockquote元素
    document.querySelectorAll('.markdown-body blockquote').forEach(quote => {
        const firstLine = quote.textContent.trim().split('\n')[0].toLowerCase();
        
        // 检查是否包含callout标记
        for (const [type, config] of Object.entries(CALLOUT_TYPES)) {
            if (firstLine.startsWith(`[!${type}]`)) {
                // 移除标记并设置样式
                quote.innerHTML = quote.innerHTML.replace(
                    new RegExp(`\\[!${type}\\]`, 'i'),
                    `<div class="callout-icon-container">
                        <i data-share-note-lucide="${config.icon}"></i>
                    </div>`
                );
                
                // 添加callout类和样式
                quote.classList.add('callout', `callout-${type}`);
                quote.style.borderLeftColor = config.color;
                quote.style.backgroundColor = config.background;
                
                // 创建标题容器
                const titleContainer = document.createElement('div');
                titleContainer.className = 'callout-title';
                titleContainer.style.color = config.color;
                
                // 包装内容
                const content = quote.innerHTML;
                quote.innerHTML = '';
                quote.appendChild(titleContainer);
                const contentDiv = document.createElement('div');
                contentDiv.className = 'callout-content';
                contentDiv.innerHTML = content;
                quote.appendChild(contentDiv);
                
                break;
            }
        }
    });

    document.querySelectorAll('.callout.is-collapsible > .callout-title')
        .forEach(titleEl => {
            titleEl.addEventListener('click', () => {
                const calloutEl = titleEl.parentElement;
                calloutEl.classList.toggle('is-collapsed');
                titleEl.querySelector('.callout-fold').classList.toggle('is-collapsed');
                calloutEl.querySelector('.callout-content').style.display = 
                    calloutEl.classList.contains('is-collapsed') ? 'none' : '';
            });
        });

    document.querySelectorAll('.list-collapse-indicator')
        .forEach(collapseEl => {
            collapseEl.addEventListener('click', () => {
                collapseEl.classList.toggle('is-collapsed');
                collapseEl.parentElement.classList.toggle('is-collapsed');
            });
        });
}