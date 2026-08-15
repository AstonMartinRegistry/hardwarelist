const { supabaseFetch } = require('./_supabase');
const { sendWhatsAppText, whatsappConfig } = require('./_whatsapp');

function shortId(id) {
  return String(id || '').slice(0, 8);
}

function formatAlert(candidate, post) {
  const lines = [
    `🔔 PLM news (${candidate.kind || 'news'})`,
    candidate.summary || post?.title || '(no summary)',
    '',
    `title: ${post?.title || ''}`,
    candidate.model ? `model: ${candidate.model}` : null,
    candidate.quant ? `quant: ${candidate.quant}` : null,
    candidate.hardware ? `hardware: ${candidate.hardware}` : null,
    candidate.speed ? `speed: ${candidate.speed}` : null,
    candidate.price ? `price: ${candidate.price}` : null,
    candidate.context ? `context: ${candidate.context}` : null,
    '',
    post?.post_url || '',
    '',
    `id: ${shortId(candidate.id)}`,
    'Reply: publish | skip | next — or tell me what to change.',
  ];
  return lines.filter((l) => l != null).join('\n');
}

async function fetchClassifiedForAlert(limit) {
  const path =
    'ingest_candidates?select=id,post_id,status,kind,confidence,summary,model,quant,hardware,speed,price,context,version_url,info,ingest_posts(id,title,body,post_url,score)&status=eq.classified&order=classified_at.asc' +
    `&limit=${limit}`;
  return supabaseFetch(path);
}

async function markAlerted(candidateId, phone) {
  const now = new Date().toISOString();
  const rows = await supabaseFetch(
    `ingest_candidates?id=eq.${encodeURIComponent(candidateId)}`,
    {
      method: 'PATCH',
      prefer: 'return=representation',
      body: { status: 'alerted', updated_at: now },
    },
  );

  await supabaseFetch('ingest_conversations', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidateId,
      channel: 'whatsapp',
      external_thread_id: phone,
      messages: [
        {
          role: 'assistant',
          content: 'alert_sent',
          at: now,
        },
      ],
      updated_at: now,
    },
  });

  await supabaseFetch('ingest_actions', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidateId,
      action: 'alert',
      actor: 'system',
      detail: { channel: 'whatsapp', to: phone },
    },
  });

  return Array.isArray(rows) ? rows[0] : rows;
}

/**
 * Send WhatsApp alerts for classified candidates.
 * @param {{ limit?: number, to?: string }} [opts]
 */
async function alertClassified(opts = {}) {
  const cfg = whatsappConfig();
  const to = opts.to || cfg.to;
  if (!cfg.token || !cfg.phoneNumberId || !to) {
    return {
      ok: true,
      skipped: true,
      reason: 'WhatsApp not configured (need ACCESS_TOKEN, PHONE_NUMBER_ID, TO_NUMBER)',
      alerted: 0,
    };
  }

  const limit = Math.min(10, Math.max(1, Number(opts.limit) || 5));
  const rows = await fetchClassifiedForAlert(limit);
  const results = [];
  let alerted = 0;
  let errors = 0;

  for (const row of rows || []) {
    try {
      const text = formatAlert(row, row.ingest_posts);
      await sendWhatsAppText(to, text);
      await markAlerted(row.id, to);
      alerted += 1;
      results.push({ id: row.id, ok: true });
    } catch (err) {
      errors += 1;
      results.push({ id: row.id, ok: false, error: err.message || String(err) });
    }
  }

  return {
    ok: true,
    pending_alerts: (rows || []).length,
    alerted,
    errors,
    results,
  };
}

module.exports = {
  formatAlert,
  alertClassified,
  shortId,
};
