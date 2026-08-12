#!/usr/bin/env node
/**
 * Classify pending ingest_candidates via Cerebras (local .env).
 *
 *   node scripts/classify_pending.js
 *   node scripts/classify_pending.js --limit 5
 */
const fs = require('fs');
const path = require('path');

function loadEnv(filePath) {
  if (!fs.existsSync(filePath)) return;
  for (const line of fs.readFileSync(filePath, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (process.env[key] == null) process.env[key] = val;
  }
}

loadEnv(path.join(__dirname, '..', '.env'));

const { classifyPending } = require('../api/_classify');

async function main() {
  const args = process.argv.slice(2);
  let limit = 5;
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--limit' && args[i + 1]) {
      limit = Number(args[i + 1]);
      i += 1;
    }
  }

  const result = await classifyPending({ limit });
  console.log(JSON.stringify(result, null, 2));
  if (result.errors > 0) process.exitCode = 1;
}

main().catch((err) => {
  console.error(err.message || err);
  if (err.detail) console.error(JSON.stringify(err.detail, null, 2));
  process.exit(1);
});
