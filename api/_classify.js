const { cerebrasChat, cerebrasConfig } = require('./_cerebras');
const { supabaseFetch } = require('./_supabase');

const NULLABLE_STRING = { anyOf: [{ type: 'string' }, { type: 'null' }] };

const CLASSIFY_SCHEMA = {
  type: 'object',
  properties: {
    is_news: {
      type: 'boolean',
      description:
        'True if this is new and exciting for local-LLM people: new models, new speed/quality improvements, notable releases, breakthroughs, or other fresh developments worth flagging.',
    },
    kind: {
      type: 'string',
      enum: ['setup', 'speed', 'quant', 'other_news', 'noise'],
    },
    confidence: {
      type: 'number',
      description: '0 to 1 confidence that is_news is correct.',
    },
    summary: {
      type: 'string',
      description: 'One or two sentences: what is new/exciting, or why this is not news.',
    },
    model: NULLABLE_STRING,
    quant: NULLABLE_STRING,
    hardware: NULLABLE_STRING,
    speed: NULLABLE_STRING,
    price: NULLABLE_STRING,
    context: NULLABLE_STRING,
    version_url: NULLABLE_STRING,
    info: NULLABLE_STRING,
  },
  required: [
    'is_news',
    'kind',
    'confidence',
    'summary',
    'model',
    'quant',
    'hardware',
    'speed',
    'price',
    'context',
    'version_url',
    'info',
  ],
  additionalProperties: false,
};

const SYSTEM_PROMPT = `You are a news triage gate for PLM List (plmlist.com) — local LLMs, hardware, and running models yourself.

Primary question: is this NEW and EXCITING?

Set is_news=true for fresh developments people in local LLM would care about, such as:
- New models / model releases / strong new open weights
- New improvements: faster tokens/sec, better latency, better quality at the same size, less VRAM, longer context that actually works
- New engines, kernels, speculative decoding, quantization methods, tooling that changes what you can run locally
- Notable hardware results or product news that shift the local-LLM landscape
- Concrete setups or benchmarks that reveal something new (not just a vague “my PC runs LLMs”)

Set is_news=false (kind=noise) for: memes, vibes, hiring, pure cloud SaaS promo, repetitive advice threads, “which GPU should I buy?” with no new info, or discussion that isn’t announcing anything new.

kind (secondary label):
- setup: someone sharing a concrete rig / stack
- speed: throughput / latency results or speed-focused improvements
- quant: quantization / format / compression
- other_news: new/exciting but not mainly setup/speed/quant (e.g. a new model drop)
- noise: not news

Bias toward catching real novelty; skip fluff.
Fill extract fields only when clearly stated; otherwise null. Do not invent specs.
Draft fields are hints for a later human/chat review — keep them short.`;

function clip(text, max) {
  const s = String(text || '').trim();
  if (s.length <= max) return s;
  return `${s.slice(0, max)}…`;
}

function buildUserPrompt(post) {
  const body = post.body || post.post_body || post.crosspost_body || '';
  const parts = [
    `post_id: ${post.id}`,
    `url: ${post.post_url || ''}`,
    `score: ${post.score ?? ''}`,
    `title: ${post.title || ''}`,
    `body:\n${clip(body, 12000)}`,
  ];
  if (post.crosspost_url) {
    parts.push(`crosspost_url: ${post.crosspost_url}`);
  }
  if (post.crosspost_body && post.crosspost_body !== body) {
    parts.push(`crosspost_body:\n${clip(post.crosspost_body, 8000)}`);
  }
  return parts.join('\n\n');
}

function normalizeResult(parsed) {
  const confidence = Number(parsed.confidence);
  const kind = ['setup', 'speed', 'quant', 'other_news', 'noise'].includes(parsed.kind)
    ? parsed.kind
    : 'noise';
  const isNews = Boolean(parsed.is_news) && kind !== 'noise';
  return {
    is_news: isNews,
    kind,
    confidence: Number.isFinite(confidence)
      ? Math.min(1, Math.max(0, confidence))
      : 0,
    summary: clip(parsed.summary || '', 2000) || null,
    model: parsed.model || null,
    quant: parsed.quant || null,
    hardware: parsed.hardware || null,
    speed: parsed.speed || null,
    price: parsed.price || null,
    context: parsed.context || null,
    version_url: parsed.version_url || null,
    info: parsed.info || null,
  };
}

