-- Run in Supabase → SQL Editor
-- Table name: plmlist

create table if not exists public.plmlist (
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

create index if not exists plmlist_created_at_idx on public.plmlist (created_at desc);

alter table public.plmlist enable row level security;

-- Server uses SUPABASE_SERVICE_ROLE_KEY (bypasses RLS).
-- No public insert policies needed for /api/submit.
