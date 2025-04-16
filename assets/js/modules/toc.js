// 用于生成目录的配置
const TOC_CONFIG = {
    contentSelector: '.markdown-body',
    headingSelector: 'h1, h2, h3, h4',
    ignoreSelector: '.no-toc',
    scrollOffset: 100,
    scrollSmooth: true,
    scrollSmoothDuration: 400,
};

function getHeadingLevel(heading) {
    return parseInt(heading.tagName.charAt(1), 10);
}

function slugify(text) {
    return text.toString().toLowerCase()
        .replace(/\s+/g, '-')           // 替换空格为 -
        .replace(/[^\w\-]+/g, '')       // 删除所有非单词字符
        .replace(/\-\-+/g, '-')         // 替换多个 - 为单个 -
        .replace(/^-+/, '')             // 删除开头的 -
        .replace(/-+$/, '');            // 删除末尾的 -
}

function createTocTree(headings) {
    const toc = [];
    const stack = [{ level: 0, children: toc }];

    headings.forEach(heading => {
        const level = getHeadingLevel(heading);
        const title = heading.textContent;
        const id = heading.id || slugify(title);
        heading.id = id;  // 确保标题有ID

        const node = {
            title,
            id,
            level,
            children: []
        };

        // 找到合适的父节点
        while (stack.length > 1 && stack[stack.length - 1].level >= level) {
            stack.pop();
        }

        stack[stack.length - 1].children.push(node);
        stack.push(node);
    });

    return toc;
}

function renderTocList(items, level = 1) {
    if (!items.length) return '';

    const list = document.createElement('ul');
    list.className = 'toc-list';

    items.forEach(item => {
        const li = document.createElement('li');
        li.className = `toc-item level-${level}`;

        const link = document.createElement('a');
        link.href = `#${item.id}`;
        link.className = 'toc-link';
        link.textContent = item.title;
        
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.getElementById(item.id);
            if (target) {
                const top = target.offsetTop - TOC_CONFIG.scrollOffset;
                window.scrollTo({
                    top,
                    behavior: TOC_CONFIG.scrollSmooth ? 'smooth' : 'auto'
                });
                // 更新URL，但不滚动
                history.pushState(null, '', `#${item.id}`);
            }
        });

        li.appendChild(link);

        if (item.children.length) {
            const sublist = renderTocList(item.children, level + 1);
            sublist.className = 'toc-sublist';
            li.appendChild(sublist);
        }

        list.appendChild(li);
    });

    return list;
}

function updateActiveHeading() {
    const headings = Array.from(document.querySelectorAll(TOC_CONFIG.headingSelector))
        .filter(h => !h.closest(TOC_CONFIG.ignoreSelector));
    
    // 提前退出如果没有标题
    if (!headings.length) return;

    // 计算每个标题的位置
    const headingPositions = headings.map(heading => ({
        id: heading.id,
        top: heading.offsetTop - TOC_CONFIG.scrollOffset - 10
    }));

    // 找到当前视窗中最接近顶部的标题
    const scrollPosition = window.scrollY;
    let currentHeading = headingPositions[0];

    for (const heading of headingPositions) {
        if (scrollPosition >= heading.top) {
            currentHeading = heading;
        } else {
            break;
        }
    }

    // 更新活动状态
    document.querySelectorAll('.toc-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentHeading.id}`) {
            link.classList.add('active');
            // 确保活动项在视图中
            const tocContainer = document.querySelector('.toc-sidebar');
            if (tocContainer) {
                const linkRect = link.getBoundingClientRect();
                const containerRect = tocContainer.getBoundingClientRect();
                
                if (linkRect.top < containerRect.top || linkRect.bottom > containerRect.bottom) {
                    link.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            }
        }
    });
}

export function initTOC() {
    const content = document.querySelector(TOC_CONFIG.contentSelector);
    if (!content) return;

    const headings = Array.from(content.querySelectorAll(TOC_CONFIG.headingSelector))
        .filter(h => !h.closest(TOC_CONFIG.ignoreSelector));

    if (headings.length === 0) {
        const toc = document.querySelector('.toc-sidebar');
        if (toc) {
            toc.style.display = 'none';
        }
        return;
    }

    const tocTree = createTocTree(headings);
    const tocContainer = document.getElementById('toc');
    if (tocContainer) {
        tocContainer.appendChild(renderTocList(tocTree));
    }

    // 监听滚动事件来更新活动标题
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            window.cancelAnimationFrame(scrollTimeout);
        }
        scrollTimeout = window.requestAnimationFrame(() => {
            updateActiveHeading();
        });
    });

    // 初始化活动标题
    updateActiveHeading();

    // 如果URL中有锚点，滚动到对应位置
    if (window.location.hash) {
        const target = document.getElementById(window.location.hash.slice(1));
        if (target) {
            setTimeout(() => {
                const top = target.offsetTop - TOC_CONFIG.scrollOffset;
                window.scrollTo({
                    top,
                    behavior: TOC_CONFIG.scrollSmooth ? 'smooth' : 'auto'
                });
            }, 100);
        }
    }
}