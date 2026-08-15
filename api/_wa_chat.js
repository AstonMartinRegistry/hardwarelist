const { cerebrasChat, cerebrasConfig } = require('./_cerebras');
const { supabaseFetch } = require('./_supabase');
const { publishCandidate, skipCandidate } = require('./_publish');
const { shortId } = require('./_alert');

const NULLABLE_STRING = { anyOf: [{ type: 'string' }, { type: 'null' }] };

const CHAT_SCHEMA = {
  type: 'object',
  properties: {
    reply: {
      type: 'string',
      description: 'Message to send back on WhatsApp (concise).',
    },
    action: {
      type: 'string',
      enum: ['none', 'update', 'publish', 'skip', 'focus_next'],
    },
    fields: {
      type: 'object',
      properties: {
        model: NULLABLE_STRING,
        quant: NULLABLE_STRING,
        hardware: NULLABLE_STRING,
        speed: NULLABLE_STRING,
        price: NULLABLE_STRING,
        context: NULLABLE_STRING,
        version_url: NULLABLE_STRING,
        info: NULLABLE_STRING,
        notes: NULLABLE_STRING,
      },
      required: [
        'model',
        'quant',
        'hardware',
        'speed',
        'price',
        'context',
        'version_url',
        'info',
        'notes',
      ],
      additionalProperties: false,
    },
  },
  required: ['reply', 'action', 'fields'],
  additionalProperties: false,
};

const SYSTEM_PROMPT = `You are the PLM List WhatsApp editor bot.
You help the operator review Reddit news candidates and publish local-LLM setups.

You can:
- update draft fields (model, quant, hardware, speed, price, context, version_url, info, notes)
- publish the current candidate to the setups table (requires model)
- skip the candidate
- focus_next to leave this one and ask for the next alerted item

Rules:
- Keep WhatsApp replies short and scannable.
- Only put values in fields when the user asked to change them OR you are confidently filling a clearly stated missing field from the post; otherwise null.
- action=publish only when the user clearly wants to publish and model is set (or you just set it).
- action=skip only when the user wants to discard.
- Prefer action=update when editing fields; include only changed fields as non-null (unchanged = null).
- If the user asks a question, answer briefly with action=none.`;

function candidateCard(candidate, post) {
  return {
    id: candidate.id,
    short_id: shortId(candidate.id),
    status: candidate.status,
    kind: candidate.kind,
    summary: candidate.summary,
    model: candidate.model,
    quant: candidate.quant,
    hardware: candidate.hardware,
    speed: candidate.speed,
    price: candidate.price,
    context: candidate.context,
    version_url: candidate.version_url,
    info: candidate.info,
    notes: candidate.notes,
    post_title: post?.title || null,
    post_url: post?.post_url || null,
    post_body: String(post?.body || post?.post_body || '').slice(0, 6000),
  };
}

async function fetchActiveCandidate(phone) {
  // Prefer chatting, then alerted — most recently updated, for this phone's threads
  const convPath =
    `ingest_conversations?select=id,candidate_id,messages,updated_at,ingest_candidates(id,status,post_id,kind,summary,model,quant,hardware,speed,price,context,version_url,info,notes,ingest_posts(id,title,body,post_body,post_url))` +
    `&channel=eq.whatsapp&external_thread_id=eq.${encodeURIComponent(phone)}` +
    `&order=updated_at.desc&limit=10`;
  const convs = await supabaseFetch(convPath);
  for (const c of convs || []) {
    const cand = c.ingest_candidates;
    if (cand && ['alerted', 'chatting', 'classified', 'ready'].includes(cand.status)) {
      return { candidate: cand, post: cand.ingest_posts, conversation: c };
    }
  }

  // Fallback: any alerted/chatting candidate
  const path =
    'ingest_candidates?select=id,status,post_id,kind,summary,model,quant,hardware,speed,price,context,version_url,info,notes,ingest_posts(id,title,body,post_body,post_url)&status=in.(alerted,chatting)&order=updated_at.desc&limit=1';
  const rows = await supabaseFetch(path);
  const candidate = rows?.[0];
  if (!candidate) return null;
  return { candidate, post: candidate.ingest_posts, conversation: null };
}

async function appendConversation(conversation, phone, candidateId, userText, assistantText) {
  const now = new Date().toISOString();
  const prev = Array.isArray(conversation?.messages) ? conversation.messages : [];
  const messages = [
    ...prev,
    { role: 'user', content: userText, at: now },
    { role: 'assistant', content: assistantText, at: now },
  ].slice(-40);

  if (conversation?.id) {
    await supabaseFetch(
      `ingest_conversations?id=eq.${encodeURIComponent(conversation.id)}`,
      {
        method: 'PATCH',
        prefer: 'return=minimal',
        body: { messages, updated_at: now },
      },
    );
    return;
  }

  await supabaseFetch('ingest_conversations', {
    method: 'POST',
    prefer: 'return=minimal',
    body: {
      candidate_id: candidateId,
      channel: 'whatsapp',
      external_thread_id: phone,
      messages,
      updated_at: now,
    },
  });
}

