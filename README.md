# PLM List

Static site + Supabase. Reddit ingest runs **on Vercel** (no Cloudflare).

```
index.html / locallist.html / stats.html
api/submit.js                 ← form → plmlist
api/cron-ingest-reddit.js     ← every 2h: scrape r/LocalLLM → Supabase
api/cron-classify.js          ← +5m: Cerebras gpt-oss-120b triage
api/candidates.js             ← list / edit candidates (WhatsApp later)
api/_reddit_scrape.js         ← old.reddit.com HTML scraper (cheerio)
api/_classify.js              ← classifier prompt + DB updates
supabase/plmlist.sql
supabase/ingest.sql
```

BenchmarkList links on cards are only a **rank data source** for open-weight
scores — this project is not affiliated with BenchmarkList.

## Vercel env

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `CRON_SECRET` — random secret; Vercel cron sends it as `Authorization: Bearer …`
- `CEREBRAS_API_KEY` — classifier (+ later chat). Models: `gpt-oss-120b` classify, `zai-glm-4.7` chat

That’s it for Reddit. No `REDDIT_SCRAPER_URL` / Worker token.

## SQL (once)

Run in Supabase SQL editor:

1. `supabase/plmlist.sql`
2. `supabase/ingest.sql`
3. `supabase/setups.sql` ← listing cards (model, t/s, price, …)

Import current HTML cards into `setups`:

```bash
node scripts/sync_setups_from_html.js
```

## Cron

`0 */2 * * *` → `GET /api/cron-ingest-reddit`  
Scrapes `r/LocalLLM` **new**, upserts `ingest_posts` + pending `ingest_candidates`.

`5 */2 * * *` → `GET /api/cron-classify`  
Classifies pending candidates with Cerebras **gpt-oss-120b** → `classified` (interesting) or `skipped` (noise). Draft extract fields are hints for the later GLM 4.7 / WhatsApp chat step.

## Local

```bash
npm install
npx vercel dev
```

Manual ingest (uses .env Supabase keys):

```bash
node scripts/ingest_reddit_json.js reddit/output/localllm-10-bodies.json
```

Classify pending (uses `.env` Cerebras + Supabase):

```bash
node scripts/classify_pending.js --limit 5
```

Or hit the cron routes locally:

```bash
curl -X POST "http://localhost:3000/api/cron-ingest-reddit?limit=5&comments=0" \
  -H "Authorization: Bearer $CRON_SECRET"

curl -X POST "http://localhost:3000/api/cron-classify?limit=5" \
  -H "Authorization: Bearer $CRON_SECRET"
```
