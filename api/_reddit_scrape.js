const cheerio = require('cheerio');

const MAX_HTML_BYTES = 2_000_000;
const MAX_POST_BODY_LENGTH = 20_000;
const MAX_COMMENT_BODY_LENGTH = 5_000;
const DISCUSSION_CONCURRENCY = 3;
const DEFAULT_SUBREDDIT = 'LocalLLM';
const USER_AGENT = 'plmlist-reddit-scraper/0.1 (+https://plmlist.com)';

function normalizeExtractedText(value, maxLength) {
  return String(value || '')
    .replace(/\r/g, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/ *\n+ */g, '\n')
    .trim()
    .slice(0, maxLength);
}

function mdText($, root) {
  if (!root || !root.length) return '';
  const clone = root.clone();
  clone.find('br').replaceWith('\n');
  clone.find('p, li, div').each((_, el) => {
    const node = $(el);
    node.append('\n');
  });
  return clone.text();
}

function requiredAttr($el, name) {
  const value = $el.attr(name);
  if (value == null) throw new Error(`Old Reddit post is missing attribute: ${name}`);
  return value;
}

function intAttr($el, name) {
  const value = Number.parseInt(requiredAttr($el, name), 10);
  if (!Number.isInteger(value)) {
    throw new Error(`Old Reddit post has invalid integer attribute: ${name}`);
  }
  return value;
}

function boolAttr($el, name) {
  const value = requiredAttr($el, name);
  if (value !== 'true' && value !== 'false') {
    throw new Error(`Old Reddit post has invalid boolean attribute: ${name}`);
  }
  return value === 'true';
}

function parseListingHtml(html, { subreddit, listing, window, fetchedAt }) {
  if (html.length > MAX_HTML_BYTES) {
    throw new Error('Old Reddit listing is unexpectedly large');
  }
  const $ = cheerio.load(html);
  const posts = [];

  $('#siteTable > .thing').each((_, el) => {
    const $el = $(el);
    if ($el.attr('data-promoted') === 'true') return;

    const classes = String($el.attr('class') || '').split(/\s+/);
    const fullname = requiredAttr($el, 'data-fullname');
    const domain = requiredAttr($el, 'data-domain');
    const permalink = requiredAttr($el, 'data-permalink');
    const title = $el.find('p.title > a.title').first().text().trim();
    if (!title) return;

    posts.push({
      rank: intAttr($el, 'data-rank'),
      id: fullname.replace(/^t3_/, ''),
      title,
      score: intAttr($el, 'data-score'),
      commentCount: intAttr($el, 'data-comments-count'),
      createdAt: new Date(intAttr($el, 'data-timestamp')).toISOString(),
      postUrl: new URL(permalink, 'https://www.reddit.com').toString(),
      outboundUrl: requiredAttr($el, 'data-url'),
      isSelf: domain.startsWith('self.'),
      isNsfw: boolAttr($el, 'data-nsfw'),
      isSpoiler: boolAttr($el, 'data-spoiler'),
      isStickied: classes.includes('stickied'),
      listings: [listing],
    });
  });

  if (!posts.length) {
    throw new Error('Old Reddit listing contained no posts');
  }

  return {
    schemaVersion: 1,
    source: 'reddit',
    subreddit,
    ranking: listing,
    window: listing === 'top' ? window : null,
    fetchedAt: (fetchedAt || new Date()).toISOString(),
    posts,
  };
}

