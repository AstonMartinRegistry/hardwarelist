module.exports = async function handler(req, res) {
  const url = (
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    process.env.SUPABASE_URL ||
    ''
  ).replace(/\/$/, '');
  const key =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    '';
  const table = process.env.SUPABASE_SETUPS_TABLE || 'plmlist';

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method === 'GET') {
    return res.status(200).json({
      ok: true,
      configured: Boolean(url && key),
      table,
    });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!url || !key) {
    return res.status(500).json({
      error: 'Supabase is not configured',
      detail: 'Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Vercel env.',
    });
  }

  const payload = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const version_url = String(payload.version_url || payload.link || '').trim();
  const hardware = String(payload.hardware || payload.specs || '').trim();
  const speed = String(payload.speed || payload.decode || '').trim();
  const kvRaw = payload.kv_ctx != null ? payload.kv_ctx : payload.context;
  const kv_ctx = Number(kvRaw);

  if (!version_url || !hardware || !speed || !Number.isFinite(kv_ctx)) {
    return res.status(400).json({
      error: 'Link, hardware, decode speed, and context length are required',
    });
  }

  const row = {
    model: String(payload.model || '').trim() || null,
    provider: String(payload.provider || '').trim() || null,
    quant_bits: String(payload.quant_bits || '').trim() || null,
    version_label: String(payload.version_label || '').trim() || null,
    version_url,
    kv_ctx,
    hardware,
    price: String(payload.price || '').trim() || null,
    speed,
    pp: String(payload.pp || '').trim() || null,
    info: String(payload.info || '').trim() || null,
    email: String(payload.email || '').trim() || null,
    payload,
  };

  const sb = await fetch(`${url}/rest/v1/${table}`, {
    method: 'POST',
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
    },
    body: JSON.stringify(row),
  });

  const text = await sb.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {
    data = text;
  }

  if (!sb.ok) {
    return res.status(502).json({
      error: 'Failed to save setup',
      detail: typeof data === 'string' ? data : JSON.stringify(data),
    });
  }

  const saved = Array.isArray(data) ? data[0] : data;
  return res.status(200).json({ ok: true, id: saved && saved.id });
};
