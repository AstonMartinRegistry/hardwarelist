# PLM List

Static site + one API route that inserts setup submissions into Supabase.

## Layout

```
hardwarelist/
  index.html / locallist.html / hamsters.html
  api/submit.py     # Vercel function only for /api/submit
  devserver.py      # local server (not used by Vercel)
  supabase/plmlist.sql
  vercel.json
  requirements.txt
  .env.example
```

## Env vars (Vercel → Settings → Environment Variables)

| Name | Required | Notes |
|------|----------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | yes | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | **service_role** secret (not the publishable key) |
| `SUPABASE_SETUPS_TABLE` | no | default `plmlist` |

Add them for **Production** (and Preview if you want), then redeploy.

## Local

```bash
pip install -r requirements.txt
python3 devserver.py
# http://127.0.0.1:5000
```

## Vercel

1. Root Directory: leave blank
2. Framework Preset: Other
3. Set the env vars above, then deploy
4. Site should load at `/`; API health at `/api/submit` should show `"configured": true`
