const MAX_HTML_BYTES = 2_000_000;
const MAX_LISTING_POSTS = 50;
const MAX_ENRICHED_POSTS = 25;
const MAX_COMMENTS_PER_POST = 10;
const DISCUSSION_CONCURRENCY = 3;
const MAX_POST_BODY_LENGTH = 20_000;
const MAX_COMMENT_BODY_LENGTH = 5_000;
const SUPPORTED_WINDOWS = ["day", "week", "month"] as const;
const SUPPORTED_LISTINGS = ["top", "new"] as const;
const SUPPORTED_RANKINGS = ["top", "new", "both"] as const;

export type RedditWindow = (typeof SUPPORTED_WINDOWS)[number];
export type RedditListing = (typeof SUPPORTED_LISTINGS)[number];
export type RedditRanking = (typeof SUPPORTED_RANKINGS)[number];

type DraftPost = RedditPost & { title: string };
type DraftComment = RedditComment & { body: string };

export interface RedditComment {
  id: string;
  body: string;
  score: number | null;
  createdAt: string | null;
  postUrl: string;
  isStickied: boolean;
}

export interface RedditDiscussion {
  postBody: string | null;
  comments: RedditComment[];
  /** Absolute Reddit URL of a linked/crossposted thread, when outboundUrl points elsewhere. */
  crosspostUrl?: string;
  /** Selftext body from that crossposted thread (null if link-only or missing). */
  crosspostBody?: string | null;
  crosspostError?: string;
  error?: string;
}

export interface RedditPost {
  rank: number;
  id: string;
  title: string;
  score: number;
  commentCount: number;
  createdAt: string;
  postUrl: string;
  outboundUrl: string;
  isSelf: boolean;
  isNsfw: boolean;
  isSpoiler: boolean;
  isStickied: boolean;
  listings: RedditListing[];
  discussion?: RedditDiscussion;
}

export interface RedditSnapshot {
  schemaVersion: 1;
  source: "reddit";
  subreddit: string;
  ranking: RedditRanking;
  window: RedditWindow | null;
  fetchedAt: string;
  enrichment?: {
    mode: "discussion";
    offset: number;
    requestedPosts: number;
    successfulPosts: number;
    commentsPerPost: number;
  };
  posts: RedditPost[];
}

interface DiscussionOptions {
  offset: number;
  postLimit: number;
  commentLimit: number;
}

function requiredAttribute(element: Element, name: string): string {
  const value = element.getAttribute(name);
  if (value === null) {
    throw new Error(`Old Reddit post is missing attribute: ${name}`);
  }
  return value;
}

function integerAttribute(element: Element, name: string): number {
  const rawValue = requiredAttribute(element, name);
  const value = Number.parseInt(rawValue, 10);
  if (!Number.isInteger(value)) {
    throw new Error(`Old Reddit post has invalid integer attribute: ${name}`);
  }
  return value;
}

function booleanAttribute(element: Element, name: string): boolean {
  const value = requiredAttribute(element, name);
  if (value !== "true" && value !== "false") {
    throw new Error(`Old Reddit post has invalid boolean attribute: ${name}`);
  }
  return value === "true";
}

function postFromElement(element: Element): DraftPost | undefined {
  if (element.getAttribute("data-promoted") === "true") {
    return undefined;
  }

  const fullname = requiredAttribute(element, "data-fullname");
  const timestamp = integerAttribute(element, "data-timestamp");
  const permalink = requiredAttribute(element, "data-permalink");
  const classes = element.getAttribute("class")?.split(/\s+/) ?? [];
  const domain = requiredAttribute(element, "data-domain");

  return {
    rank: integerAttribute(element, "data-rank"),
    id: fullname.replace(/^t3_/, ""),
    title: "",
    score: integerAttribute(element, "data-score"),
    commentCount: integerAttribute(element, "data-comments-count"),
    createdAt: new Date(timestamp).toISOString(),
    postUrl: new URL(permalink, "https://www.reddit.com").toString(),
    outboundUrl: requiredAttribute(element, "data-url"),
    isSelf: domain.startsWith("self."),
    isNsfw: booleanAttribute(element, "data-nsfw"),
    isSpoiler: booleanAttribute(element, "data-spoiler"),
    isStickied: classes.includes("stickied"),
    listings: [],
  };
}

