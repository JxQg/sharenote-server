export function initDocTree() {
    // 初始化文档树
    fetch('/api/doc-tree')
        .then(response => response.json())
        .then(data => {
            renderTree(data);
            initTreeInteractions();
        })
        .catch(error => console.error('Error loading doc tree:', error));
}

function renderTree(nodes, parentEl = document.getElementById('doc-tree')) {
    const ul = document.createElement('ul');
    ul.className = 'tree-list';
    
    nodes.forEach(node => {
        const li = document.createElement('li');
        
        if (node.isFolder) {
            li.className = 'folder-item';
            li.innerHTML = `
                <span class="folder-icon">▶</span>
                <span class="folder-name">${node.title}</span>
                <div class="folder-children"></div>
            `;
            
            if (node.children && node.children.length > 0) {
                renderTree(node.children, li.querySelector('.folder-children'));
            }
        } else {
            li.className = 'file-item';
            li.innerHTML = `<a href="${node.url}">${node.title}</a>`;
        }
        
        ul.appendChild(li);
    });
    
    parentEl.appendChild(ul);
}

function initTreeInteractions() {
    // 文件夹展开/折叠功能
    document.querySelectorAll('.folder-item').forEach(folder => {
        folder.addEventListener('click', (e) => {
            if (e.target.closest('.file-item')) return;
            
            e.stopPropagation();
            folder.classList.toggle('folder-open');
            
            const children = folder.querySelector('.folder-children');
            if (children) {
                if (folder.classList.contains('folder-open')) {
                    children.style.height = children.scrollHeight + 'px';
                } else {
                    children.style.height = '0';
                }
            }
        });
    });
    
    // 移动端导航切换
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const navSidebar = document.querySelector('.nav-sidebar');
    
    if (mobileNavToggle && navSidebar) {
        mobileNavToggle.addEventListener('click', () => {
            navSidebar.classList.toggle('show');
        });
        
        // 点击内容区域关闭导航
        document.querySelector('.content').addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navSidebar.classList.remove('show');
            }
        });
    }
    
    // 记住文件夹展开状态
    const saveTreeState = () => {
        const state = {};
        document.querySelectorAll('.folder-item').forEach(folder => {
            const path = getFolderPath(folder);
            state[path] = folder.classList.contains('folder-open');
        });
        localStorage.setItem('treeState', JSON.stringify(state));
    };
    
    // 恢复文件夹展开状态
    const restoreTreeState = () => {
        try {
            const state = JSON.parse(localStorage.getItem('treeState')) || {};
            document.querySelectorAll('.folder-item').forEach(folder => {
                const path = getFolderPath(folder);
                if (state[path]) {
                    folder.classList.add('folder-open');
                    const children = folder.querySelector('.folder-children');
                    if (children) {
                        children.style.height = children.scrollHeight + 'px';
                    }
                }
            });
        } catch (e) {
            console.error('Error restoring tree state:', e);
        }
    };
    
    // 获取文件夹路径
    function getFolderPath(folder) {
        const path = [];
        let current = folder;
        while (current && !current.matches('#doc-tree')) {
            if (current.classList.contains('folder-item')) {
                path.unshift(current.querySelector('.folder-name').textContent);
            }
            current = current.parentElement.closest('.folder-item');
        }
        return path.join('/');
    }
    
    // 监听文件夹状态变化
    document.querySelectorAll('.folder-item').forEach(folder => {
        folder.addEventListener('click', saveTreeState);
    });
    
    // 初始化时恢复状态
    restoreTreeState();
}