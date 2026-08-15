/**
 * Inject DB setups into static HTML for crawlability (SSR-style embed).
 */
const fs = require('fs');
const path = require('path');
const { supabaseFetch } = require('./_supabase');

const ROOT = path.join(__dirname, '..');
const SITE = 'https://plmlist.com';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function providerSlug(p) {
  const known = ['qwen', 'glm', 'gemma', 'minimax', 'mistral', 'other'];
  const s = String(p || 'other').toLowerCase().trim();
  if (known.includes(s)) return s;
  return s.replace(/[^a-z0-9-]+/g, '-') || 'other';
}

async function loadSetups() {
  return supabaseFetch(
    'setups?select=id,provider,model,quant,version_label,version_url,context,context_tokens,rank,hardware,price_usd,speed_raw,speed_tps,pp_tps,memory_used,memory_kv,memory_total,info,search,source,payload,updated_at&order=provider.asc,model.asc&limit=500',
  );
}

function jsonLd(setups) {
  const items = (setups || []).slice(0, 200).map((row, i) => ({
    '@type': 'ListItem',
    position: i + 1,
    name: [row.model, row.quant, row.hardware].filter(Boolean).join(' · '),
    description: [
      row.speed_raw && `${row.speed_raw}`,
      row.context && `ctx ${row.context}`,
      row.price_usd != null && `$${row.price_usd}`,
      row.info,
    ]
      .filter(Boolean)
      .join(' — ')
      .slice(0, 300),
  }));
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'PLM List — Personal Language Model hardware setups',
    description:
      'Community directory of personal language models (local LLMs): hardware, quantization, VRAM, and tokens/sec.',
    url: SITE,
    numberOfItems: (setups || []).length,
    itemListElement: items,
  };
}

function noscriptList(setups) {
  const lis = (setups || [])
    .map((row) => {
      const bits = [
        row.model,
        row.quant,
        row.version_label,
        row.hardware,
        row.price_usd != null ? `$${row.price_usd}` : '',
        row.speed_raw,
        row.context ? `ctx ${row.context}` : '',
      ].filter(Boolean);
      return `<li>${esc(bits.join(' · '))}</li>`;
    })
    .join('\n');
  return `<noscript>
<section class="seo-fallback">
<h2>Personal Language Model (PLM) hardware setups</h2>
<p>Directory of local LLM rigs: llama.cpp, vLLM, Ollama, GGUF quants, VRAM, and tokens/sec.</p>
<ul>
${lis}
</ul>
</section>
</noscript>`;
}

function bootstrapScript(setups) {
  const payload = JSON.stringify({ ok: true, setups: setups || [], embedded: true });
  // Break </script> in JSON if present
  const safe = payload.replace(/</g, '\\u003c');
  return `<script type="application/json" id="plm-setups-bootstrap">${safe}</script>
<script type="application/ld+json" id="plm-jsonld">${JSON.stringify(jsonLd(setups)).replace(/</g, '\\u003c')}</script>`;
}

/** Minimal card HTML for crawlers (mirrors setups-client structure). */
function renderCard(row) {
  const provider = providerSlug(row.provider);
  const price = row.price_usd != null ? Number(row.price_usd) : null;
  const mem =
    row.memory_used != null
      ? `${row.memory_used}${row.memory_kv != null ? ` +kv ${row.memory_kv}` : ''}${row.memory_total != null ? ` / ${row.memory_total} GB` : ''}`
      : '';
  const rows = [
    row.quant && `<div class="rf"><span class="rl">quant</span><span class="rv">${esc(row.quant)}</span></div>`,
    row.version_label && `<div class="rf"><span class="rl">version</span><span class="rv">${esc(row.version_label)}</span></div>`,
    `<div class="rf"><span class="rl">context</span><span class="rv">${esc(row.context || 'n/a')}</span></div>`,
    row.hardware && `<div class="rf"><span class="rl">hardware</span><span class="rv">${esc(row.hardware)}</span></div>`,
    price != null && Number.isFinite(price) && `<div class="rf"><span class="rl">price</span><span class="rv">$${esc(price)}</span></div>`,
    mem && `<div class="rf"><span class="rl">memory</span><span class="rv">${esc(mem)}</span></div>`,
    row.speed_raw && `<div class="rf"><span class="rl">speed</span><span class="rv">${esc(row.speed_raw)}</span></div>`,
    row.info && `<div class="rf"><span class="rl">info</span><span class="rv">${esc(String(row.info).slice(0, 280))}</span></div>`,
  ]
    .filter(Boolean)
    .join('');
  return `<div class="setup setup-rich cat-${esc(provider)}" data-provider="${esc(provider)}" data-search="${esc([row.model, row.quant, row.hardware, row.speed_raw].filter(Boolean).join(' '))}"${row.id ? ` data-id="${esc(row.id)}"` : ''}${price != null ? ` data-price="${esc(price)}"` : ''}><div class="model-box"><span class="model-name">${esc(row.model || 'unknown')}</span></div><div class="results-box"><div class="rich-stack">${rows}</div></div></div>`;
}

