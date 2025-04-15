export function initCallouts() {
    document.querySelectorAll('.callout.is-collapsible > .callout-title')
        .forEach(titleEl => {
            titleEl.addEventListener('click', () => {
                const calloutEl = titleEl.parentElement;
                calloutEl.classList.toggle('is-collapsed');
                titleEl.querySelector('.callout-fold').classList.toggle('is-collapsed');
                calloutEl.querySelector('.callout-content').style.display = 
                    calloutEl.classList.contains('is-collapsed') ? 'none' : '';
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