async function classifyPost(post, { model } = {}) {
  const { classifyModel } = cerebrasConfig();
  const usedModel = model || classifyModel;

  const { content, raw } = await cerebrasChat({
    model: usedModel,
    reasoning_effort: 'low',
    temperature: 0,
    max_tokens: 1200,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: buildUserPrompt(post) },
    ],
    response_format: {
      type: 'json_schema',
      json_schema: {
        name: 'plmlist_classify',
        strict: true,
        schema: CLASSIFY_SCHEMA,
      },
    },
  });

  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch (err) {
    const e = new Error(`Classifier returned invalid JSON: ${err.message}`);
    e.status = 502;
    e.detail = { content };
    throw e;
  }

  return {
    result: normalizeResult(parsed),
    model: usedModel,
    raw,
  };
}

async function fetchPendingCandidates(limit) {
  const path =
    'ingest_candidates?select=id,post_id,status,ingest_posts(id,title,body,post_body,crosspost_url,crosspost_body,post_url,score,source_created_at)&status=eq.pending&order=created_at.asc' +
    `&limit=${limit}`;
  return supabaseFetch(path);
}

async function applyClassification(candidateId, { result, model }) {
  const status = result.is_news ? 'classified' : 'skipped';
  const now = new Date().toISOString();
  const patch = {
    ...result,
    extracted: {
      draft: {
        model: result.model,
        quant: result.quant,
        hardware: result.hardware,
        speed: result.speed,
        price: result.price,
        context: result.context,
        version_url: result.version_url,
        info: result.info,
      },
    },
    classifier_model: model,
    status,
    classified_at: now,
    updated_at: now,
  };

  const rows = await supabaseFetch(
    `ingest_candidates?id=eq.${encodeURIComponent(candidateId)}`,
    {
      method: 'PATCH',
      prefer: 'return=representation',
      body: patch,
    },
  );

  await supabaseFetch('ingest_actions', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidateId,
      action: 'classify',
      actor: 'system',
      detail: {
        model,
        status,
        is_news: result.is_news,
        kind: result.kind,
        confidence: result.confidence,
      },
    },
  });

  return Array.isArray(rows) ? rows[0] : rows;
}

/**
 * Classify pending ingest_candidates with Cerebras gpt-oss-120b.
 * @param {{ limit?: number }} [opts]
 */
async function classifyPending(opts = {}) {
  const limit = Math.min(30, Math.max(1, Number(opts.limit) || 15));
  const { apiKey, classifyModel } = cerebrasConfig();
  if (!apiKey) {
    const err = new Error('CEREBRAS_API_KEY is not configured');
    err.status = 500;
    throw err;
  }

  const pending = await fetchPendingCandidates(limit);
  const results = [];
  let classified = 0;
  let skipped = 0;
  let errors = 0;

  for (const row of pending || []) {
    const post = row.ingest_posts;
    if (!post) {
      errors += 1;
      results.push({ id: row.id, ok: false, error: 'missing ingest_posts join' });
      continue;
    }

    try {
      const { result, model } = await classifyPost(post, { model: classifyModel });
      const updated = await applyClassification(row.id, { result, model });
      if (result.is_news) classified += 1;
      else skipped += 1;
      results.push({
        id: row.id,
        post_id: row.post_id,
        ok: true,
        status: updated?.status || (result.is_news ? 'classified' : 'skipped'),
        is_news: result.is_news,
        kind: result.kind,
        confidence: result.confidence,
        summary: result.summary,
      });
    } catch (err) {
      errors += 1;
      results.push({
        id: row.id,
        post_id: row.post_id,
        ok: false,
        error: err.message || String(err),
      });
    }
  }

  return {
    ok: true,
    model: classifyModel,
    pending: (pending || []).length,
    classified,
    skipped,
    errors,
    results,
  };
}

module.exports = {
  CLASSIFY_SCHEMA,
  SYSTEM_PROMPT,
  classifyPost,
  classifyPending,
  buildUserPrompt,
};
