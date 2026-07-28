const nodemailer = require('nodemailer');

function asObject(value) {
  if (value == null) return null;
  if (Buffer.isBuffer(value)) {
    const raw = value.toString('utf8').trim();
    if (!raw) return null;
    return JSON.parse(raw);
  }
  if (typeof value === 'string') {
    const raw = value.trim();
    if (!raw) return null;
    return JSON.parse(raw);
  }
  if (typeof value === 'object') return value;
  return null;
}

function readBody(req) {
  // Vercel Node functions expose a parsed body; streaming req.on('data') is unreliable.
  try {
    const fromBody = asObject(req.body);
    if (fromBody && Object.keys(fromBody).length) return fromBody;
  } catch (_) {
    /* fall through */
  }
  return {};
}

function line(label, value) {
  const v = value == null ? '' : String(value).trim();
  if (!v) return null;
  return `${label}: ${v}`;
}

function formatBody(payload) {
  const lines = [
    line('Model', payload.model),
    line('Provider', payload.provider),
    line('Quant', payload.quant_bits),
    line('Version', payload.version_label),
    line('Link', payload.version_url),
    line('Context', payload.kv_ctx),
    line('Hardware', payload.hardware),
    line('Price', payload.price),
    line('Decode', payload.speed),
    line('Prefill', payload.pp),
    line('Info', payload.info),
    line('Email', payload.email),
  ].filter(Boolean);

  return `${lines.join('\n')}\n\n---\nJSON\n${JSON.stringify(payload, null, 2)}\n`;
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method !== 'POST') {
    res.statusCode = 405;
    res.setHeader('Allow', 'POST');
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }

  const user = process.env.SENDER_EMAIL;
  const pass = process.env.SENDER_PASSWORD;
  const to = process.env.RECEIVER_EMAIL || user;

  if (!user || !pass || !to) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: 'Email is not configured' }));
    return;
  }

  let payload;
  try {
    payload = readBody(req);
  } catch (err) {
    res.statusCode = 400;
    res.end(JSON.stringify({ error: err.message || 'Invalid JSON' }));
    return;
  }

  const versionUrl = String(payload.version_url || payload.link || '').trim();
  const hardware = String(payload.hardware || payload.specs || '').trim();
  const speed = String(payload.speed || payload.decode || '').trim();
  const kvCtx = payload.kv_ctx != null ? payload.kv_ctx : payload.context;
  const hasKvCtx = kvCtx != null && String(kvCtx).trim() !== '' && Number.isFinite(Number(kvCtx));

  if (!versionUrl || !hardware || !speed || !hasKvCtx) {
    res.statusCode = 400;
    res.end(JSON.stringify({
      error: 'Link, hardware, decode speed, and context length are required',
      received: Object.keys(payload || {}),
    }));
    return;
  }

  // Normalize onto expected keys for the email body.
  payload.version_url = versionUrl;
  payload.hardware = hardware;
  payload.speed = speed;
  payload.kv_ctx = Number(kvCtx);

  const submitter = String(payload.email || '').trim();
  const model = String(payload.model || '').trim() || 'setup';
  const subject = `PLM List setup: ${model} on ${hardware}`;

  try {
    const transporter = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 465,
      secure: true,
      auth: { user, pass },
    });

    await transporter.sendMail({
      from: `"PLM List" <${user}>`,
      to,
      replyTo: submitter || undefined,
      subject,
      text: formatBody(payload),
    });

    res.statusCode = 200;
    res.end(JSON.stringify({ ok: true }));
  } catch (err) {
    console.error('submit mail failed', err);
    res.statusCode = 502;
    res.end(JSON.stringify({ error: 'Failed to send email' }));
  }
};
