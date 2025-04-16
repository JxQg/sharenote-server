function getCurrentPath() {
    return window.location.pathname.replace(/^\//, '').replace(/\.html$/, '') || 'index';
}

function createTreeNode(item) {
    const li = document.createElement('li');
    li.className = 'tree-item';
    
    if (item.isFolder) {
        li.classList.add('tree-folder');
        
        const folderHeader = document.createElement('div');
        folderHeader.className = 'folder-header';
        
        const toggle = document.createElement('span');
        toggle.className = 'folder-toggle';
        toggle.innerHTML = `
            <svg class="folder-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m9 18 6-6-6-6"/>
            </svg>
        `;
        
        // 移除文件夹图标，只保留箭头和标题
        
        const title = document.createElement('span');
        title.className = 'folder-title';
        title.textContent = item.title;
        
        folderHeader.appendChild(toggle);
        folderHeader.appendChild(title);
        li.appendChild(folderHeader);
        
        if (item.children && item.children.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'tree-list';
            item.children.forEach(child => {
                ul.appendChild(createTreeNode(child));
            });
            li.appendChild(ul);
        }
        
        // 添加折叠/展开功能
        folderHeader.addEventListener('click', (e) => {
            if (e.target.closest('.tree-item-link')) return;
            li.classList.toggle('collapsed');
        });
    } else {
        const link = document.createElement('a');
        link.href = item.url;
        link.className = 'tree-item-link';
        
        // 移除文档图标，只保留标题文字
        
        const title = document.createElement('span');
        title.className = 'doc-title';
        title.textContent = item.title;
        
        link.appendChild(title);
        li.appendChild(link);
        
        // 高亮当前页面
        if (window.location.pathname === item.url) {
            li.classList.add('active');
            // 展开父文件夹
            let parent = li.parentElement;
            while (parent) {
                if (parent.classList.contains('tree-list')) {
                    parent.parentElement.classList.remove('collapsed');
                }
                parent = parent.parentElement;
            }
        }
    }
    
    return li;
}

async function fetchDocTree() {
    try {
        const response = await fetch('/api/doc-tree');
        if (!response.ok) throw new Error('Failed to fetch doc tree');
        return await response.json();
    } catch (error) {
        console.error('Error fetching doc tree:', error);
        return [];
    }
}

export async function initDocTree() {
    const container = document.getElementById('doc-tree');
    if (!container) return;
    
    const data = await fetchDocTree();
    if (!data || !data.length) {
        container.innerHTML = '<div class="tree-empty">No documents found</div>';
        return;
    }
    
    const ul = document.createElement('ul');
    ul.className = 'tree-list root';
    data.forEach(item => {
        ul.appendChild(createTreeNode(item));
    });
    
    container.innerHTML = '';
    container.appendChild(ul);
    
    // 初始化时展开包含当前页面的文件夹
    const currentPath = window.location.pathname;
    if (currentPath !== '/') {
        document.querySelectorAll('.tree-item-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                let parent = link.parentElement;
                while (parent) {
                    if (parent.classList.contains('tree-folder')) {
                        parent.classList.remove('collapsed');
                    }
                    parent = parent.parentElement;
                }
            }
        });
    }
}

function highlightCurrentPage() {
    const currentPath = getCurrentPath();
    const links = document.querySelectorAll('#doc-tree .doc-link');
    
    links.forEach(link => {
        if (link.getAttribute('href').replace(/^\//, '').replace(/\.html$/, '') === currentPath) {
            link.classList.add('active');
        }
    });
}

function expandCurrentSection() {
    const activeLink = document.querySelector('#doc-tree .active');
    if (activeLink) {
        let parent = activeLink.parentElement;
        while (parent) {
            if (parent.tagName === 'DETAILS') {
                parent.setAttribute('open', '');
            }
            parent = parent.parentElement;
        }
    }
}

function initMobileNav() {
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const navSidebar = document.querySelector('.nav-sidebar');
    
    mobileNavToggle?.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            navSidebar.style.display = 
                navSidebar.style.display === 'block' ? 'none' : 'block';
        }
    });
}

function handleWindowResize() {
    const navSidebar = document.querySelector('.nav-sidebar');
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            navSidebar.style.display = 'block';
        }
    });
}