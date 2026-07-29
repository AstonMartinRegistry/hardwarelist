# PLM List

Normal static website. One API route saves form submissions to Supabase.

```
index.html          ← the site
locallist.html
hamsters.html
api/submit.js       ← form POST target
```

## Vercel setup

1. Import the GitHub repo
2. Root Directory: **leave blank**
3. Framework Preset: **Other**
4. Environment Variables (Production):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
5. Deploy

That’s it. `/` is the website. `/api/submit` is only the form endpoint.

## Local

```bash
npx vercel dev
```

Or open the HTML files directly; submit only works with the API running.
