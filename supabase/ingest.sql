-- Ingest pipeline tables for Reddit/Twitter → classify → WhatsApp → publish
-- Run in Supabase → SQL Editor (after plmlist.sql)

-- Raw / near-raw source posts (temporary retention; cleanup job can delete old rows)
create table if not exists public.ingest_posts (
  id text primary key,                    -- e.g. reddit:1vlwpr2
  source text not null,                   -- reddit | twitter | ...
  external_id text not null,
  subreddit text,
  ranking text,                           -- new | top | both
  title text not null default '',
  body text,                              -- best text: post_body or crosspost_body
  post_body text,
  crosspost_url text,
  crosspost_body text,
  score integer,
  comment_count integer,
  post_url text not null,
  outbound_url text,
  is_self boolean,
  listings text[] not null default '{}',
  raw jsonb not null default '{}'::jsonb,
  source_created_at timestamptz,
  fetched_at timestamptz not null,
  ingested_at timestamptz not null default now(),
  unique (source, external_id)
);

create index if not exists ingest_posts_ingested_at_idx
  on public.ingest_posts (ingested_at desc);
create index if not exists ingest_posts_source_created_at_idx
  on public.ingest_posts (source_created_at desc nulls last);

-- Classified + editable working copy (WhatsApp / chat edits land here)
create table if not exists public.ingest_candidates (
  id uuid primary key default gen_random_uuid(),
  post_id text not null references public.ingest_posts (id) on delete cascade,
  is_news boolean not null default false,
  kind text,                              -- setup | speed | quant | other_news | noise
  confidence real,
  summary text,
  -- Denormalized extract fields (edit these via WhatsApp)
  model text,
  quant text,
  hardware text,
  speed text,
  price text,
  context text,
  version_url text,
  info text,
  extracted jsonb not null default '{}'::jsonb,
  classifier_model text,
  status text not null default 'pending',
    -- pending | classified | alerted | chatting | ready | posted | skipped
  plmlist_id uuid,
  notes text,                             -- freeform chat notes
  classified_at timestamptz,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (post_id)
);

create index if not exists ingest_candidates_status_idx
  on public.ingest_candidates (status, updated_at desc);
create index if not exists ingest_candidates_is_news_idx
  on public.ingest_candidates (is_news, classified_at desc nulls last);

-- WhatsApp / ops chat threads bound to a candidate
create table if not exists public.ingest_conversations (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null references public.ingest_candidates (id) on delete cascade,
  channel text not null default 'whatsapp',
  external_thread_id text,
  messages jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ingest_conversations_candidate_idx
  on public.ingest_conversations (candidate_id, updated_at desc);

-- Audit of actions (post / skip / field edits)
create table if not exists public.ingest_actions (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references public.ingest_candidates (id) on delete set null,
  action text not null,                   -- classify | alert | edit | post | skip
  actor text not null default 'system',   -- system | whatsapp | user
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ingest_actions_candidate_idx
  on public.ingest_actions (candidate_id, created_at desc);

alter table public.ingest_posts enable row level security;
alter table public.ingest_candidates enable row level security;
alter table public.ingest_conversations enable row level security;
alter table public.ingest_actions enable row level security;

-- Optional: drop raw posts older than 14 days (run manually or via cron SQL)
-- delete from public.ingest_posts where ingested_at < now() - interval '14 days';
