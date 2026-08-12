-- Curated PLM List setups (imported from HTML / published from WhatsApp)
-- Run in Supabase SQL Editor after plmlist.sql + ingest.sql

create table if not exists public.setups (
  id uuid primary key default gen_random_uuid(),
  provider text,
  model text not null,
  quant text,
  version_label text,
  version_url text,
  context text,
  context_tokens double precision,
  rank integer,
  hardware text,
  price_usd numeric,
  speed_raw text,
  speed_tps double precision,
  pp_tps double precision,
  memory_used double precision,
  memory_kv double precision,
  memory_total double precision,
  info text,
  search text,
  source text not null default 'html',
  external_key text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (external_key)
);

create index if not exists setups_provider_model_idx
  on public.setups (provider, model);
create index if not exists setups_price_idx
  on public.setups (price_usd);
create index if not exists setups_speed_idx
  on public.setups (speed_tps desc nulls last);
create index if not exists setups_rank_idx
  on public.setups (rank);

alter table public.setups enable row level security;
