const CALLOUT_TYPES = {
    note:       { icon: 'info',           color: '#0ea5e9' },
    info:       { icon: 'info',           color: '#0ea5e9' },
    tip:        { icon: 'lightbulb',      color: '#8d46e7' },
    hint:       { icon: 'lightbulb',      color: '#8d46e7' },
    abstract:   { icon: 'clipboard-list', color: '#06b6d4' },
    summary:    { icon: 'clipboard-list', color: '#06b6d4' },
    tldr:       { icon: 'clipboard-list', color: '#06b6d4' },
    todo:       { icon: 'check-square',   color: '#3b82f6' },
    success:    { icon: 'check-circle',   color: '#10b981' },
    check:      { icon: 'check-circle',   color: '#10b981' },
    done:       { icon: 'check-circle',   color: '#10b981' },
    question:   { icon: 'help-circle',    color: '#f59e0b' },
    help:       { icon: 'help-circle',    color: '#f59e0b' },
    faq:        { icon: 'help-circle',    color: '#f59e0b' },
    warning:    { icon: 'alert-triangle', color: '#f97316' },
    caution:    { icon: 'alert-triangle', color: '#f97316' },
    attention:  { icon: 'alert-triangle', color: '#f97316' },
    important:  { icon: 'alert-triangle', color: '#f97316' },
    error:      { icon: 'x-octagon',      color: '#ef4444' },
    danger:     { icon: 'zap',            color: '#ef4444' },
    failure:    { icon: 'x-circle',       color: '#ef4444' },
    fail:       { icon: 'x-circle',       color: '#ef4444' },
    missing:    { icon: 'x-circle',       color: '#ef4444' },
    bug:        { icon: 'bug',            color: '#dc2626' },
    example:    { icon: 'list',           color: '#8b5cf6' },
    quote:      { icon: 'quote',          color: '#6b7280' },
    cite:       { icon: 'quote',          color: '#6b7280' },
};

/**
 * 从第一行文本中解析 callout 信息
 * 格式：[!type] 标题文字  或  [!type]+ 标题  或  [!type]- 标题
 * 返回 { type, title, collapsible, collapsed } 或 null
 */
function parseCalloutMarker(firstLine) {
    const match = firstLine.match(/^\[!(\w+)\]([+-]?)(.*)$/i);
    if (!match) return null;
    const type = match[1].toLowerCase();
    if (!CALLOUT_TYPES[type]) return null;
    const modifier = match[2];
    const titleSuffix = match[3].trim();
    return {
        type,
        title: titleSuffix || type.charAt(0).toUpperCase() + type.slice(1),
        collapsible: modifier !== '',
        collapsed: modifier === '-',
    };
}

export function initCallouts() {
    document.querySelectorAll('.markdown-body blockquote').forEach(quote => {
        // 找到第一个文本节点或 <p> 中的第一行
        const firstP = quote.querySelector('p');
        const rawText = firstP ? firstP.textContent : quote.textContent;
        const firstLine = rawText.trim().split('\n')[0].trim();

        const info = parseCalloutMarker(firstLine);
        if (!info) return;

        const config = CALLOUT_TYPES[info.type];

        // 构建 callout DOM
        quote.classList.add('callout', `callout-${info.type}`);
        if (info.collapsible) quote.classList.add('is-collapsible');
        if (info.collapsed) quote.classList.add('is-collapsed');

        // 标题行
        const titleEl = document.createElement('div');
        titleEl.className = 'callout-title';
        titleEl.style.color = config.color;
        titleEl.innerHTML = `
            <span class="callout-icon-container"><i data-share-note-lucide="${config.icon}"></i></span>
            <span class="callout-title-text">${info.title}</span>
            ${info.collapsible ? '<span class="callout-fold">' + (info.collapsed ? '▶' : '▼') + '</span>' : ''}
        `;

        // 移除原始标记文字（第一个 <p> 的第一行）
        if (firstP) {
            const lines = firstP.innerHTML.split(/<br\s*\/?>/i);
            // 删除第一行（含 [!type] 标记）
            lines.shift();
            if (lines.length) {
                firstP.innerHTML = lines.join('<br>');
            } else {
                firstP.remove();
            }
        }

        // 内容容器
        const contentEl = document.createElement('div');
        contentEl.className = 'callout-content';
        if (info.collapsed) contentEl.style.display = 'none';

        // 把 quote 现有内容移入 contentEl
        while (quote.firstChild) {
            contentEl.appendChild(quote.firstChild);
        }

        quote.appendChild(titleEl);
        quote.appendChild(contentEl);

        // 折叠交互
        if (info.collapsible) {
            titleEl.style.cursor = 'pointer';
            titleEl.addEventListener('click', () => {
                const isCollapsed = quote.classList.toggle('is-collapsed');
                contentEl.style.display = isCollapsed ? 'none' : '';
                const foldIcon = titleEl.querySelector('.callout-fold');
                if (foldIcon) foldIcon.textContent = isCollapsed ? '▶' : '▼';
            });
        }
    });

    // 支持已有 .is-collapsible 的 callout（由后端渲染）
    document.querySelectorAll('.callout.is-collapsible > .callout-title')
        .forEach(titleEl => {
            if (titleEl.dataset.bound) return;
            titleEl.dataset.bound = '1';
            titleEl.addEventListener('click', () => {
                const calloutEl = titleEl.parentElement;
                const isCollapsed = calloutEl.classList.toggle('is-collapsed');
                const foldEl = titleEl.querySelector('.callout-fold');
                if (foldEl) foldEl.classList.toggle('is-collapsed', isCollapsed);
                const content = calloutEl.querySelector('.callout-content');
                if (content) content.style.display = isCollapsed ? 'none' : '';
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
