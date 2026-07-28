const nodemailer = require('nodemailer');

function parseBody(req) {
  const value = req.body;
  if (value == null) return {};
  if (Buffer.isBuffer(value)) {
    const raw = value.toString('utf8').trim();
    return raw ? JSON.parse(raw) : {};
  }
  if (typeof value === 'string') {
    const raw = value.trim();
    return raw ? JSON.parse(raw) : {};
  }
  if (typeof value === 'object') return value;
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

function errInfo(err) {
  return {
    message: String((err && err.message) || err || 'unknown'),
    code: err && err.code != null ? String(err.code) : undefined,
    response: err && err.response != null ? String(err.response) : undefined,
    responseCode: err && err.responseCode != null ? err.responseCode : undefined,
    command: err && err.command != null ? String(err.command) : undefined,
  };
}

function withTimeout(promise, ms, message) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(Object.assign(new Error(message), { code: 'ETIMEDOUT' }));
    }, ms);
    promise.then(
      (value) => { clearTimeout(timer); resolve(value); },
      (err) => { clearTimeout(timer); reject(err); },
    );
  });
}

async function sendWithGmail({ user, pass, to, submitter, subject, text }) {
  const attempts = [
    { host: 'smtp.gmail.com', port: 465, secure: true, family: 4 },
    { host: 'smtp.gmail.com', port: 587, secure: false, requireTLS: true, family: 4 },
  ];

  let lastErr;
  for (const opts of attempts) {
    try {
      const transporter = nodemailer.createTransport({
        ...opts,
        auth: { user, pass },
        connectionTimeout: 8000,
        greetingTimeout: 8000,
        socketTimeout: 12000,
        tls: { servername: 'smtp.gmail.com', minVersion: 'TLSv1.2' },
      });
      const info = await transporter.sendMail({
        from: `"PLM List" <${user}>`,
        to,
        replyTo: submitter || undefined,
        subject,
        text,
      });
      return info;
    } catch (err) {
      lastErr = err;
      console.error('smtp attempt failed', opts.port, errInfo(err));
      if (err && err.code === 'EAUTH') break;
    }
  }
  throw lastErr || new Error('SMTP failed');
}

module.exports = async function handler(req, res) {
  const json = (code, body) => {
    res.statusCode = code;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(body));
  };

  try {
    if (req.method === 'OPTIONS') {
      res.statusCode = 204;
      res.end();
      return;
    }

    if (req.method === 'GET') {
      const configured = Boolean(
        process.env.SENDER_EMAIL
        && process.env.SENDER_PASSWORD
        && (process.env.RECEIVER_EMAIL || process.env.SENDER_EMAIL)
      );
      return json(200, { ok: true, configured });
    }

    if (req.method !== 'POST') {
      res.setHeader('Allow', 'POST, GET, OPTIONS');
      return json(405, { error: 'Method not allowed' });
    }

    const user = String(process.env.SENDER_EMAIL || '').trim();
    const pass = String(process.env.SENDER_PASSWORD || '').replace(/\s+/g, '');
    const to = String(process.env.RECEIVER_EMAIL || user).trim();

    if (!user || !pass || !to) {
      return json(500, { error: 'Email is not configured on the server' });
    }

    let payload;
    try {
      payload = parseBody(req);
    } catch (_) {
      return json(400, { error: 'Invalid JSON' });
    }

    const versionUrl = String(payload.version_url || payload.link || '').trim();
    const hardware = String(payload.hardware || payload.specs || '').trim();
    const speed = String(payload.speed || payload.decode || '').trim();
    const kvCtx = payload.kv_ctx != null ? payload.kv_ctx : payload.context;
    const hasKvCtx = kvCtx != null && String(kvCtx).trim() !== '' && Number.isFinite(Number(kvCtx));

    if (!versionUrl || !hardware || !speed || !hasKvCtx) {
      return json(400, {
        error: 'Link, hardware, decode speed, and context length are required',
        received: Object.keys(payload || {}),
      });
    }

    payload.version_url = versionUrl;
    payload.hardware = hardware;
    payload.speed = speed;
    payload.kv_ctx = Number(kvCtx);

    const submitter = String(payload.email || '').trim();
    const model = String(payload.model || '').trim() || 'setup';
    const subject = `PLM List setup: ${model} on ${hardware}`;

    await withTimeout(
      sendWithGmail({
        user,
        pass,
        to,
        submitter,
        subject,
        text: formatBody(payload),
      }),
      25000,
      'Email server timed out, please try again',
    );

    return json(200, { ok: true });
  } catch (err) {
    console.error('submit failed', errInfo(err));
    return json(502, {
      error: 'Failed to send email',
      detail: errInfo(err),
    });
  }
};
