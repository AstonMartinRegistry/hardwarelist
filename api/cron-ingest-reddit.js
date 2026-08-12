const { upsertSnapshot } = require('./_ingest');
const { supabaseConfig } = require('./_supabase');
const { scrapeReddit } = require('./_reddit_scrape');

function unauthorized(res) {
  return res.status(401).json({ error: 'Unauthorized' });
}

function isVercelCron(req) {
  const ua = String(req.headers['user-agent'] || '');
  return ua.includes('vercel-cron');
}

function authorizeCron(req) {
  const secret = process.env.CRON_SECRET || '';
  const header = req.headers.authorization || '';

  if (secret && header === `Bearer ${secret}`) return true;
  if (secret && (req.query || {}).secret === secret) return true;
  if (!secret && process.env.VERCEL_ENV !== 'production') return true;
  if (!secret && isVercelCron(req)) return true;
  return false;
}

async function runIngest(req) {
  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const q = req.query || {};
  const limit = Math.min(50, Math.max(1, Number(body.limit || q.limit) || 25));
  const includeDiscussion = (body.includeDiscussion ?? q.includeDiscussion) !== 'false'
    && (body.includeDiscussion ?? q.includeDiscussion) !== false;
  const posts = Math.min(25, Math.max(1, Number(body.posts || q.posts) || limit));
  const comments = Math.min(10, Math.max(0, Number(body.comments || q.comments) || 0));
  const ranking = String(body.ranking || q.ranking || 'new');
  const window = String(body.window || q.window || 'week');

  let snapshot = body.snapshot;
  if (!snapshot) {
    snapshot = await scrapeReddit({
      ranking,
      window,
      limit,
      includeDiscussion,
      posts,
      comments,
    });
  }

  const result = await upsertSnapshot(snapshot);
  return {
    ok: true,
    ranking: snapshot.ranking,
    fetchedAt: snapshot.fetchedAt,
    ...result,
  };
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') return res.status(204).end();

  if (req.method === 'GET' && (req.query?.health === '1' || req.query?.health === 'true')) {
    const { url, key } = supabaseConfig();
    return res.status(200).json({
      ok: true,
      configured: Boolean(url && key),
      scraper: 'builtin',
      schedule: '0 */2 * * *',
    });
  }

  if (req.method !== 'GET' && req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!authorizeCron(req)) return unauthorized(res);

  try {
    const result = await runIngest(req);
    return res.status(200).json(result);
  } catch (err) {
    const status = err.status || 500;
    return res.status(status).json({
      error: err.message || 'Ingest failed',
      detail: err.detail || undefined,
    });
  }
};
