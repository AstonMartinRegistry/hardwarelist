import { describe, expect, it } from "vitest";
import worker, {
  parseOldRedditDiscussion,
  parseOldRedditListing,
  resolveCrosspostUrl,
} from "../src/index";

const env: Env = {
  SUBREDDIT: "LocalLLM",
  USER_AGENT: "benchmarklist-reddit-scraper/0.2 (+https://benchmarklist.com)",
  RUN_TOKEN: "test-run-token",
};

describe("parseOldRedditListing", () => {
  it("normalizes Old Reddit post attributes without retaining author or body", async () => {
    const html = `
      <div id="siteTable">
        <div
          class="thing link odd"
          data-fullname="t3_abc123"
          data-timestamp="1700000000000"
          data-permalink="/r/LocalLLM/comments/abc123/a_useful_post/"
          data-url="https://example.com/model"
          data-domain="example.com"
          data-rank="1"
          data-comments-count="7"
          data-score="42"
          data-promoted="false"
          data-nsfw="false"
          data-spoiler="false"
          data-author="not-retained"
        >
          <div class="entry">
            <p class="title"><a class="title">A useful LocalLLM post</a></p>
            <div class="usertext-body">not retained either</div>
          </div>
        </div>
      </div>`;

    const snapshot = await parseOldRedditListing(
      new Response(html, {
        headers: {
          "Content-Type": "text/html",
          "Content-Length": String(html.length),
        },
      }),
      "LocalLLM",
      "top",
      "month",
      new Date("2026-07-13T12:00:00.000Z"),
    );

    expect(snapshot).toEqual({
      schemaVersion: 1,
      source: "reddit",
      subreddit: "LocalLLM",
      ranking: "top",
      window: "month",
      fetchedAt: "2026-07-13T12:00:00.000Z",
      posts: [
        {
          rank: 1,
          id: "abc123",
          title: "A useful LocalLLM post",
          score: 42,
          commentCount: 7,
          createdAt: "2023-11-14T22:13:20.000Z",
          postUrl: "https://www.reddit.com/r/LocalLLM/comments/abc123/a_useful_post/",
          outboundUrl: "https://example.com/model",
          isSelf: false,
          isNsfw: false,
          isSpoiler: false,
          isStickied: false,
          listings: ["top"],
        },
      ],
    });
    expect(snapshot.posts[0]).not.toHaveProperty("author");
    expect(snapshot.posts[0]).not.toHaveProperty("selftext");
  });

  it("rejects listings without posts", async () => {
    await expect(
      parseOldRedditListing(
        new Response('<div id="siteTable"></div>'),
        "LocalLLM",
        "new",
        null,
        new Date(),
      ),
    ).rejects.toThrow("Old Reddit listing contained no posts");
  });
});

describe("parseOldRedditDiscussion", () => {
  it("extracts a self-post body and bounded top-level comments without authors", async () => {
    const html = `
      <div id="siteTable">
        <div class="thing link self">
          <div class="entry">
            <div class="usertext-body"><div class="md">
              <p>Post body paragraph one.</p><p>Paragraph two.</p>
            </div></div>
          </div>
        </div>
      </div>
      <div class="commentarea">
        <div class="sitetable">
          <div class="thing comment stickied" data-fullname="t1_bot" data-permalink="/bot/">
            <div class="entry"><div class="usertext-body"><div class="md"><p>Bot notice</p></div></div></div>
          </div>
          <div class="thing comment" data-fullname="t1_comment1" data-permalink="/r/LocalLLM/comments/post/comment1/" data-author="not-retained">
            <div class="entry">
              <p class="tagline">
                <span class="score unvoted" title="17">17 points</span>
                <time datetime="2026-07-13T11:00:00+00:00">one hour ago</time>
              </p>
              <div class="usertext-body"><div class="md"><p>Useful &#39;comment&#39;.</p><p>More detail.</p></div></div>
            </div>
          </div>
        </div>
      </div>`;

    const discussion = await parseOldRedditDiscussion(
      new Response(html, { headers: { "Content-Length": String(html.length) } }),
      5,
    );

    expect(discussion).toEqual({
      postBody: "Post body paragraph one.\nParagraph two.",
      comments: [
        {
          id: "comment1",
          body: "Useful 'comment'.\nMore detail.",
          score: 17,
          createdAt: "2026-07-13T11:00:00.000Z",
          postUrl: "https://www.reddit.com/r/LocalLLM/comments/post/comment1/",
          isStickied: false,
        },
      ],
    });
    expect(discussion.comments[0]).not.toHaveProperty("author");
  });

  it("returns null for the body of a link post", async () => {
    const discussion = await parseOldRedditDiscussion(
      new Response('<div id="siteTable"><div class="thing link"></div></div>'),
      0,
    );

    expect(discussion).toEqual({ postBody: null, comments: [] });
  });
});

