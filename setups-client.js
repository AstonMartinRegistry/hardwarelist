/**
 * Client-side renderer: Supabase setups → .setup.setup-rich cards
 * Shared by index.html / locallist.html (and usable by stats).
 */
(function (global) {
  const PROVIDER_LABELS = {
    qwen: 'Qwen',
    glm: 'GLM',
    gemma: 'Gemma',
    minimax: 'MiniMax',
    mistral: 'Mistral',
    other: 'Other',
  };

  const KNOWN = ['qwen', 'glm', 'gemma', 'minimax', 'mistral', 'other'];

  function esc(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function providerSlug(p) {
    const s = String(p || 'other').toLowerCase().trim();
    if (KNOWN.includes(s)) return s;
    if (!s) return 'other';
    return s.replace(/[^a-z0-9-]+/g, '-') || 'other';
  }

  function formatPrice(n) {
    if (n == null || n === '') return '';
    const num = Number(n);
    if (!Number.isFinite(num)) return esc(String(n));
    return '$' + (Number.isInteger(num) ? String(num) : String(num));
  }

  function formatSpeed(row) {
    if (row.speed_raw) return esc(row.speed_raw);
    const parts = [];
    if (row.speed_tps != null) parts.push(`${row.speed_tps}t/s`);
    if (row.pp_tps != null) parts.push(`${row.pp_tps}t/s pp`);
    return parts.join(' · ');
  }

  function buildSearch(row) {
    if (row.search) return String(row.search);
    return [row.model, row.quant, row.hardware, row.speed_raw, row.provider]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
  }

  function renderRankRow(row) {
    const tipHtml = row.payload && row.payload.tip_html;
    if (tipHtml) return tipHtml; // already a full .rf rank row from sync
    if (row.rank == null) return '';
    return rf('rank', `<span class="rank-n">#${esc(row.rank)}</span>`);
  }

  function renderVersion(row) {
    const label = row.version_label || row.version_url || '';
    if (!label && !row.version_url) return '';
    if (row.version_url) {
      return `<a class="link-plain" href="${esc(row.version_url)}" target="_blank" rel="noopener" title="${esc(label || row.version_url)}">${esc(label || row.version_url)}</a>`;
    }
    return esc(label);
  }

  function renderMemory(row) {
    const used = row.memory_used;
    const total = row.memory_total;
    const kv = row.memory_kv;
    if (used == null && total == null) return '';
    const usedN = Number(used);
    const totalN = Number(total);
    const kvN = kv != null ? Number(kv) : null;
    const allow = Number.isFinite(usedN) && Number.isFinite(kvN) ? usedN + kvN : null;
    const max = Number.isFinite(totalN) && totalN > 0 ? totalN : null;
    const fillPct =
      max && Number.isFinite(usedN) ? Math.min(100, (usedN / max) * 100) : 0;
    const allowPct =
      max && Number.isFinite(allow) ? Math.min(100, (allow / max) * 100) : fillPct;

    let ratio = '';
    if (Number.isFinite(usedN)) {
      ratio += `<span class="mem-used">${esc(usedN)}</span>`;
      if (Number.isFinite(kvN)) {
        ratio += `<span class="mem-allow" title="KV cache estimate"> +kv ${esc(kvN)}</span>`;
      }
      if (Number.isFinite(totalN)) {
        ratio += `<span class="mem-sep"> / </span><span class="mem-total">${esc(totalN)} GB</span>`;
      }
    } else if (Number.isFinite(totalN)) {
      ratio = `<span class="mem-total">${esc(totalN)} GB</span>`;
    }

    const bar =
      max != null
        ? `<div class="mem-bar" role="meter" aria-label="memory" aria-valuemin="0" aria-valuemax="${esc(max)}" aria-valuenow="${esc(usedN || 0)}"><div class="mem-bar-allow" style="width:${allowPct.toFixed(1)}%"></div><div class="mem-bar-fill" style="width:${fillPct.toFixed(1)}%"></div></div>`
        : '';

    return `<span class="mem-ratio">${ratio}</span>${bar}`;
  }

  function renderInfo(row) {
    const info = row.info || '';
    if (!info) return '';
    return `<span class="info-v"><span class="info-clamp">${esc(info)}</span> <button type="button" class="read-more-btn" onclick="toggleInfo(this)" hidden>read more</button></span>`;
  }

  function rf(label, inner) {
    if (!inner) return '';
    return `<div class="rf"><span class="rl">${esc(label)}</span><span class="rv">${inner}</span></div>`;
  }

  function renderCard(row) {
    const provider = providerSlug(row.provider);
    const price = row.price_usd != null ? Number(row.price_usd) : null;
    const attrs = [
      `class="setup setup-rich cat-${esc(provider)}"`,
      `data-search="${esc(buildSearch(row))}"`,
      row.id ? `data-id="${esc(row.id)}"` : '',
      Number.isFinite(price) ? `data-price="${esc(price)}"` : '',
      row.rank != null ? `data-rank="${esc(row.rank)}"` : '',
      `data-provider="${esc(provider)}"`,
    ]
      .filter(Boolean)
      .join(' ');

    const stack = [
      rf('quant', esc(row.quant || '')),
      rf('version', renderVersion(row)),
      rf('context', esc(row.context || 'n/a')),
      renderRankRow(row),
      '<div class="rich-rule" aria-hidden="true"></div>',
      rf('hardware', esc(row.hardware || '')),
      rf('price', formatPrice(price)),
      rf('memory', renderMemory(row)),
      rf('speed', formatSpeed(row)),
      rf('info', renderInfo(row)),
    ].join('');

    return `<div ${attrs}><div class="model-box"><span class="model-name">${esc(row.model || 'unknown')}</span></div><div class="results-box"><div class="rich-stack">${stack}</div></div></div>`;
  }

  function ensureSection(slug) {
    let section = document.getElementById(`cat-${slug}`);
    if (section) return section;
    const cats = document.querySelector('.cats');
    if (!cats) return null;
    const sorted = document.getElementById('cat-sorted');
    section = document.createElement('section');
    section.className = `cat cat-${slug}`;
    section.id = `cat-${slug}`;
    section.innerHTML = '<div class="cat-results"><div class="grid"></div></div>';
    if (sorted) cats.insertBefore(section, sorted);
    else cats.appendChild(section);

    // Nav chip if missing
    const nav = document.querySelector('.navlinks');
    if (nav && !nav.querySelector(`[href="#cat-${slug}"]`)) {
      const clear = document.getElementById('nav-clear');
      const a = document.createElement('a');
      a.className = `navlink nav-${slug}`;
      a.href = `#cat-${slug}`;
      a.innerHTML = `<span class="nav-label">${esc(PROVIDER_LABELS[slug] || slug)}</span><span class="navn"><span class="navn-num">0</span></span>`;
      if (clear) nav.insertBefore(a, clear);
      else nav.appendChild(a);
    }
    return section;
  }

  function updateNavCounts(counts) {
    Object.entries(counts).forEach(([slug, n]) => {
      const link = document.querySelector(`.navlink[href="#cat-${slug}"] .navn-num`);
      if (link) link.textContent = String(n);
    });
    // zero out known empty
    KNOWN.forEach((slug) => {
      if (counts[slug] != null) return;
      const link = document.querySelector(`.navlink[href="#cat-${slug}"] .navn-num`);
      if (link) link.textContent = '0';
    });
  }

  function mountSetups(setups) {
    const cats = document.querySelector('.cats');
    if (!cats) return { count: 0 };

    // Clear existing cards
    cats.querySelectorAll('.setup').forEach((el) => el.remove());

    const byProvider = {};
    for (const row of setups || []) {
      const slug = providerSlug(row.provider);
      if (!byProvider[slug]) byProvider[slug] = [];
      byProvider[slug].push(row);
    }

    const counts = {};
    for (const [slug, rows] of Object.entries(byProvider)) {
      const section = ensureSection(slug);
      const grid = section?.querySelector('.grid');
      if (!grid) continue;
      grid.innerHTML = rows.map(renderCard).join('');
      counts[slug] = rows.length;
    }

    updateNavCounts(counts);
    global.PLMSetups.lastSetups = setups || [];
    document.dispatchEvent(new CustomEvent('plm:setups-loaded', { detail: { setups: setups || [] } }));

    if (typeof global.locallistBindSetups === 'function') {
      global.locallistBindSetups();
    }
    if (typeof global.refreshInfoButtons === 'function') {
      global.refreshInfoButtons();
    }

    return { count: (setups || []).length, counts };
  }

  async function loadAndMount(apiUrl) {
    const boot = typeof document !== 'undefined'
      ? document.getElementById('plm-setups-bootstrap')
      : null;
    if (boot && boot.textContent) {
      try {
        const data = JSON.parse(boot.textContent);
        if (data && Array.isArray(data.setups)) {
          const mounted = mountSetups(data.setups);
          // Refresh in background so long-lived tabs stay current
          if (apiUrl !== false) {
            fetch(apiUrl || '/api/setups', { cache: 'no-store' })
              .then((r) => (r.ok ? r.json() : null))
              .then((fresh) => {
                if (fresh && fresh.ok && Array.isArray(fresh.setups)) mountSetups(fresh.setups);
              })
              .catch(() => {});
          }
          return mounted;
        }
      } catch (_) {
        /* fall through to network */
      }
    }
    const url = apiUrl || '/api/setups';
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`setups ${res.status}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'setups failed');
    return mountSetups(data.setups || []);
  }

  function mapApiToStats(rows) {
    return (rows || [])
      .map((row, i) => {
        const price = row.price_usd != null ? Number(row.price_usd) : null;
        const rank = row.rank != null ? Number(row.rank) : null;
        const quant = row.quant || '';
        const qm = String(quant).match(/(\d+(?:\.\d+)?)/);
        const speed =
          row.speed_tps != null
            ? Number(row.speed_tps)
            : null;
        let context = row.context_tokens != null ? Number(row.context_tokens) : null;
        if (context == null && row.context) {
          const k = String(row.context).match(/([\d.]+)\s*k/i);
          const m = String(row.context).match(/([\d.]+)\s*m/i);
          const n = String(row.context).replace(/,/g, '').match(/([\d.]+)/);
          if (k) context = Number(k[1]) * 1000;
          else if (m) context = Number(m[1]) * 1e6;
          else if (n) context = Number(n[1]);
        }
        return {
          id: row.id || i,
          name: row.model || 'unknown',
          provider: providerSlug(row.provider),
          price: Number.isFinite(price) ? price : null,
          priceLabel: formatPrice(price),
          rank: Number.isFinite(rank) ? rank : null,
          smart: Number.isFinite(rank) ? 160 - rank : null,
          aa: null,
          quant,
          quantN: qm ? Number(qm[1]) : null,
          hardware: row.hardware || '',
          speed: Number.isFinite(speed) ? speed : null,
          speedRaw: row.speed_raw || '',
          context: Number.isFinite(context) ? context : null,
          contextRaw: row.context || '',
          memUsed: row.memory_used != null ? Number(row.memory_used) : null,
          memTotal: row.memory_total != null ? Number(row.memory_total) : null,
          search: buildSearch(row),
        };
      })
      .filter((s) => s.price != null);
  }

  global.PLMSetups = {
    renderCard,
    mountSetups,
    loadAndMount,
    mapApiToStats,
    providerSlug,
    PROVIDER_LABELS,
    lastSetups: [],
  };
})(typeof window !== 'undefined' ? window : globalThis);
