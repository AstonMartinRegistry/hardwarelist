/**
 * Offline open-source registry: providers left, models / config on the right.
 */
(function (global) {
  let providers = [];
  let query = '';
  let openId = '';
  let selected = null;
  const pageCache = new Map();

  function esc(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function slug(name) {
    return String(name || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  function groups() {
    const q = query.trim().toLowerCase();
    const tokens = q.split(/\s+/).filter(Boolean);
    return providers
      .map((p) => {
        const models = tokens.length
          ? (p.models || []).filter((m) => {
              const blob = [p.name, m.name, m.id].join(' ').toLowerCase();
              return tokens.every((t) => blob.includes(t));
            })
          : p.models || [];
        return { name: p.name, id: slug(p.name), models };
      })
      .filter((p) => p.models.length);
  }

  function currentGroup() {
    const gs = groups();
    if (!gs.length) return null;
    return gs.find((g) => g.id === openId) || gs[0];
  }

  function renderProviders() {
    const host = document.getElementById('registry-list');
    const countEl = document.getElementById('registry-count');
    if (!host) return;
    const gs = groups();
    const nModels = providers.reduce((n, p) => n + (p.models || []).length, 0);
    const shown = gs.reduce((n, p) => n + p.models.length, 0);
    if (countEl) {
      countEl.textContent =
        shown === nModels
          ? `${nModels} models`
          : `${shown} of ${nModels} models`;
    }
    if (!providers.length) {
      host.innerHTML = '<p class="registry-empty">Loading models…</p>';
      return;
    }
    if (!gs.length) {
      host.innerHTML = '<p class="registry-empty">No models match that search.</p>';
      return;
    }
    if (!openId || !gs.some((g) => g.id === openId)) openId = gs[0].id;
    host.innerHTML = gs
      .map((p) => {
        const on = p.id === openId;
        return `<button type="button" class="registry-provider-btn${on ? ' is-on' : ''}" data-provider="${esc(p.id)}" aria-current="${on ? 'true' : 'false'}">
          <span class="reg-name">${esc(p.name)}</span>
          <span class="reg-n">${p.models.length}</span>
        </button>`;
      })
      .join('');
  }

  function renderModels() {
    const pane = document.getElementById('registry-models');
    const detail = document.getElementById('registry-detail');
    if (!pane) return;
    if (selected) {
      pane.hidden = true;
      return;
    }
    pane.hidden = false;
    if (detail) detail.hidden = true;
    const g = currentGroup();
    if (!g) {
      pane.innerHTML = '<p class="registry-empty">Select a provider.</p>';
      return;
    }
    pane.innerHTML =
      `<h2 class="registry-pane-title">${esc(g.name)}</h2>` +
      `<ul class="registry-models">${g.models
        .map(
          (m) =>
            `<li><button type="button" class="registry-model-btn" data-model="${esc(m.id)}">${esc(m.name)}</button></li>`,
        )
        .join('')}</ul>`;
  }

  function renderDetail(page) {
    const pane = document.getElementById('registry-models');
    const detail = document.getElementById('registry-detail');
    if (!detail) return;
    if (pane) pane.hidden = true;
    detail.hidden = false;
    const paras = String(page.description || '')
      .split(/\n\n+/)
      .filter(Boolean)
      .map((p) => `<p>${esc(p)}</p>`)
      .join('');
    const cfg = page.config
      ? `<h3 class="registry-config-label">config.json</h3><pre class="registry-config">${esc(JSON.stringify(page.config, null, 2))}</pre>`
      : '<p class="registry-empty">No config.json on file for this model.</p>';
    const hf = page.hf_url
      ? `<p><a class="registry-hf" href="${esc(page.hf_url)}" target="_blank" rel="noopener">${esc(page.hf_url.replace('https://', ''))}</a></p>`
      : '';
    const paper = page.paper && page.paper.url
      ? `<p><a class="registry-hf" href="${esc(page.paper.url)}" target="_blank" rel="noopener">${esc(page.paper.title || page.paper.url)}</a></p>`
      : '';
    detail.innerHTML = `
      <button type="button" class="registry-back" data-registry-back>← ${esc(page.provider || 'Models')}</button>
      <h2 class="registry-model-title">${esc(page.name)}</h2>
      ${hf}
      ${paper}
      ${cfg}
      <div class="registry-note">${paras}</div>
    `;
  }

  function render() {
    renderProviders();
    if (selected) {
      const cached = pageCache.get(selected);
      if (cached) renderDetail(cached);
      return;
    }
    renderModels();
  }

  async function openModel(id) {
    selected = id;
    const pane = document.getElementById('registry-models');
    const detail = document.getElementById('registry-detail');
    if (pane) pane.hidden = true;
    if (detail) {
      detail.hidden = false;
      detail.innerHTML = '<p class="registry-empty">Loading config.json…</p>';
    }
    if (!pageCache.has(id)) {
      try {
        const res = await fetch('/data/model-pages/' + encodeURIComponent(id) + '.json', {
          cache: 'no-store',
        });
        if (!res.ok) throw new Error('missing');
        pageCache.set(id, await res.json());
      } catch {
        pageCache.set(id, {
          id,
          name: id,
          provider: currentGroup() ? currentGroup().name : 'Registry',
          description: 'No local config.json snapshot for this model yet.',
          config: null,
        });
      }
    }
    if (selected === id) renderDetail(pageCache.get(id));
  }

  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-registry-back]')) {
      selected = null;
      render();
      return;
    }
    const modelBtn = e.target.closest('.registry-model-btn');
    if (modelBtn) {
      openModel(modelBtn.getAttribute('data-model') || '');
      return;
    }
    const btn = e.target.closest('.registry-provider-btn');
    if (!btn) return;
    openId = btn.getAttribute('data-provider') || '';
    selected = null;
    render();
  });

  document.addEventListener('input', (e) => {
    if (e.target && e.target.id === 'registry-search') {
      query = e.target.value || '';
      selected = null;
      openId = '';
      render();
    }
  });

  async function load() {
    const host = document.getElementById('registry-list');
    if (host && !providers.length) {
      host.innerHTML = '<p class="registry-empty">Loading models…</p>';
    }
    try {
      const res = await fetch('/data/open-models.json', { cache: 'no-store' });
      const data = await res.json();
      if (!res.ok || !data || !Array.isArray(data.providers)) {
        throw new Error('Registry file missing');
      }
      providers = data.providers;
      render();
    } catch (err) {
      if (host) {
        host.innerHTML = `<p class="registry-empty">Could not load the open source registry. ${esc(err && err.message ? err.message : '')}</p>`;
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }

  global.PLMRegistry = { load, render };
})(typeof window !== 'undefined' ? window : globalThis);
