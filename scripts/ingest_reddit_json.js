#!/usr/bin/env node
/**
 * Apply a local Reddit snapshot JSON into Supabase ingest tables.
 *
 * Usage:
 *   node scripts/ingest_reddit_json.js reddit/output/localllm-10-bodies.json
 *
 * Requires .env: NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
 * Tables: run supabase/ingest.sql in the Supabase SQL editor first.
 */

const fs = require('fs');
const path = require('path');

function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#') || !t.includes('=')) continue;
    const i = t.indexOf('=');
    const k = t.slice(0, i).trim();
    let v = t.slice(i + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    if (!(k in process.env)) process.env[k] = v;
  }
}

loadEnv(path.join(__dirname, '..', '.env'));
loadEnv(path.join(__dirname, '..', '.env.local'));

const { upsertSnapshot } = require('../api/_ingest');

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: node scripts/ingest_reddit_json.js <snapshot.json>');
    process.exit(1);
  }
  const abs = path.resolve(file);
  const snapshot = JSON.parse(fs.readFileSync(abs, 'utf8'));
  const result = await upsertSnapshot(snapshot);
  console.log(JSON.stringify({ ok: true, file: abs, ...result }, null, 2));
}

main().catch((err) => {
  console.error(err.message);
  if (err.detail) console.error(JSON.stringify(err.detail, null, 2));
  process.exit(1);
});
