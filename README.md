# PLM List

Static site + one API route that inserts setup submissions into Supabase.

## Layout

```
hardwarelist/
  public/           # site (index, locallist, hamsters)
  api/submit.py     # Vercel serverless: POST /api/submit → Supabase
  devserver.py      # local server only (not used by Vercel)
  pyproject.toml    # points Vercel at api.submit:handler
  supabase/plmlist.sql
  vercel.json
  requirements.txt
  .env.example
```

## Env vars (local `.env` and Vercel → Settings → Environment Variables)

| Name | Required | Notes |
|------|----------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | yes | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | **service_role** secret (not the publishable key) |
| `SUPABASE_SETUPS_TABLE` | no | default `plmlist` |

Create the table with `supabase/plmlist.sql` if needed.

## Local

```bash
pip install -r requirements.txt
python3 devserver.py
# http://127.0.0.1:5000
```

## Vercel reconnect

1. Import this repo (Root Directory blank, Framework Preset = Other).
2. Set the two env vars above for Production (and Preview if you want).
3. Deploy. Confirm `GET https://your-domain/api/submit` returns `"configured": true`.
4. Point the domain / Cloudflare at the new deployment.
