/**
 * Hash views + left nav. Research children stay hidden until Research is opened.
 */
(function () {
  const PAGE = document.body?.dataset?.plmPage || 'index';
  const RESEARCH_PAGES = new Set(['stats', 'hamsters', 'chinese-oss']);

  function nav() {
    return document.querySelector('.plm-nav');
  }

  function setView(id) {
    document.querySelectorAll('.plm-view').forEach((el) => {
      el.hidden = el.id !== 'view-' + id;
    });
  }

  function markActive(view, researchOpen) {
    const root = nav();
    if (!root) return;
    root.querySelectorAll('[data-view], [data-research]').forEach((el) => {
      el.classList.remove('is-on');
    });
    const researchItem = root.querySelector('.plm-nav-item[data-nav="research"]');
    const researchBtn = root.querySelector('[data-view="research"]');
    if (researchItem) researchItem.classList.toggle('is-open', Boolean(researchOpen));
    if (researchBtn) researchBtn.setAttribute('aria-expanded', researchOpen ? 'true' : 'false');

    if (researchOpen && RESEARCH_PAGES.has(PAGE)) {
      const child = root.querySelector(`[data-research="${PAGE}"]`);
      if (child) child.classList.add('is-on');
      const btn = root.querySelector('[data-view="research"]');
      if (btn) btn.classList.add('is-on');
      return;
    }
    const link = root.querySelector(`[data-view="${view}"]`);
    if (link) link.classList.add('is-on');
  }

  function parseHash() {
    const raw = (location.hash || '').replace(/^#/, '').toLowerCase();
    if (raw === 'about' || raw === 'manifesto') return 'manifesto';
    if (raw === 'history' || raw === 'registry' || raw === 'setups') return raw;
    return 'setups';
  }

  function apply() {
    if (PAGE !== 'index') {
      markActive(null, true);
      return;
    }
    const view = parseHash();
    setView(view);
    const researchOpen = Boolean(nav()?.querySelector('.plm-nav-item[data-nav="research"]')?.classList.contains('is-open'));
    markActive(view, researchOpen);
  }

  function go(view) {
    if (PAGE !== 'index') {
      location.href = 'index.html#' + view;
      return;
    }
    const next = '#' + view;
    if (location.hash === next) apply();
    else location.hash = next;
  }

  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-research]')) return;

    const btn = e.target.closest('[data-view]');
    if (!btn || !nav()?.contains(btn)) return;
    e.preventDefault();
    const view = btn.getAttribute('data-view');
    if (view === 'research') {
      const item = btn.closest('.plm-nav-item');
      const open = !item?.classList.contains('is-open');
      item?.classList.toggle('is-open', open);
      btn.classList.toggle('is-on', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      return;
    }
    go(view);
  });

  window.addEventListener('hashchange', apply);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }
})();