function assertBoundedHtml(response: Response, label: string): void {
  const contentLength = response.headers.get("Content-Length");
  if (contentLength !== null && Number(contentLength) > MAX_HTML_BYTES) {
    throw new Error(`${label} is unexpectedly large`);
  }
}

async function consumeTransformedResponse(response: Response, label: string): Promise<void> {
  if (!response.body) {
    throw new Error(`${label} returned an empty response`);
  }
  await response.body.pipeTo(new WritableStream());
}

function normalizeExtractedText(value: string, maxLength: number): string {
  return decodeHtmlEntities(value)
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/ *\n+ */g, "\n")
    .trim()
    .slice(0, maxLength);
}

function decodeHtmlEntities(value: string): string {
  return value.replace(
    /&(#\d+|#x[\da-f]+|amp|lt|gt|quot|apos|nbsp);/gi,
    (match, entity: string) => {
      const normalized = entity.toLowerCase();
      if (normalized.startsWith("#")) {
        const radix = normalized.startsWith("#x") ? 16 : 10;
        const digits = normalized.slice(radix === 16 ? 2 : 1);
        const codePoint = Number.parseInt(digits, radix);
        if (
          Number.isInteger(codePoint)
          && codePoint >= 0
          && codePoint <= 0x10ffff
          && !(codePoint >= 0xd800 && codePoint <= 0xdfff)
        ) {
          return String.fromCodePoint(codePoint);
        }
        return match;
      }

      switch (normalized) {
        case "amp": return "&";
        case "lt": return "<";
        case "gt": return ">";
        case "quot": return '"';
        case "apos": return "'";
        case "nbsp": return " ";
        default: return match;
      }
    },
  );
}

export async function parseOldRedditListing(
  response: Response,
  subreddit: string,
  listing: RedditListing,
  window: RedditWindow | null,
  fetchedAt: Date,
): Promise<RedditSnapshot> {
  assertBoundedHtml(response, "Old Reddit listing");

  let activePost: DraftPost | undefined;
  const posts: DraftPost[] = [];

  const parsedResponse = new HTMLRewriter()
    .on("#siteTable > .thing", {
      element(element) {
        activePost = postFromElement(element);
        if (activePost) {
          posts.push(activePost);
        }
      },
    })
    .on("#siteTable > .thing p.title > a.title", {
      text(text) {
        if (activePost) {
          activePost.title += text.text;
        }
      },
    })
    .transform(response);

  await consumeTransformedResponse(parsedResponse, "Old Reddit listing");

  if (posts.length === 0) {
    throw new Error("Old Reddit listing contained no posts");
  }
  for (const post of posts) {
    post.title = post.title.trim();
    if (post.title.length === 0) {
      throw new Error(`Old Reddit post ${post.id} has no title`);
    }
    post.listings = [listing];
  }

  return {
    schemaVersion: 1,
    source: "reddit",
    subreddit,
    ranking: listing,
    window,
    fetchedAt: fetchedAt.toISOString(),
    posts,
  };
}

export async function parseOldRedditDiscussion(
  response: Response,
  commentLimit: number,
): Promise<RedditDiscussion> {
  assertBoundedHtml(response, "Old Reddit discussion");

  let postBody = "";
  let activeComment: DraftComment | undefined;
  const comments: DraftComment[] = [];

  const rewriter = new HTMLRewriter()
    .on("#siteTable > .thing.link.self > .entry .usertext-body > .md", {
      text(text) {
        postBody += text.text;
      },
    })
    .on("#siteTable > .thing.link.self > .entry .usertext-body > .md p", {
      element() {
        postBody += "\n";
      },
    })
    .on("#siteTable > .thing.link.self > .entry .usertext-body > .md li", {
      element() {
        postBody += "\n";
      },
    })
    .on("#siteTable > .thing.link.self > .entry .usertext-body > .md br", {
      element() {
        postBody += "\n";
      },
    })
    .on(".commentarea > .sitetable > .thing.comment", {
      element(element) {
        const classes = element.getAttribute("class")?.split(/\s+/) ?? [];
        if (classes.includes("stickied") || comments.length >= commentLimit) {
          activeComment = undefined;
          return;
        }

        const fullname = requiredAttribute(element, "data-fullname");
        const permalink = requiredAttribute(element, "data-permalink");
        activeComment = {
          id: fullname.replace(/^t1_/, ""),
          body: "",
          score: null,
          createdAt: null,
          postUrl: new URL(permalink, "https://www.reddit.com").toString(),
          isStickied: false,
        };
        comments.push(activeComment);
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry > .tagline > .score.unvoted", {
      element(element) {
        const score = element.getAttribute("title");
        if (activeComment && score !== null) {
          const parsedScore = Number.parseInt(score, 10);
          activeComment.score = Number.isInteger(parsedScore) ? parsedScore : null;
        }
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry > .tagline > time", {
      element(element) {
        const datetime = element.getAttribute("datetime");
        if (activeComment && datetime !== null) {
          const timestamp = Date.parse(datetime);
          activeComment.createdAt = Number.isNaN(timestamp)
            ? null
            : new Date(timestamp).toISOString();
        }
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry .usertext-body > .md", {
      text(text) {
        if (activeComment) {
          activeComment.body += text.text;
        }
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry .usertext-body > .md p", {
      element() {
        if (activeComment) {
          activeComment.body += "\n";
        }
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry .usertext-body > .md li", {
      element() {
        if (activeComment) {
          activeComment.body += "\n";
        }
      },
    })
    .on(".commentarea > .sitetable > .thing.comment > .entry .usertext-body > .md br", {
      element() {
        if (activeComment) {
          activeComment.body += "\n";
        }
      },
    });

  await consumeTransformedResponse(rewriter.transform(response), "Old Reddit discussion");

  const normalizedComments = comments
    .map((comment) => ({
      ...comment,
      body: normalizeExtractedText(comment.body, MAX_COMMENT_BODY_LENGTH),
    }))
    .filter((comment) => comment.body.length > 0);

  const normalizedPostBody = normalizeExtractedText(postBody, MAX_POST_BODY_LENGTH);
  return {
    postBody: normalizedPostBody.length > 0 ? normalizedPostBody : null,
    comments: normalizedComments,
  };
}

function parseWindow(value: string | null): RedditWindow | undefined {
  const requestedWindow = value ?? "week";
  return SUPPORTED_WINDOWS.find((window) => window === requestedWindow);
}

function parseRanking(value: string | null): RedditRanking | undefined {
  const requestedRanking = value ?? "new";
  return SUPPORTED_RANKINGS.find((ranking) => ranking === requestedRanking);
}

function parseIntegerOption(
  value: string | null,
  defaultValue: number,
  minimum: number,
  maximum: number,
): number | undefined {
  if (value === null) {
    return defaultValue;
  }
  if (!/^\d+$/.test(value)) {
    return undefined;
  }
  const parsed = Number.parseInt(value, 10);
  return parsed >= minimum && parsed <= maximum ? parsed : undefined;
}

function oldRedditUrl(postUrl: string, commentLimit: number): URL {
  const url = new URL(postUrl);
  url.hostname = "old.reddit.com";
  url.searchParams.set("sort", "top");
  url.searchParams.set("limit", String(Math.max(1, commentLimit)));
  return url;
}

/** If outboundUrl is a different Reddit comments thread, return its absolute URL. */
export function resolveCrosspostUrl(outboundUrl: string, postUrl: string): string | null {
  try {
    const outbound = new URL(outboundUrl, postUrl);
    if (!/(^|\.)reddit\.com$/i.test(outbound.hostname)) {
      return null;
    }
    const outboundMatch = outbound.pathname.match(
      /^\/r\/[^/]+\/comments\/([a-z0-9]+)\//i,
    );
    if (!outboundMatch) {
      return null;
    }
    const postMatch = new URL(postUrl).pathname.match(/\/comments\/([a-z0-9]+)\//i);
    if (postMatch && postMatch[1].toLowerCase() === outboundMatch[1].toLowerCase()) {
      return null;
    }
    outbound.hash = "";
    outbound.search = "";
    outbound.hostname = "www.reddit.com";
    outbound.protocol = "https:";
    return outbound.toString();
  } catch {
    return null;
  }
}

async function fetchRedditHtml(url: URL, env: Env, label: string): Promise<Response> {
  const response = await fetch(url, {
    headers: {
      Accept: "text/html",
      "User-Agent": env.USER_AGENT,
    },
    redirect: "follow",
  });

  if (!response.ok) {
    await response.body?.cancel();
    throw new Error(`${label} failed with HTTP ${response.status}`);
  }
  if (!response.headers.get("Content-Type")?.includes("text/html")) {
    await response.body?.cancel();
    throw new Error(`${label} returned a non-HTML response`);
  }
  return response;
}

async function scrapeListing(
  env: Env,
  listing: RedditListing,
  window: RedditWindow | null,
  listingLimit: number,
): Promise<RedditSnapshot> {
  const url = new URL(
    `https://old.reddit.com/r/${encodeURIComponent(env.SUBREDDIT)}/${listing}/`,
  );
  if (listing === "top") {
    if (!window) {
      throw new Error("Top listings require a time window");
    }
    url.searchParams.set("sort", "top");
    url.searchParams.set("t", window);
  }
  url.searchParams.set("limit", String(listingLimit));

  const response = await fetchRedditHtml(url, env, `Old Reddit ${listing} listing request`);
  console.log(JSON.stringify({
    message: "reddit rate limit observed",
    listing,
    used: response.headers.get("X-Ratelimit-Used"),
    remaining: response.headers.get("X-Ratelimit-Remaining"),
    resetSeconds: response.headers.get("X-Ratelimit-Reset"),
  }));

  return parseOldRedditListing(
    response,
    env.SUBREDDIT,
    listing,
    listing === "top" ? window : null,
    new Date(),
  );
}

function mergeSnapshots(
  top: RedditSnapshot,
  newest: RedditSnapshot,
  window: RedditWindow,
): RedditSnapshot {
  const byId = new Map<string, RedditPost>();
  for (const post of top.posts) {
    byId.set(post.id, { ...post, listings: [...post.listings] });
  }
  for (const post of newest.posts) {
    const existing = byId.get(post.id);
    if (existing) {
      if (!existing.listings.includes("new")) {
        existing.listings = [...existing.listings, "new"];
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
    source: "reddit",
    subreddit: top.subreddit,
    ranking: "both",
    window,
    fetchedAt: new Date().toISOString(),
    posts,
  };
}

async function scrapePosts(
  env: Env,
  ranking: RedditRanking,
  window: RedditWindow | null,
  listingLimit: number,
): Promise<RedditSnapshot> {
  if (ranking === "top") {
    return scrapeListing(env, "top", window, listingLimit);
  }
  if (ranking === "new") {
    return scrapeListing(env, "new", null, listingLimit);
  }

  if (!window) {
    throw new Error("Combined scrapes require a time window for top");
  }
  const [top, newest] = await Promise.all([
    scrapeListing(env, "top", window, listingLimit),
    scrapeListing(env, "new", null, listingLimit),
  ]);
  return mergeSnapshots(top, newest, window);
}

async function mapWithConcurrency<T>(
  items: T[],
  concurrency: number,
  task: (item: T) => Promise<void>,
): Promise<void> {
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

async function enrichDiscussions(
  snapshot: RedditSnapshot,
  env: Env,
  options: DiscussionOptions,
): Promise<void> {
  const selectedPosts = snapshot.posts.slice(
    options.offset,
    options.offset + options.postLimit,
  );
  let successfulPosts = 0;

  await mapWithConcurrency(selectedPosts, DISCUSSION_CONCURRENCY, async (post) => {
    try {
      const response = await fetchRedditHtml(
        oldRedditUrl(post.postUrl, options.commentLimit),
        env,
        `Old Reddit discussion request for ${post.id}`,
      );
      const discussion = await parseOldRedditDiscussion(response, options.commentLimit);
      post.discussion = discussion;
      successfulPosts += 1;

      const crosspostUrl = resolveCrosspostUrl(post.outboundUrl, post.postUrl);
      if (crosspostUrl) {
        discussion.crosspostUrl = crosspostUrl;
        try {
          const crossResponse = await fetchRedditHtml(
            oldRedditUrl(crosspostUrl, 0),
            env,
            `Old Reddit crosspost request for ${post.id}`,
          );
          const crossDiscussion = await parseOldRedditDiscussion(crossResponse, 0);
          discussion.crosspostBody = crossDiscussion.postBody;
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          discussion.crosspostBody = null;
          discussion.crosspostError = message;
          console.error(JSON.stringify({
            message: "reddit crosspost enrichment failed",
            postId: post.id,
            crosspostUrl,
            error: message,
          }));
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      post.discussion = {
        postBody: null,
        comments: [],
        error: message,
      };
      console.error(JSON.stringify({
        message: "reddit discussion enrichment failed",
        postId: post.id,
        error: message,
      }));
    }
  });

  snapshot.enrichment = {
    mode: "discussion",
    offset: options.offset,
    requestedPosts: selectedPosts.length,
    successfulPosts,
    commentsPerPost: options.commentLimit,
  };
}

async function tokensMatch(provided: string, expected: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  const left = new Uint8Array(providedHash);
  const right = new Uint8Array(expectedHash);
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left[index] ^ right[index];
  }
  return difference === 0;
}

function jsonResponse(body: unknown, status = 200): Response {
  return Response.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

async function isAuthorized(request: Request, env: Env): Promise<boolean> {
  const authorization = request.headers.get("Authorization");
  if (!authorization?.startsWith("Bearer ")) {
    return false;
  }
  return tokensMatch(authorization.slice("Bearer ".length), env.RUN_TOKEN);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ ok: true, scraper: "reddit", subreddit: env.SUBREDDIT });
    }

    if (request.method !== "POST" || url.pathname !== "/scrape") {
      return jsonResponse({ error: "Not found" }, 404);
    }

    if (!(await isAuthorized(request, env))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }

    const ranking = parseRanking(url.searchParams.get("ranking"));
    if (!ranking) {
      return jsonResponse({
        error: "Invalid ranking",
        supportedRankings: SUPPORTED_RANKINGS,
      }, 400);
    }

    let window: RedditWindow | null = null;
    if (ranking === "top" || ranking === "both") {
      const parsedWindow = parseWindow(url.searchParams.get("window"));
      if (!parsedWindow) {
        return jsonResponse({
          error: "Invalid window",
          supportedWindows: SUPPORTED_WINDOWS,
        }, 400);
      }
      window = parsedWindow;
    }

    const include = url.searchParams.get("include");
    if (include !== null && include !== "discussion") {
      return jsonResponse({
        error: "Invalid include option",
        supportedIncludes: ["discussion"],
      }, 400);
    }

    const listingLimit = parseIntegerOption(
      url.searchParams.get("limit"),
      25,
      1,
      MAX_LISTING_POSTS,
    );
    if (listingLimit === undefined) {
      return jsonResponse({
        error: "Invalid listing limit",
        limit: { minimum: 1, maximum: MAX_LISTING_POSTS },
      }, 400);
    }

    const postLimit = parseIntegerOption(
      url.searchParams.get("posts"),
      5,
      1,
      MAX_ENRICHED_POSTS,
    );
    const commentLimit = parseIntegerOption(
      url.searchParams.get("comments"),
      5,
      0,
      MAX_COMMENTS_PER_POST,
    );
    const offset = parseIntegerOption(
      url.searchParams.get("offset"),
      0,
      0,
      listingLimit - 1,
    );
    if (postLimit === undefined || commentLimit === undefined || offset === undefined) {
      return jsonResponse({
        error: "Invalid enrichment limits",
        offset: { minimum: 0, maximum: listingLimit - 1 },
        posts: { minimum: 1, maximum: MAX_ENRICHED_POSTS },
        comments: { minimum: 0, maximum: MAX_COMMENTS_PER_POST },
      }, 400);
    }

    try {
      const snapshot = await scrapePosts(env, ranking, window, listingLimit);
      if (include === "discussion") {
        await enrichDiscussions(snapshot, env, { offset, postLimit, commentLimit });
      }
      console.log(JSON.stringify({
        message: "reddit scrape completed",
        subreddit: snapshot.subreddit,
        ranking: snapshot.ranking,
        postCount: snapshot.posts.length,
        enrichedPostCount: snapshot.enrichment?.successfulPosts ?? 0,
      }));
      return jsonResponse(snapshot);
    } catch (error) {
      console.error(JSON.stringify({
        message: "reddit scrape failed",
        error: error instanceof Error ? error.message : String(error),
      }));
      return jsonResponse({ error: "Reddit scrape failed" }, 502);
    }
  },
} satisfies ExportedHandler<Env>;
