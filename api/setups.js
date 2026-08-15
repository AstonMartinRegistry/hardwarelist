const { supabaseFetch, supabaseConfig } = require('./_supabase');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=120');

  if (req.method === 'OPTIONS') return res.status(204).end();

  if (req.method === 'GET' && (req.query?.health === '1' || req.query?.health === 'true')) {
    const { url, key } = supabaseConfig();
    return res.status(200).json({
      ok: true,
      configured: Boolean(url && key),
      table: 'setups',
    });
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const limit = Math.min(500, Math.max(1, Number(req.query?.limit) || 500));
    const rows = await supabaseFetch(
      `setups?select=id,provider,model,quant,version_label,version_url,context,context_tokens,rank,hardware,price_usd,speed_raw,speed_tps,pp_tps,memory_used,memory_kv,memory_total,info,search,source,payload,updated_at&order=provider.asc,model.asc&limit=${limit}`,
    );
    return res.status(200).json({
      ok: true,
      count: Array.isArray(rows) ? rows.length : 0,
      setups: rows || [],
    });
  } catch (err) {
    return res.status(err.status || 500).json({
      error: err.message || 'Failed to load setups',
      detail: err.detail || undefined,
    });
  }
};