describe("resolveCrosspostUrl", () => {
  const postUrl = "https://www.reddit.com/r/LocalLLM/comments/abc123/a_post/";

  it("returns absolute URL when outbound points at another Reddit thread", () => {
    expect(
      resolveCrosspostUrl(
        "/r/LocalLLaMA/comments/xyz789/original_post/",
        postUrl,
      ),
    ).toBe("https://www.reddit.com/r/LocalLLaMA/comments/xyz789/original_post/");
  });

  it("ignores self outbound links and non-Reddit URLs", () => {
    expect(
      resolveCrosspostUrl("/r/LocalLLM/comments/abc123/a_post/", postUrl),
    ).toBeNull();
    expect(resolveCrosspostUrl("https://example.com/model", postUrl)).toBeNull();
    expect(resolveCrosspostUrl("https://i.redd.it/abc.png", postUrl)).toBeNull();
  });
});

describe("request routing", () => {
  it("exposes a health check without contacting Reddit", async () => {
    const response = await worker.fetch(new Request("https://worker.test/health"), env);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      ok: true,
      scraper: "reddit",
      subreddit: "LocalLLM",
    });
  });

  it("protects scrape runs with a bearer token", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape", { method: "POST" }),
      env,
    );

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ error: "Unauthorized" });
  });

  it("rejects unsupported time windows for top scrapes", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape?ranking=top&window=decade", {
        method: "POST",
        headers: { Authorization: "Bearer test-run-token" },
      }),
      env,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: "Invalid window",
      supportedWindows: ["day", "week", "month"],
    });
  });

  it("rejects unsupported rankings", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape?ranking=hot", {
        method: "POST",
        headers: { Authorization: "Bearer test-run-token" },
      }),
      env,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: "Invalid ranking",
      supportedRankings: ["top", "new", "both"],
    });
  });

  it("rejects enrichment limits outside the safe range", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape?include=discussion&posts=26&comments=11", {
        method: "POST",
        headers: { Authorization: "Bearer test-run-token" },
      }),
      env,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: "Invalid enrichment limits",
      offset: { minimum: 0, maximum: 24 },
      posts: { minimum: 1, maximum: 25 },
      comments: { minimum: 0, maximum: 10 },
    });
  });

  it("rejects listing limits above fifty", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape?window=month&limit=51", {
        method: "POST",
        headers: { Authorization: "Bearer test-run-token" },
      }),
      env,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: "Invalid listing limit",
      limit: { minimum: 1, maximum: 50 },
    });
  });

  it("rejects discussion offsets beyond the requested listing", async () => {
    const response = await worker.fetch(
      new Request("https://worker.test/scrape?limit=50&include=discussion&offset=50", {
        method: "POST",
        headers: { Authorization: "Bearer test-run-token" },
      }),
      env,
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: "Invalid enrichment limits",
      offset: { minimum: 0, maximum: 49 },
      posts: { minimum: 1, maximum: 25 },
      comments: { minimum: 0, maximum: 10 },
    });
  });
});
