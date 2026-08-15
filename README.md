# PLM List

Static shell + **live setups from Supabase**. Reddit ingest / classify / WhatsApp on Vercel.

```
index.html / locallist.html   ← shell; cards from GET /api/setups
setups-client.js              ← renders .setup-rich boxes in the browser
stats.html                    ← charts from /api/setups
api/setups.js                 ← public list of curated setups
api/submit.js                 ← form → plmlist (submissions queue)
api/cron-ingest-reddit.js     ← every 2h: scrape → ingest_*
api/cron-classify.js          ← +5m: gpt-oss-120b + WhatsApp alerts
api/whatsapp.js               ← Meta webhook ↔ zai-glm-4.7 chat / publish
supabase/setups.sql           ← curated listing rows (source of truth)
```

BenchmarkList links on cards are only a **rank data source** for open-weight
scores — this project is not affiliated with BenchmarkList.

## Vercel env

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `CRON_SECRET`
- `CEREBRAS_API_KEY` — `gpt-oss-120b` classify, `zai-glm-4.7` WhatsApp chat
- WhatsApp Cloud API (optional until chat is live):
  - `WHATSAPP_ACCESS_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`
  - `WHATSAPP_TO_NUMBER`
  - `WHATSAPP_VERIFY_TOKEN`
  - `WHATSAPP_APP_SECRET`

## SQL (once)

1. `supabase/plmlist.sql`
2. `supabase/ingest.sql`
3. `supabase/setups.sql`

Curated list lives only in **`public.setups`**. The site loads boxes dynamically — do not hardcode cards in HTML.

## Cron pipeline

`0 */2 * * *` → ingest Reddit → `pending`  
`5 */2 * * *` → classify → WhatsApp alert → chat → `publish` writes `setups` → site updates on next load

## Local

No Vercel CLI needed:

```bash
npm install
npm run dev
```

Opens **http://localhost:3000** (static site + `/api/*`). Needs `.env` Supabase keys for `/api/setups`.

Optional: `npx vercel dev` still works if you prefer it.