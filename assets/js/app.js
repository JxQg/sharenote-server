// Import modules
import { initTOC } from './modules/toc.js';
import { initDocTree } from './modules/doc-tree.js';
import { initCallouts } from './modules/callout.js';

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

    // 应用明亮模式
    document.documentElement.dataset.theme = 'light';
    document.documentElement.classList.add('theme-light');
    document.documentElement.classList.remove('theme-dark');
});
