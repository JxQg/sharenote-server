import { initCallouts } from './modules/callout.js';
import { initThemeToggle } from './modules/theme.js';
import { initTOC } from './modules/toc.js';
import { generateTOC } from './modules/toc.js';
import { initDocTree } from './modules/tree.js';

function initDocument() {
    // 初始化所有模块
    initCallouts();
    initThemeToggle();
    initTOC();

    // 初始化复制代码按钮
    document.querySelectorAll('button.copy-code-button')
        .forEach(buttonEl => {
            buttonEl.addEventListener('click', () => {
                const codeEl = buttonEl.parentElement.querySelector('code');
                navigator.clipboard.writeText(codeEl.innerText.trim()).then();
            });
        });

    // 响应式移动端类名处理
    function toggleMobileClasses() {
        const mobileClasses = ['is-mobile', 'is-phone'];
        if (window.innerWidth <= 768) {
            document.body.classList.add(...mobileClasses);
        } else {
            document.body.classList.remove(...mobileClasses);
        }
    }

    toggleMobileClasses();
    window.addEventListener('resize', toggleMobileClasses);

    // 加载Lucide图标
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://unpkg.com/lucide@0.287.0/dist/umd/lucide.min.js';
    script.onload = () => {
        lucide.createIcons({
            attrs: {
                class: ['callout-icon']
            },
            nameAttr: 'data-share-note-lucide'
        });
    };
    document.head.appendChild(script);
}

window.initDocument = initDocument;

document.addEventListener('DOMContentLoaded', () => {
    // 初始化文档导航树
    initDocTree();
    
    // 生成文档目录
    const content = document.querySelector('.markdown-body');
    if (content) {
        const toc = generateTOC(content);
        const tocContainer = document.getElementById('toc');
        if (tocContainer) {
            tocContainer.innerHTML = toc;
        }
    }
    
    // 移动端目录切换按钮
    const tocToggle = document.createElement('button');
    tocToggle.className = 'mobile-nav-toggle toc-toggle';
    tocToggle.innerHTML = '<span>目录</span>';
    document.body.appendChild(tocToggle);
    
    tocToggle.addEventListener('click', () => {
        const tocSidebar = document.querySelector('.toc-sidebar');
        if (tocSidebar) {
            tocSidebar.classList.toggle('show');
        }
    });
    
    // 响应式布局处理
    function handleResize() {
        const navSidebar = document.querySelector('.nav-sidebar');
        const tocSidebar = document.querySelector('.toc-sidebar');
        
        if (window.innerWidth > 768) {
            navSidebar?.classList.remove('show');
            tocSidebar?.classList.remove('show');
        }
    }
    
    window.addEventListener('resize', handleResize);
    handleResize(); // 初始化时执行一次
    
    // 暗色模式切换
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    function handleColorSchemeChange(e) {
        document.body.classList.toggle('dark-theme', e.matches);
    }
    
    prefersDarkScheme.addListener(handleColorSchemeChange);
    handleColorSchemeChange(prefersDarkScheme);
});
