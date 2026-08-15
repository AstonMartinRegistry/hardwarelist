const { classifyPending } = require('./_classify');
const { alertClassified } = require('./_alert');
const { cerebrasConfig } = require('./_cerebras');
const { supabaseConfig } = require('./_supabase');
const { whatsappConfig } = require('./_whatsapp');

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

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') return res.status(204).end();

  if (req.method === 'GET' && (req.query?.health === '1' || req.query?.health === 'true')) {
    const { url, key } = supabaseConfig();
    const { apiKey, classifyModel, chatModel } = cerebrasConfig();
    const wa = whatsappConfig();
    return res.status(200).json({
      ok: true,
      configured: Boolean(url && key && apiKey),
      supabase: Boolean(url && key),
      cerebras: Boolean(apiKey),
      whatsapp: Boolean(wa.token && wa.phoneNumberId && wa.to),
      classifyModel,
      chatModel,
      schedule: '5 */2 * * *',
    });
  }

  if (req.method !== 'GET' && req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!authorizeCron(req)) return unauthorized(res);

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const q = req.query || {};
    const limit = Number(body.limit || q.limit) || 15;
    const alertLimit = Number(body.alertLimit || q.alertLimit) || 5;
    const skipAlert =
      body.skipAlert === true ||
      q.skipAlert === '1' ||
      q.skipAlert === 'true';
    const result = await classifyPending({ limit });
    let alerts = null;
    if (!skipAlert && result.classified > 0) {
      alerts = await alertClassified({ limit: alertLimit });
    } else if (!skipAlert) {
      // Still flush any leftover classified rows
      alerts = await alertClassified({ limit: alertLimit });
    }
    return res.status(200).json({ ...result, alerts });
  } catch (err) {
    return res.status(err.status || 500).json({
      error: err.message || 'Classify cron failed',
      detail: err.detail || undefined,
    });
  }
};
