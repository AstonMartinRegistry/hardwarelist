const crypto = require('crypto');

function whatsappConfig() {
  return {
    token: process.env.WHATSAPP_ACCESS_TOKEN || '',
    phoneNumberId: process.env.WHATSAPP_PHONE_NUMBER_ID || '',
    verifyToken: process.env.WHATSAPP_VERIFY_TOKEN || '',
    appSecret: process.env.WHATSAPP_APP_SECRET || '',
    to: normalizePhone(process.env.WHATSAPP_TO_NUMBER || ''),
    allowlist: String(process.env.WHATSAPP_ALLOWLIST || process.env.WHATSAPP_TO_NUMBER || '')
      .split(',')
      .map((s) => normalizePhone(s))
      .filter(Boolean),
    apiVersion: process.env.WHATSAPP_API_VERSION || 'v21.0',
  };
}

function normalizePhone(value) {
  return String(value || '').replace(/[^\d]/g, '');
}

function isAllowedSender(from) {
  const { allowlist } = whatsappConfig();
  const phone = normalizePhone(from);
  if (!allowlist.length) return true;
  return allowlist.includes(phone);
}

function verifyWebhookChallenge(query) {
  const { verifyToken } = whatsappConfig();
  const mode = query['hub.mode'];
  const token = query['hub.verify_token'];
  const challenge = query['hub.challenge'];
  if (mode === 'subscribe' && token && verifyToken && token === verifyToken) {
    return challenge;
  }
  return null;
}

function verifySignature(rawBody, signatureHeader) {
  const { appSecret } = whatsappConfig();
  if (!appSecret) return true; // optional in early setup
  if (!signatureHeader || !rawBody) return false;
  const expected =
    'sha256=' +
    crypto.createHmac('sha256', appSecret).update(rawBody).digest('hex');
  try {
    const a = Buffer.from(expected);
    const b = Buffer.from(String(signatureHeader));
    if (a.length !== b.length) return false;
    return crypto.timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

async function sendWhatsAppText(to, text) {
  const { token, phoneNumberId, apiVersion } = whatsappConfig();
  if (!token || !phoneNumberId) {
    const err = new Error('WhatsApp is not configured (token / phone number id)');
    err.status = 500;
    throw err;
  }
  const phone = normalizePhone(to);
  if (!phone) {
    const err = new Error('WhatsApp recipient number missing');
    err.status = 400;
    throw err;
  }

  const url = `https://graph.facebook.com/${apiVersion}/${phoneNumberId}/messages`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messaging_product: 'whatsapp',
      to: phone,
      type: 'text',
      text: { preview_url: true, body: String(text || '').slice(0, 4096) },
    }),
  });

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(
      data?.error?.message || `WhatsApp send failed (${res.status})`,
    );
    err.status = res.status;
    err.detail = data;
    throw err;
  }
  return data;
}

function extractInboundMessages(payload) {
  const out = [];
  const entries = payload?.entry || [];
  for (const entry of entries) {
    for (const change of entry.changes || []) {
      const value = change.value || {};
      const contacts = value.contacts || [];
      const contactName = contacts[0]?.profile?.name || null;
      for (const msg of value.messages || []) {
        if (msg.type !== 'text' || !msg.text?.body) continue;
        out.push({
          id: msg.id,
          from: normalizePhone(msg.from),
          timestamp: msg.timestamp,
          text: String(msg.text.body).trim(),
          contactName,
        });
      }
    }
  }
  return out;
}

async function readRawBody(req) {
  if (typeof req.body === 'string') return req.body;
  if (Buffer.isBuffer(req.body)) return req.body.toString('utf8');
  if (req.body && typeof req.body === 'object') {
    return JSON.stringify(req.body);
  }
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

module.exports = {
  whatsappConfig,
  normalizePhone,
  isAllowedSender,
  verifyWebhookChallenge,
  verifySignature,
  sendWhatsAppText,
  extractInboundMessages,
  readRawBody,
};
