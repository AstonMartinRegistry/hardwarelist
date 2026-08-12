const { supabaseFetch } = require('./_supabase');

const EDITABLE = new Set([
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
  'extracted',
  'status',
  'notes',
  'plmlist_id',
]);

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const secret = process.env.CRON_SECRET || process.env.INGEST_API_SECRET || '';
  if (secret) {
    const auth = req.headers.authorization || '';
    if (auth !== `Bearer ${secret}`) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  try {
    if (req.method === 'GET') {
      const q = req.query || {};
      const status = q.status ? String(q.status) : '';
      const newsOnly = q.news === '1' || q.news === 'true';
      const limit = Math.min(100, Math.max(1, Number(q.limit) || 20));

      let path =
        'ingest_candidates?select=*,ingest_posts(id,title,body,post_url,score,source_created_at,crosspost_url,crosspost_body)&order=updated_at.desc' +
        `&limit=${limit}`;
      if (status) path += `&status=eq.${encodeURIComponent(status)}`;
      if (newsOnly) path += '&is_news=eq.true';

      const rows = await supabaseFetch(path);
      return res.status(200).json({ ok: true, candidates: rows });
    }

    if (req.method === 'PATCH') {
      const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
      const id = body.id || req.query?.id;
      if (!id) return res.status(400).json({ error: 'id is required' });

      const patch = {};
      for (const key of EDITABLE) {
        if (Object.prototype.hasOwnProperty.call(body, key)) {
          patch[key] = body[key];
        }
      }
      if (!Object.keys(patch).length) {
        return res.status(400).json({ error: 'No editable fields provided' });
      }
      patch.updated_at = new Date().toISOString();

      const rows = await supabaseFetch(
        `ingest_candidates?id=eq.${encodeURIComponent(id)}`,
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
          candidate_id: id,
          action: 'edit',
          actor: body.actor || 'api',
          detail: { patch },
        },
      });

      return res.status(200).json({ ok: true, candidate: Array.isArray(rows) ? rows[0] : rows });
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    return res.status(err.status || 500).json({
      error: err.message || 'Candidates request failed',
      detail: err.detail || undefined,
    });
  }
};
