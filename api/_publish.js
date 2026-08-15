const { supabaseFetch } = require('./_supabase');

function parsePriceUsd(price) {
  if (price == null || price === '') return null;
  if (typeof price === 'number' && Number.isFinite(price)) return price;
  const m = String(price).replace(/,/g, '').match(/(\d+(?:\.\d+)?)/);
  return m ? Number(m[1]) : null;
}

function parseSpeed(speed) {
  if (speed == null || speed === '') return { speed_raw: null, speed_tps: null, pp_tps: null };
  const raw = String(speed).trim();
  const nums = [...raw.matchAll(/(\d+(?:\.\d+)?)\s*(?:t\/?s|tok(?:ens)?\/?s(?:ec)?|tps)?/gi)]
    .map((m) => Number(m[1]))
    .filter((n) => Number.isFinite(n));
  let speed_tps = null;
  let pp_tps = null;
  const lower = raw.toLowerCase();
  if (/pp|prefill|prompt/.test(lower) && nums.length >= 2) {
    // Heuristic: first is gen, second is pp — or vice versa if "pp" comes first
    if (lower.indexOf('pp') < lower.search(/\d/)) {
      pp_tps = nums[0];
      speed_tps = nums[1] ?? null;
    } else {
      speed_tps = nums[0];
      pp_tps = nums[1] ?? null;
    }
  } else if (nums.length) {
    speed_tps = nums[0];
    if (nums[1] != null) pp_tps = nums[1];
  }
  return { speed_raw: raw, speed_tps, pp_tps };
}

async function publishCandidate(candidate, post) {
  if (!candidate?.model) {
    const err = new Error('Cannot publish: model is required');
    err.status = 400;
    throw err;
  }

  const { speed_raw, speed_tps, pp_tps } = parseSpeed(candidate.speed);
  const price_usd = parsePriceUsd(candidate.price);
  const now = new Date().toISOString();
  const external_key = `ingest:${candidate.id}`;

  const row = {
    provider: null,
    model: candidate.model,
    quant: candidate.quant || null,
    version_label: null,
    version_url: candidate.version_url || null,
    context: candidate.context || null,
    context_tokens: null,
    rank: null,
    hardware: candidate.hardware || null,
    price_usd,
    speed_raw,
    speed_tps,
    pp_tps,
    memory_used: null,
    memory_kv: null,
    memory_total: null,
    info: candidate.info || candidate.summary || null,
    search: [candidate.model, candidate.quant, candidate.hardware, candidate.speed]
      .filter(Boolean)
      .join(' '),
    source: 'whatsapp',
    external_key,
    payload: {
      candidate_id: candidate.id,
      post_id: candidate.post_id,
      post_url: post?.post_url || null,
      kind: candidate.kind,
      summary: candidate.summary,
    },
    updated_at: now,
  };

  const setups = await supabaseFetch('setups?on_conflict=external_key', {
    method: 'POST',
    prefer: 'resolution=merge-duplicates,return=representation',
    body: [row],
  });
  const setup = Array.isArray(setups) ? setups[0] : setups;

  const patched = await supabaseFetch(
    `ingest_candidates?id=eq.${encodeURIComponent(candidate.id)}`,
    {
      method: 'PATCH',
      prefer: 'return=representation',
      body: {
        status: 'posted',
        plmlist_id: setup?.id || null,
        updated_at: now,
      },
    },
  );

  await supabaseFetch('ingest_actions', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidate.id,
      action: 'post',
      actor: 'whatsapp',
      detail: { setup_id: setup?.id || null, external_key },
    },
  });

  return {
    setup,
    candidate: Array.isArray(patched) ? patched[0] : patched,
  };
}

async function skipCandidate(candidateId, reason) {
  const now = new Date().toISOString();
  const patched = await supabaseFetch(
    `ingest_candidates?id=eq.${encodeURIComponent(candidateId)}`,
    {
      method: 'PATCH',
      prefer: 'return=representation',
      body: {
        status: 'skipped',
        notes: reason || null,
        updated_at: now,
      },
    },
  );
  await supabaseFetch('ingest_actions', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidateId,
      action: 'skip',
      actor: 'whatsapp',
      detail: { reason: reason || null },
    },
  });
  return Array.isArray(patched) ? patched[0] : patched;
}

module.exports = {
  parsePriceUsd,
  parseSpeed,
  publishCandidate,
  skipCandidate,
};