function fillGrids(html, setups) {
  const byProvider = {};
  for (const row of setups || []) {
    const slug = providerSlug(row.provider);
    if (!byProvider[slug]) byProvider[slug] = [];
    byProvider[slug].push(row);
  }
  let out = html;
  for (const [slug, rows] of Object.entries(byProvider)) {
    const cards = rows.map(renderCard).join('');
    const re = new RegExp(
      `(<section[^>]*\\bid=["']cat-${slug}["'][^>]*>[\\s\\S]*?<div class=["']grid["']>)([\\s\\S]*?)(<\\/div>)`,
      'i',
    );
    if (re.test(out)) {
      out = out.replace(re, `$1${cards}$3`);
    }
  }
  // Nav counts
  for (const [slug, rows] of Object.entries(byProvider)) {
    const re = new RegExp(
      `(href=["']#cat-${slug}["'][\\s\\S]*?<span class=["']navn-num["']>)([^<]*)(<\\/span>)`,
      'i',
    );
    out = out.replace(re, `$1${rows.length}$3`);
  }
  return out;
}

function injectHead(html) {
  // Ensure SEO head block exists (idempotent replace of title if still bare)
  if (html.includes('name="description"')) return html;
  const block = `
<meta name="description" content="PLM List — directory of Personal Language Models and local LLM hardware setups: VRAM, GGUF quants, llama.cpp / vLLM speeds (tokens/sec), and community rigs.">
<meta name="keywords" content="personal language model, PLM, local LLM, llama.cpp, vLLM, Ollama, GGUF, VRAM, RTX, local AI hardware">
<link rel="canonical" href="${SITE}/">
<meta property="og:type" content="website">
<meta property="og:url" content="${SITE}/">
<meta property="og:title" content="PLM List – Personal Language Models & Local LLM Hardware">
<meta property="og:description" content="Browse community hardware setups, VRAM needs, and tokens/sec for personal language models and local AI.">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="PLM List – Personal Language Models & Local LLM Hardware">
<meta name="twitter:description" content="Community directory of local LLM hardware setups and benchmarks.">
`;
  return html.replace(/<title>PLM List<\/title>/, `<title>PLM List – Personal Language Models & Local LLM Hardware</title>${block}`);
}

async function embedSetupsIntoHtml(htmlPath) {
  const raw = fs.readFileSync(htmlPath, 'utf8');
  let setups = [];
  try {
    setups = (await loadSetups()) || [];
  } catch (err) {
    console.error('embed: failed to load setups', err.message || err);
  }
  let html = injectHead(raw);
  html = fillGrids(html, setups);
  const inject = `${bootstrapScript(setups)}\n${noscriptList(setups)}\n`;
  if (html.includes('<!--plm:embed-->')) {
    html = html.replace('<!--plm:embed-->', inject);
  } else {
    html = html.replace('</body>', `${inject}</body>`);
  }
  return { html, count: setups.length };
}

module.exports = {
  embedSetupsIntoHtml,
  loadSetups,
  SITE,
};
