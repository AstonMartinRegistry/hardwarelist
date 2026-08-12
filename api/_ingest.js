const { supabaseFetch } = require('./_supabase');

function bestBody(post) {
  const discussion = post.discussion || {};
  return (
    discussion.postBody ||
    discussion.crosspostBody ||
    null
  );
}

function toPostRow(post, snapshot) {
  const discussion = post.discussion || {};
  const externalId = String(post.id);
  return {
    id: `reddit:${externalId}`,
    source: 'reddit',
    external_id: externalId,
    subreddit: snapshot.subreddit || null,
    ranking: snapshot.ranking || null,
    title: post.title || '',
    body: bestBody(post),
    post_body: discussion.postBody ?? null,
    crosspost_url: discussion.crosspostUrl ?? null,
    crosspost_body: discussion.crosspostBody ?? null,
    score: post.score ?? null,
    comment_count: post.commentCount ?? null,
    post_url: post.postUrl,
    outbound_url: post.outboundUrl ?? null,
    is_self: Boolean(post.isSelf),
    listings: Array.isArray(post.listings) ? post.listings : [],
    raw: post,
    source_created_at: post.createdAt || null,
    fetched_at: snapshot.fetchedAt || new Date().toISOString(),
  };
}

function prefer(next, prev) {
  if (next == null || next === '') return prev ?? null;
  return next;
}

function mergePostRow(incoming, existing) {
  if (!existing) return incoming;
  const incomingHasDiscussion = Boolean(
    incoming.raw && incoming.raw.discussion,
  );
  return {
    ...existing,
    ...incoming,
    title: prefer(incoming.title, existing.title) || '',
    body: prefer(incoming.body, existing.body),
    post_body: prefer(incoming.post_body, existing.post_body),
    crosspost_url: prefer(incoming.crosspost_url, existing.crosspost_url),
    crosspost_body: prefer(incoming.crosspost_body, existing.crosspost_body),
    score: incoming.score ?? existing.score ?? null,
    comment_count: incoming.comment_count ?? existing.comment_count ?? null,
    outbound_url: prefer(incoming.outbound_url, existing.outbound_url),
    listings: (incoming.listings && incoming.listings.length)
      ? incoming.listings
      : (existing.listings || []),
    // Keep richer raw (prefer payload that includes discussion)
    raw: incomingHasDiscussion ? incoming.raw : (existing.raw || incoming.raw),
    source_created_at: prefer(incoming.source_created_at, existing.source_created_at),
    fetched_at: incoming.fetched_at || existing.fetched_at,
    ranking: prefer(incoming.ranking, existing.ranking),
    subreddit: prefer(incoming.subreddit, existing.subreddit),
  };
}

function toCandidateStub(postId) {
  return {
    post_id: postId,
    is_news: false,
    kind: null,
    confidence: null,
    summary: null,
    model: null,
    quant: null,
    hardware: null,
    speed: null,
    price: null,
    context: null,
    version_url: null,
    info: null,
    extracted: {},
    classifier_model: null,
    status: 'pending',
  };
}

async function fetchExistingPosts(ids) {
  if (!ids.length) return new Map();
  // PostgREST: id=in.(a,b,c)
  const list = ids.map((id) => `"${id.replace(/"/g, '')}"`).join(',');
  const rows = await supabaseFetch(
    `ingest_posts?select=*&id=in.(${list})`,
  );
  return new Map((rows || []).map((r) => [r.id, r]));
}

async function upsertSnapshot(snapshot) {
  const posts = Array.isArray(snapshot.posts) ? snapshot.posts : [];
  if (!posts.length) {
    return { upserted: 0, candidates: 0 };
  }

  const incoming = posts.map((p) => toPostRow(p, snapshot));
  const existing = await fetchExistingPosts(incoming.map((r) => r.id));
  const rows = incoming.map((row) => mergePostRow(row, existing.get(row.id)));

  await supabaseFetch('ingest_posts?on_conflict=id', {
    method: 'POST',
    prefer: 'resolution=merge-duplicates,return=minimal',
    body: rows,
  });

  const stubs = rows.map((r) => toCandidateStub(r.id));
  // Do not overwrite existing candidate edits on re-ingest
  await supabaseFetch('ingest_candidates?on_conflict=post_id', {
    method: 'POST',
    prefer: 'resolution=ignore-duplicates,return=minimal',
    body: stubs,
  });

  return { upserted: rows.length, candidates: stubs.length };
}

module.exports = {
  bestBody,
  toPostRow,
  toCandidateStub,
  upsertSnapshot,
};