function parseDiscussionHtml(html, commentLimit) {
  if (html.length > MAX_HTML_BYTES) {
    throw new Error('Old Reddit discussion is unexpectedly large');
  }
  const $ = cheerio.load(html);
  const bodyRoot = $('#siteTable > .thing.link.self > .entry .usertext-body > .md').first();
  const postBody = normalizeExtractedText(mdText($, bodyRoot), MAX_POST_BODY_LENGTH);

  const comments = [];
  $('.commentarea > .sitetable > .thing.comment').each((_, el) => {
    if (comments.length >= commentLimit) return false;
    const $el = $(el);
    const classes = String($el.attr('class') || '').split(/\s+/);
    if (classes.includes('stickied')) return;

    const fullname = $el.attr('data-fullname');
    const permalink = $el.attr('data-permalink');
    if (!fullname || !permalink) return;

    const scoreTitle = $el.find('> .entry > .tagline > .score.unvoted').attr('title');
    const parsedScore = scoreTitle != null ? Number.parseInt(scoreTitle, 10) : NaN;
    const datetime = $el.find('> .entry > .tagline > time').attr('datetime');
    const ts = datetime ? Date.parse(datetime) : NaN;
    const body = normalizeExtractedText(
      mdText($, $el.find('> .entry .usertext-body > .md').first()),
      MAX_COMMENT_BODY_LENGTH,
    );
    if (!body) return;

    comments.push({
      id: fullname.replace(/^t1_/, ''),
      body,
      score: Number.isInteger(parsedScore) ? parsedScore : null,
      createdAt: Number.isNaN(ts) ? null : new Date(ts).toISOString(),
      postUrl: new URL(permalink, 'https://www.reddit.com').toString(),
      isStickied: false,
    });
  });

  return {
    postBody: postBody.length ? postBody : null,
    comments,
  };
}

