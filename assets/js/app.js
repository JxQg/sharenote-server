// Import modules
import { initTOC } from './modules/toc.js';
import { initDocTree } from './modules/doc-tree.js';
import { initCallouts } from './modules/callout.js';
import { initTheme } from './modules/theme.js';

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize all modules
    initTOC();
    await initDocTree();
    initCallouts();
    
    // Initialize code copy buttons
    document.querySelectorAll('.markdown-body pre').forEach(pre => {
        const button = document.createElement('button');
        button.className = 'copy-code-button';
        button.textContent = '复制';
        button.addEventListener('click', () => {
            const code = pre.querySelector('code');
            if (code) {
                navigator.clipboard.writeText(code.innerText.trim()).then(() => {
                    const originalText = button.textContent;
                    button.textContent = '已复制！';
                    setTimeout(() => {
                        button.textContent = originalText;
                    }, 2000);
                });
            }
        });
        pre.appendChild(button);
    });

    // Initialize mobile navigation
    const mobileNavToggle = document.getElementById('mobile-nav-toggle');
    const navSidebar = document.querySelector('.nav-sidebar');
    const mobileNavBackdrop = document.querySelector('.mobile-nav-backdrop');
    
    if (mobileNavToggle && navSidebar) {
        mobileNavToggle.addEventListener('click', () => {
            navSidebar.classList.toggle('show');
            if (mobileNavBackdrop) {
                mobileNavBackdrop.classList.toggle('show');
            }
        });
    }
    
    if (mobileNavBackdrop) {
        mobileNavBackdrop.addEventListener('click', () => {
            navSidebar.classList.remove('show');
            mobileNavBackdrop.classList.remove('show');
        });
    }
    
    // Handle links in mobile nav
    document.querySelectorAll('.nav-sidebar a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navSidebar.classList.remove('show');
                mobileNavBackdrop.classList.remove('show');
            }
        });
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            navSidebar?.classList.remove('show');
            mobileNavBackdrop?.classList.remove('show');
        }
        
        // Handle responsive classes
        const mobileClasses = ['is-mobile', 'is-phone'];
        if (window.innerWidth <= 768) {
            document.body.classList.add(...mobileClasses);
        } else {
            document.body.classList.remove(...mobileClasses);
        }
    });
    
    // Initialize Lucide icons
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

    // Add anchors to headings
    document.querySelectorAll('.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4').forEach(heading => {
        if (!heading.id) {
            heading.id = heading.textContent.toLowerCase().replace(/\s+/g, '-');
        }
        const anchor = document.createElement('a');
        anchor.className = 'heading-anchor';
        anchor.href = `#${heading.id}`;
        anchor.textContent = '#';
        heading.appendChild(anchor);
    });

    // Initialize scroll animations
    initScrollAnimations();

    // Initialize scroll progress indicator
    initScrollProgress();

    // Initialize back to top button
    initBackToTop();

    // 初始化主题（跟随系统偏好或用户上次选择）
    initTheme();
});

// ========== 滚动动画功能 ==========
function initScrollAnimations() {
    // 添加标记类，表示 JS 已加载，可以启用滚动动画
    document.documentElement.classList.add('scroll-animations-enabled');

    // 创建 Intersection Observer
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                // 动画完成后取消观察以提升性能
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // 观察所有需要动画的元素
    const animatedElements = document.querySelectorAll(
        '.markdown-body h1, .markdown-body h2, .markdown-body h3, ' +
        '.markdown-body p, .markdown-body ul, .markdown-body ol, ' +
        '.markdown-body blockquote, .markdown-body pre, ' +
        '.markdown-body table, .markdown-body .callout'
    );

    animatedElements.forEach(el => {
        observer.observe(el);
    });
}

// ========== 滚动进度指示器 ==========
function initScrollProgress() {
    // 创建进度条元素
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    progressBar.innerHTML = '<div class="scroll-progress-bar"></div>';
    document.body.appendChild(progressBar);

    const progressBarFill = progressBar.querySelector('.scroll-progress-bar');

    // 更新进度条
    function updateProgress() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;

        progressBarFill.style.width = `${Math.min(scrollPercent, 100)}%`;
    }

    // 监听滚动事件
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateProgress();
                ticking = false;
            });
            ticking = true;
        }
    });

    // 初始化
    updateProgress();
}

// ========== 返回顶部按钮 ==========
function initBackToTop() {
    // 创建返回顶部按钮
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.innerHTML = '↑';
    backToTopBtn.setAttribute('aria-label', '返回顶部');
    document.body.appendChild(backToTopBtn);

    // 显示/隐藏按钮
    function toggleBackToTop() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('show');
        } else {
            backToTopBtn.classList.remove('show');
        }
    }

    // 点击返回顶部
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // 监听滚动
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                toggleBackToTop();
                ticking = false;
            });
            ticking = true;
        }
    });

    // 初始化
    toggleBackToTop();
}
