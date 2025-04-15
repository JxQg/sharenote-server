export function initTOC() {
    const headers = document.querySelectorAll('.markdown-preview-section h1, .markdown-preview-section h2, .markdown-preview-section h3, .markdown-preview-section h4');
    const tocContainer = document.getElementById('toc');
    const tocList = document.createElement('ul');
    tocList.className = 'toc-list';

    headers.forEach((header, index) => {
        const id = `header-${index}`;
        header.id = id;

        const li = document.createElement('li');
        li.className = `toc-item toc-${header.tagName.toLowerCase()}`;

        const a = document.createElement('a');
        a.href = `#${id}`;
        a.textContent = header.textContent;
        a.onclick = (e) => {
            e.preventDefault();
            header.scrollIntoView({behavior: 'smooth'});
            if (window.innerWidth <= 768) {
                document.querySelector('.toc-container').classList.remove('show');
            }
        };

        li.appendChild(a);
        tocList.appendChild(li);
    });

    tocContainer.appendChild(tocList);

    // Mobile TOC Toggle
    const tocToggle = document.querySelector('.toc-toggle');
    const tocContainerEl = document.querySelector('.toc-container');

    tocToggle?.addEventListener('click', () => {
        tocContainerEl.classList.toggle('show');
    });
}

export function generateTOC(contentSelector) {
    const content = document.querySelector(contentSelector);
    const headings = content.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let toc = '<ul class="toc-list">';
    let lastLevel = 0;
    
    headings.forEach((heading, index) => {
        const level = parseInt(heading.tagName.charAt(1));
        const title = heading.textContent;
        const id = `heading-${index}`;
        heading.id = id;
        
        while (level > lastLevel) {
            toc += '<ul>';
            lastLevel++;
        }
        
        while (level < lastLevel) {
            toc += '</ul>';
            lastLevel--;
        }
        
        toc += `
            <li>
                <a href="#${id}" class="toc-link">${title}</a>
            </li>
        `;
    });
    
    // 关闭所有剩余的ul标签
    while (lastLevel > 0) {
        toc += '</ul>';
        lastLevel--;
    }
    
    return toc;
}