function resolveCrosspostUrl(outboundUrl, postUrl) {
  try {
    const outbound = new URL(outboundUrl, postUrl);
    if (!/(^|\.)reddit\.com$/i.test(outbound.hostname)) return null;
    const outboundMatch = outbound.pathname.match(/^\/r\/[^/]+\/comments\/([a-z0-9]+)\//i);
    if (!outboundMatch) return null;
    const postMatch = new URL(postUrl).pathname.match(/\/comments\/([a-z0-9]+)\//i);
    if (postMatch && postMatch[1].toLowerCase() === outboundMatch[1].toLowerCase()) {
      return null;
    }
    outbound.hash = '';
    outbound.search = '';
    outbound.hostname = 'www.reddit.com';
    outbound.protocol = 'https:';
    return outbound.toString();
  } catch {
    return null;
  }
}

function oldRedditDiscussionUrl(postUrl, commentLimit) {
  const url = new URL(postUrl);
  url.hostname = 'old.reddit.com';
  url.searchParams.set('sort', 'top');
  url.searchParams.set('limit', String(Math.max(1, commentLimit)));
  return url;
}

async function fetchHtml(url, label) {
  const response = await fetch(url, {
    headers: {
      Accept: 'text/html',
      'User-Agent': USER_AGENT,
    },
    redirect: 'follow',
  });
  if (!response.ok) {
    throw new Error(`${label} failed with HTTP ${response.status}`);
  }
  const type = response.headers.get('Content-Type') || '';
  if (!type.includes('text/html')) {
    throw new Error(`${label} returned a non-HTML response`);
  }
  return response.text();
}

async function mapWithConcurrency(items, concurrency, task) {
  let nextIndex = 0;
  const workers = Array.from(
    { length: Math.min(concurrency, items.length) },
    async () => {
      while (nextIndex < items.length) {
        const item = items[nextIndex];
        nextIndex += 1;
        await task(item);
      }
    },
  );
  await Promise.all(workers);
}

async function scrapeListing({ subreddit, listing, window, limit }) {
  const url = new URL(
    `https://old.reddit.com/r/${encodeURIComponent(subreddit)}/${listing}/`,
  );
  if (listing === 'top') {
    if (!window) throw new Error('Top listings require a time window');
    url.searchParams.set('sort', 'top');
    url.searchParams.set('t', window);
  }
  url.searchParams.set('limit', String(limit));

  const html = await fetchHtml(url, `Old Reddit ${listing} listing request`);
  return parseListingHtml(html, {
    subreddit,
    listing,
    window: listing === 'top' ? window : null,
    fetchedAt: new Date(),
  });
}

function mergeSnapshots(top, newest, window) {
  const byId = new Map();
  for (const post of top.posts) {
    byId.set(post.id, { ...post, listings: [...post.listings] });
  }
  for (const post of newest.posts) {
    const existing = byId.get(post.id);
    if (existing) {
      if (!existing.listings.includes('new')) {
        existing.listings = [...existing.listings, 'new'];
      }
    } else {
      byId.set(post.id, { ...post, listings: [...post.listings] });
    }
  }
  const posts = [...byId.values()].map((post, index) => ({
    ...post,
    rank: index + 1,
  }));
  return {
    schemaVersion: 1,
    source: 'reddit',
    subreddit: top.subreddit,
    ranking: 'both',
    window,
    fetchedAt: new Date().toISOString(),
    posts,
  };
}

async function enrichDiscussions(snapshot, { offset, postLimit, commentLimit }) {
  const selected = snapshot.posts.slice(offset, offset + postLimit);
  let successfulPosts = 0;

  await mapWithConcurrency(selected, DISCUSSION_CONCURRENCY, async (post) => {
    try {
      const html = await fetchHtml(
        oldRedditDiscussionUrl(post.postUrl, commentLimit),
        `Old Reddit discussion request for ${post.id}`,
      );
      const discussion = parseDiscussionHtml(html, commentLimit);
      post.discussion = discussion;
      successfulPosts += 1;

      const crosspostUrl = resolveCrosspostUrl(post.outboundUrl, post.postUrl);
      if (crosspostUrl) {
        discussion.crosspostUrl = crosspostUrl;
        try {
          const crossHtml = await fetchHtml(
            oldRedditDiscussionUrl(crosspostUrl, 0),
            `Old Reddit crosspost request for ${post.id}`,
          );
          const cross = parseDiscussionHtml(crossHtml, 0);
          discussion.crosspostBody = cross.postBody;
        } catch (error) {
          discussion.crosspostBody = null;
          discussion.crosspostError = error instanceof Error ? error.message : String(error);
        }
      }
    } catch (error) {
      post.discussion = {
        postBody: null,
        comments: [],
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });

  snapshot.enrichment = {
    mode: 'discussion',
    offset,
    requestedPosts: selected.length,
    successfulPosts,
    commentsPerPost: commentLimit,
  };
}

/**
 * Scrape r/LocalLLM (or override) from old.reddit.com HTML.
 * @param {object} opts
 * @param {'new'|'top'|'both'} [opts.ranking='new']
 * @param {'day'|'week'|'month'|null} [opts.window='week']
 * @param {number} [opts.limit=25]
 * @param {boolean} [opts.includeDiscussion=true]
 * @param {number} [opts.posts] discussion enrichment count
 * @param {number} [opts.comments=0]
 * @param {number} [opts.offset=0]
 * @param {string} [opts.subreddit='LocalLLM']
 */
async function scrapeReddit(opts = {}) {
  const ranking = opts.ranking || 'new';
  const window = opts.window || 'week';
  const limit = Math.min(50, Math.max(1, Number(opts.limit) || 25));
  const includeDiscussion = opts.includeDiscussion !== false;
  const postLimit = Math.min(25, Math.max(1, Number(opts.posts) || limit));
  const commentLimit = Math.min(10, Math.max(0, Number(opts.comments) || 0));
  const offset = Math.min(limit - 1, Math.max(0, Number(opts.offset) || 0));
  const subreddit = opts.subreddit || process.env.REDDIT_SUBREDDIT || DEFAULT_SUBREDDIT;

  let snapshot;
  if (ranking === 'top') {
    snapshot = await scrapeListing({ subreddit, listing: 'top', window, limit });
  } else if (ranking === 'both') {
    const [top, newest] = await Promise.all([
      scrapeListing({ subreddit, listing: 'top', window, limit }),
      scrapeListing({ subreddit, listing: 'new', window: null, limit }),
    ]);
    snapshot = mergeSnapshots(top, newest, window);
  } else {
    snapshot = await scrapeListing({ subreddit, listing: 'new', window: null, limit });
  }

  if (includeDiscussion) {
    await enrichDiscussions(snapshot, { offset, postLimit, commentLimit });
  }
  return snapshot;
}

module.exports = {
  scrapeReddit,
  parseListingHtml,
  parseDiscussionHtml,
  resolveCrosspostUrl,
  USER_AGENT,
  DEFAULT_SUBREDDIT,
};
