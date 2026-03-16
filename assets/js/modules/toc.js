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
    list.className = `toc-list depth-${level}`;

    items.forEach(item => {
        const li = document.createElement('li');
        li.className = `toc-item level-${level}`;

        const link = document.createElement('a');
        link.href = `#${item.id}`;
        link.className = `toc-link level-${level}`;  // 添加level类到链接
        
        const titleSpan = document.createElement('span');
        titleSpan.className = 'toc-title';
        titleSpan.textContent = item.title;
        link.appendChild(titleSpan);
        
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.getElementById(item.id);
            if (target) {
                // 使用 getBoundingClientRect 获取准确位置
                const targetRect = target.getBoundingClientRect();
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const top = targetRect.top + scrollTop - TOC_CONFIG.scrollOffset;

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
            sublist.className = `toc-sublist depth-${level + 1}`;
            li.appendChild(sublist);
        }

        list.appendChild(li);
    });

    return list;
}

// 缓存变量，避免每次滚动重新查询 DOM
let _headingPositions = [];
let _tocLinks = [];
let _tocContainer = null;

function buildHeadingPositions() {
    const headings = Array.from(document.querySelectorAll(TOC_CONFIG.headingSelector))
        .filter(h => !h.closest(TOC_CONFIG.ignoreSelector));
    _headingPositions = headings.map(heading => {
        const rect = heading.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        return {
            id: heading.id,
            top: rect.top + scrollTop - TOC_CONFIG.scrollOffset - 10
        };
    });
}

function updateActiveHeading() {
    if (!_headingPositions.length) return;

    const scrollPosition = window.scrollY;
    let currentHeading = _headingPositions[0];

    for (const heading of _headingPositions) {
        if (scrollPosition >= heading.top) {
            currentHeading = heading;
        } else {
            break;
        }
    }

    _tocLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentHeading.id}`) {
            link.classList.add('active');
            if (_tocContainer) {
                const linkRect = link.getBoundingClientRect();
                const containerRect = _tocContainer.getBoundingClientRect();
                if (linkRect.top < containerRect.top || linkRect.bottom > containerRect.bottom) {
                    link.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

    // 缓存 DOM 引用，供滚动回调使用
    _tocLinks = Array.from(document.querySelectorAll('.toc-link'));
    _tocContainer = document.querySelector('.toc-sidebar');
    buildHeadingPositions();

    // 窗口尺寸变化时重建位置缓存
    window.addEventListener('resize', buildHeadingPositions);

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