async function patchCandidateFields(candidateId, fields) {
  const patch = { updated_at: new Date().toISOString(), status: 'chatting' };
  for (const key of [
    'model',
    'quant',
    'hardware',
    'speed',
    'price',
    'context',
    'version_url',
    'info',
    'notes',
  ]) {
    if (fields[key] != null && fields[key] !== '') patch[key] = fields[key];
  }
  const rows = await supabaseFetch(
    `ingest_candidates?id=eq.${encodeURIComponent(candidateId)}`,
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
      candidate_id: candidateId,
      action: 'edit',
      actor: 'whatsapp',
      detail: { patch },
    },
  });
  return Array.isArray(rows) ? rows[0] : rows;
}

function mergeFields(candidate, fields) {
  const next = { ...candidate };
  for (const key of Object.keys(fields || {})) {
    if (fields[key] != null && fields[key] !== '') next[key] = fields[key];
  }
  return next;
}

async function runChatTurn({ phone, text }) {
  const active = await fetchActiveCandidate(phone);
  if (!active) {
    return {
      reply:
        'No candidates waiting. When the classifier finds news I will alert you here.',
    };
  }

  const { candidate, post, conversation } = active;
  const lower = text.trim().toLowerCase();

  // Fast-path commands (no LLM)
  if (['publish', 'post', 'ship'].includes(lower)) {
    const merged = candidate;
    if (!merged.model) {
      return { reply: 'Need a model name before publish. Reply e.g. model: Qwen2.5-32B' };
    }
    const { setup } = await publishCandidate(merged, post);
    await appendConversation(
      conversation,
      phone,
      candidate.id,
      text,
      `Published ${setup?.model || merged.model}`,
    );
    return { reply: `✅ Published to setups (${shortId(setup?.id || candidate.id)}).` };
  }
  if (['skip', 'noise', 'ignore'].includes(lower)) {
    await skipCandidate(candidate.id, 'skipped via whatsapp');
    await appendConversation(conversation, phone, candidate.id, text, 'Skipped');
    return { reply: 'Skipped. Send next or wait for the next alert.' };
  }
  if (['next', 'status'].includes(lower)) {
    const card = candidateCard(candidate, post);
    return {
      reply: [
        `Current (${card.short_id}) [${card.status}/${card.kind}]`,
        card.summary,
        `model: ${card.model || '—'}`,
        `hardware: ${card.hardware || '—'}`,
        `speed: ${card.speed || '—'}`,
        `price: ${card.price || '—'}`,
        card.post_url || '',
      ]
        .filter(Boolean)
        .join('\n'),
    };
  }

  const { chatModel } = cerebrasConfig();
  const userPayload = {
    operator_message: text,
    current_candidate: candidateCard(candidate, post),
  };

  const { content } = await cerebrasChat({
    model: chatModel,
    reasoning_effort: 'low',
    temperature: 0.2,
    max_tokens: 1200,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: JSON.stringify(userPayload) },
    ],
    response_format: {
      type: 'json_schema',
      json_schema: {
        name: 'plmlist_wa_chat',
        strict: true,
        schema: CHAT_SCHEMA,
      },
    },
  });

  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch (err) {
    return { reply: 'Bot parse error — try: publish | skip | model: …' };
  }

  let reply = String(parsed.reply || '').trim() || 'OK';
  const action = parsed.action || 'none';
  const fields = parsed.fields || {};

  try {
    if (action === 'update' || Object.values(fields).some((v) => v != null && v !== '')) {
      await patchCandidateFields(candidate.id, fields);
    }

    if (action === 'publish') {
      const merged = mergeFields(candidate, fields);
      if (!merged.model) {
        reply = 'Need a model before publish. Tell me the model name.';
      } else {
        const { setup } = await publishCandidate(merged, post);
        reply = reply || `✅ Published (${setup?.model || merged.model}).`;
      }
    } else if (action === 'skip') {
      await skipCandidate(candidate.id, fields.notes || 'skipped via chat');
      reply = reply || 'Skipped.';
    } else if (action === 'focus_next') {
      // Leave current as alerted/chatting; operator can wait for next alert
      reply = reply || 'Alright — reply when the next alert arrives, or say status.';
    }
  } catch (err) {
    reply = `Error: ${err.message || String(err)}`;
  }

  await appendConversation(conversation, phone, candidate.id, text, reply);
  return { reply, action, candidate_id: candidate.id };
}

module.exports = {
  runChatTurn,
  fetchActiveCandidate,
  candidateCard,
};
