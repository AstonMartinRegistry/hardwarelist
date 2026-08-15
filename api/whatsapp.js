const {
  whatsappConfig,
  verifyWebhookChallenge,
  verifySignature,
  extractInboundMessages,
  isAllowedSender,
  sendWhatsAppText,
  readRawBody,
} = require('./_whatsapp');
const { runChatTurn } = require('./_wa_chat');

// Need raw body for Meta signature verification when possible
module.exports.config = {
  api: {
    bodyParser: false,
  },
};

module.exports = async function handler(req, res) {
  if (req.method === 'GET') {
    if (req.query?.health === '1' || req.query?.health === 'true') {
      const cfg = whatsappConfig();
      return res.status(200).json({
        ok: true,
        configured: Boolean(cfg.token && cfg.phoneNumberId && cfg.to),
        hasVerifyToken: Boolean(cfg.verifyToken),
        hasAppSecret: Boolean(cfg.appSecret),
        to: cfg.to ? `${cfg.to.slice(0, 4)}…` : null,
      });
    }

    const challenge = verifyWebhookChallenge(req.query || {});
    if (challenge != null) {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'text/plain');
      return res.end(String(challenge));
    }
    return res.status(403).json({ error: 'Verification failed' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const rawBody = await readRawBody(req);
    const signature = req.headers['x-hub-signature-256'];
    if (!verifySignature(rawBody, signature)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    let payload;
    try {
      payload = JSON.parse(rawBody || '{}');
    } catch {
      return res.status(400).json({ error: 'Invalid JSON' });
    }

    // Ack fast; process messages sequentially in this invocation
    const messages = extractInboundMessages(payload);
    const replies = [];

    for (const msg of messages) {
      if (!isAllowedSender(msg.from)) {
        replies.push({ from: msg.from, skipped: true, reason: 'not allowlisted' });
        continue;
      }
      try {
        const { reply } = await runChatTurn({ phone: msg.from, text: msg.text });
        if (reply) {
          await sendWhatsAppText(msg.from, reply);
        }
        replies.push({ from: msg.from, ok: true });
      } catch (err) {
        try {
          await sendWhatsAppText(
            msg.from,
            `Bot error: ${err.message || 'failed'}`,
          );
        } catch {
          /* ignore secondary send failure */
        }
        replies.push({ from: msg.from, ok: false, error: err.message });
      }
    }

    return res.status(200).json({ ok: true, handled: messages.length, replies });
  } catch (err) {
    return res.status(err.status || 500).json({
      error: err.message || 'WhatsApp webhook failed',
      detail: err.detail || undefined,
    });
  }
};
