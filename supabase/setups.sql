-- Run in Supabase → SQL Editor
create table if not exists public.setups (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  model text,
  provider text,
  quant_bits text,
  version_label text,
  version_url text not null,
  kv_ctx double precision,
  hardware text not null,
  price text,
  speed text not null,
  pp text,
  info text,
  email text,
  payload jsonb not null default '{}'::jsonb
);

create index if not exists setups_created_at_idx on public.setups (created_at desc);

alter table public.setups enable row level security;

-- Server uses the service role key (bypasses RLS).
-- No public policies needed for inserts from /api/submit.
