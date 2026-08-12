#!/usr/bin/env node
/**
 * Parse index.html setup cards → upsert into public.setups
 *
 *   node scripts/sync_setups_from_html.js
 *   node scripts/sync_setups_from_html.js index.html
 *
 * Requires .env Supabase keys. Run supabase/setups.sql first.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#') || !t.includes('=')) continue;
    const i = t.indexOf('=');
    const k = t.slice(0, i).trim();
    let v = t.slice(i + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    if (!(k in process.env)) process.env[k] = v;
  }
}

loadEnv(path.join(__dirname, '..', '.env'));
loadEnv(path.join(__dirname, '..', '.env.local'));

const { supabaseFetch } = require('../api/_supabase');

function stripHtml(s) {
  return String(s || '')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function field(chunk, label) {
  const re = new RegExp(
    `rl">${label}</span><span class="rv">([\\s\\S]*?)</span>`,
  );
  const m = chunk.match(re);
  return m ? stripHtml(m[1]) : '';
}

function parseContextTokens(s) {
  if (!s) return null;
  const k = s.match(/([\d.]+)\s*k/i);
  if (k) return Number(k[1]) * 1000;
  const m = s.match(/([\d.]+)\s*m/i);
  if (m) return Number(m[1]) * 1e6;
  const n = s.replace(/,/g, '').match(/([\d.]+)/);
  return n ? Number(n[1]) : null;
}

function parseSpeed(s) {
  if (!s) return { speed_tps: null, pp_tps: null };
  const parts = s.split(/·/).map((x) => x.trim());
  let speed_tps = null;
  let pp_tps = null;
  for (const part of parts) {
    const isPp = /\bpp\b/i.test(part);
    const range = part.match(/([\d.]+)\s*[-–]\s*([\d.]+)\s*t\/?s/i);
    const single = part.match(/([\d.]+)\s*t\/?s/i);
    const val = range
      ? (Number(range[1]) + Number(range[2])) / 2
      : single
        ? Number(single[1])
        : null;
    if (val == null) continue;
    if (isPp) pp_tps = val;
    else if (speed_tps == null) speed_tps = val;
  }
  return { speed_tps, pp_tps };
}

function parseMem(chunk) {
  const used = chunk.match(/mem-used">([^<]+)/);
  const allow = chunk.match(/mem-allow[^>]*>([^<]+)/);
  const total = chunk.match(/mem-total">([^<]+)/);
  const kv = allow ? allow[1].replace(/[^\d.]/g, '') : null;
  const tot = total ? total[1].match(/([\d.]+)/) : null;
  return {
    memory_used: used ? Number(used[1]) : null,
    memory_kv: kv ? Number(kv) : null,
    memory_total: tot ? Number(tot[1]) : null,
  };
}

function extractCards(html) {
  const cards = [];
  const sectionRe = /<section class="cat cat-([a-z0-9-]+)"[^>]*>([\s\S]*?)<\/section>/gi;
  let sec;
  while ((sec = sectionRe.exec(html))) {
    const provider = sec[1];
    const body = sec[2];
    const starts = [];
    const marker = '<div class="setup setup-rich"';
    let idx = 0;
    while (true) {
      const at = body.indexOf(marker, idx);
      if (at < 0) break;
      starts.push(at);
      idx = at + marker.length;
    }
    for (let i = 0; i < starts.length; i++) {
      const start = starts[i];
      const end = i + 1 < starts.length ? starts[i + 1] : body.length;
      const chunk = body.slice(start, end);
      const name = chunk.match(/model-name">([^<]+)/);
      if (!name) continue;
      const priceAttr = chunk.match(/data-price="(\d+)"/);
      const rankAttr = chunk.match(/data-rank="(\d+)"/);
      const search = chunk.match(/data-search="([^"]*)"/);
      const versionHref = chunk.match(
        /rl">version<\/span><span class="rv"><a class="link-plain" href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/,
      );
      const speedRaw = field(chunk, 'speed');
      const { speed_tps, pp_tps } = parseSpeed(speedRaw);
      const mem = parseMem(chunk);
      const context = field(chunk, 'context') || null;
      const hardware = field(chunk, 'hardware') || null;
      const quant = field(chunk, 'quant') || null;
      const info = field(chunk, 'info') || null;
      const model = name[1].trim();
      const price_usd = priceAttr ? Number(priceAttr[1]) : null;
      const external_key = crypto
        .createHash('sha1')
        .update(
          [
            provider,
            model,
            quant || '',
            hardware || '',
            String(price_usd ?? ''),
            speedRaw || '',
          ].join('|'),
        )
        .digest('hex');

      cards.push({
        provider,
        model,
        quant,
        version_label: versionHref ? stripHtml(versionHref[2]) : null,
        version_url: versionHref ? versionHref[1] : null,
        context,
        context_tokens: parseContextTokens(context || ''),
        rank: rankAttr ? Number(rankAttr[1]) : null,
        hardware,
        price_usd,
        speed_raw: speedRaw || null,
        speed_tps,
        pp_tps,
        ...mem,
        info: info || null,
        search: search ? search[1] : null,
        source: 'html',
        external_key,
        payload: {
          price_label: field(chunk, 'price') || null,
        },
        updated_at: new Date().toISOString(),
      });
    }
  }
  return cards;
}

async function main() {
  const file = path.resolve(
    process.argv[2] || path.join(__dirname, '..', 'index.html'),
  );
  const html = fs.readFileSync(file, 'utf8');
  const cards = extractCards(html);
  if (!cards.length) {
    console.error('No setup cards found in', file);
    process.exit(1);
  }

  const chunkSize = 20;
  for (let i = 0; i < cards.length; i += chunkSize) {
    const slice = cards.slice(i, i + chunkSize);
    await supabaseFetch('setups?on_conflict=external_key', {
      method: 'POST',
      prefer: 'resolution=merge-duplicates,return=minimal',
      body: slice,
    });
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        file,
        upserted: cards.length,
        sample: cards.slice(0, 3).map((c) => ({
          model: c.model,
          provider: c.provider,
          speed_tps: c.speed_tps,
          pp_tps: c.pp_tps,
          price_usd: c.price_usd,
          hardware: c.hardware,
          rank: c.rank,
        })),
      },
      null,
      2,
    ),
  );
}

main().catch((err) => {
  console.error(err.message);
  if (err.detail) console.error(JSON.stringify(err.detail, null, 2));
  process.exit(1);
});
