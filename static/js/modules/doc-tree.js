export function initDocTree() {
    generateDocTree();
    initMobileNav();
    handleWindowResize();
}

function generateDocTree() {
    fetch('/api/doc-tree')
        .then(response => response.json())
        .then(data => {
            const tree = buildTreeHTML(data);
            document.getElementById('doc-tree').innerHTML = tree;
        })
        .catch(error => console.error('Error loading doc tree:', error));
}

function buildTreeHTML(data) {
    let html = '<ul>';
    data.forEach(item => {
        html += `
            <li>
                <a href="${item.url}">${item.title}</a>
                ${item.children ? buildTreeHTML(item.children) : ''}
            </li>
        `;
    });
    html += '</ul>';
    return html;
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