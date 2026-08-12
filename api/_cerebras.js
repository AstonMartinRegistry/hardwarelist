/** Thin Cerebras chat-completions client (OpenAI-compatible). */

const CEREBRAS_BASE = 'https://api.cerebras.ai/v1';

function cerebrasConfig() {
  const apiKey = process.env.CEREBRAS_API_KEY || '';
  const classifyModel =
    process.env.CEREBRAS_CLASSIFY_MODEL || 'gpt-oss-120b';
  const chatModel = process.env.CEREBRAS_CHAT_MODEL || 'zai-glm-4.7';
  return { apiKey, classifyModel, chatModel };
}

/**
 * @param {object} opts
 * @param {string} opts.model
 * @param {Array<{role: string, content: string}>} opts.messages
 * @param {object} [opts.response_format]
 * @param {string} [opts.reasoning_effort]
 * @param {number} [opts.temperature]
 * @param {number} [opts.max_tokens]
 */
async function cerebrasChat(opts) {
  const { apiKey } = cerebrasConfig();
  if (!apiKey) {
    const err = new Error('CEREBRAS_API_KEY is not configured');
    err.status = 500;
    throw err;
  }

  const body = {
    model: opts.model,
    messages: opts.messages,
  };
  if (opts.response_format) body.response_format = opts.response_format;
  if (opts.reasoning_effort) body.reasoning_effort = opts.reasoning_effort;
  if (opts.temperature != null) body.temperature = opts.temperature;
  if (opts.max_tokens != null) body.max_tokens = opts.max_tokens;

  const res = await fetch(`${CEREBRAS_BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const msg =
      (data && typeof data === 'object' && (data.message || data.error?.message)) ||
      `Cerebras ${res.status}`;
    const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    err.status = res.status;
    err.detail = data;
    throw err;
  }

  const content = data?.choices?.[0]?.message?.content;
  if (content == null || content === '') {
    const err = new Error('Cerebras returned empty content');
    err.status = 502;
    err.detail = data;
    throw err;
  }

  return { content: String(content), raw: data };
}

module.exports = {
  cerebrasConfig,
  cerebrasChat,
};
