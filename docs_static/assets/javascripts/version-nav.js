(function () {
  function init() {
    const menu = document.querySelector('.wy-nav-side .wy-menu-vertical');
    if (!menu) {
      return;
    }

    const latestLabel = 'SpatialDDS 1.4';

    menu.querySelectorAll('p.caption').forEach((caption) => {
      const list = caption.nextElementSibling;
      if (!list || list.tagName !== 'UL') {
        return;
      }

      const span = caption.querySelector('.caption-text');
      if (!span) {
        return;
      }

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'version-toggle';
      button.innerHTML = span.innerHTML;

      const containsCurrent = Boolean(list.querySelector('.current'));
      const isLatest = span.textContent && span.textContent.trim() === latestLabel;
      const expanded = containsCurrent || isLatest;

      button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      if (!expanded) {
        list.classList.add('version-collapsed');
      }

      button.addEventListener('click', () => {
        const isOpen = button.getAttribute('aria-expanded') === 'true';
        const nextState = !isOpen;
        button.setAttribute('aria-expanded', nextState ? 'true' : 'false');
        list.classList.toggle('version-collapsed', !nextState);
      });

      span.replaceWith(button);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
