#!/usr/bin/env node
/**
 * Local static + API server (no Vercel CLI required).
 *
 *   node scripts/dev_server.js
 *   # → http://localhost:3000
 *
 * Loads .env, serves HTML/JS from the repo root, and routes /api/* to
 * the same CommonJS handlers used on Vercel.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const ROOT = path.join(__dirname, '..');
const PORT = Number(process.env.PORT) || 3000;

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

loadEnv(path.join(ROOT, '.env'));
loadEnv(path.join(ROOT, '.env.local'));

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
};

function send(res, status, body, headers = {}) {
  const payload = body == null ? '' : Buffer.isBuffer(body) ? body : Buffer.from(String(body));
  res.writeHead(status, {
    'Content-Length': payload.length,
    ...headers,
  });
  res.end(payload);
}

function wrapRes(res) {
  let statusCode = 200;
  const headers = {};
  return {
    get statusCode() {
      return statusCode;
    },
    set statusCode(v) {
      statusCode = v;
    },
    setHeader(k, v) {
      headers[k] = v;
    },
    status(code) {
      statusCode = code;
      return this;
    },
    json(obj) {
      const body = JSON.stringify(obj);
      headers['Content-Type'] = headers['Content-Type'] || 'application/json; charset=utf-8';
      send(res, statusCode, body, headers);
    },
    end(data) {
      send(res, statusCode, data == null ? '' : data, headers);
    },
  };
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8');
  if (!raw) return { raw: '', body: {} };
  try {
    return { raw, body: JSON.parse(raw) };
  } catch {
    return { raw, body: raw };
  }
}

function resolveApi(pathname) {
  // /api/foo → api/foo.js ; /api/foo/bar ignored
  const name = pathname.replace(/^\/api\//, '').replace(/\/$/, '');
  if (!name || name.includes('..') || name.startsWith('_')) return null;
  const file = path.join(ROOT, 'api', `${name}.js`);
  if (!fs.existsSync(file)) return null;
  return file;
}

function safeStatic(urlPath) {
  let rel = decodeURIComponent(urlPath.split('?')[0]);
  if (rel === '/' || rel === '') rel = '/index.html';
  const file = path.normalize(path.join(ROOT, rel));
  if (!file.startsWith(ROOT)) return null;
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) return null;
  return file;
}

const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url || '/', `http://localhost:${PORT}`);
    if (u.pathname.startsWith('/api/')) {
      const file = resolveApi(u.pathname);
      if (!file) return send(res, 404, JSON.stringify({ error: 'Not found' }), {
        'Content-Type': 'application/json',
      });
      delete require.cache[require.resolve(file)];
      // Also drop sibling api modules so local edits to helpers apply.
      for (const key of Object.keys(require.cache)) {
        if (key.startsWith(path.join(ROOT, 'api') + path.sep)) {
          delete require.cache[key];
        }
      }
      const handler = require(file);
      const { raw, body } = await readBody(req);
      const query = Object.fromEntries(u.searchParams.entries());
      const fakeReq = {
        method: req.method,
        headers: req.headers,
        query,
        body,
        rawBody: raw,
        url: req.url,
        async *[Symbol.asyncIterator]() {
          if (raw) yield Buffer.from(raw);
        },
      };
      await handler(fakeReq, wrapRes(res));
      return;
    }

    const file = safeStatic(u.pathname);
    // SSR embed for main list pages (same as Vercel rewrites)
    if (
      (u.pathname === '/' || u.pathname === '/index.html' || u.pathname === '/locallist.html') &&
      u.searchParams.get('raw') !== '1'
    ) {
      const apiName = u.pathname === '/locallist.html' ? 'ssr-locallist' : 'ssr-home';
      const apiFile = path.join(ROOT, 'api', `${apiName}.js`);
      delete require.cache[require.resolve(apiFile)];
      const handler = require(apiFile);
      await handler(
        { method: req.method, headers: req.headers, query: {}, url: req.url },
        wrapRes(res),
      );
      return;
    }

    if (!file) return send(res, 404, 'Not found', { 'Content-Type': 'text/plain' });
    const ext = path.extname(file).toLowerCase();
    send(res, 200, fs.readFileSync(file), {
      'Content-Type': MIME[ext] || 'application/octet-stream',
    });
  } catch (err) {
    console.error(err);
    if (!res.headersSent) {
      send(res, 500, JSON.stringify({ error: err.message || 'Server error' }), {
        'Content-Type': 'application/json',
      });
    }
  }
});

server.listen(PORT, () => {
  console.log(`PLM List local server → http://localhost:${PORT}`);
  console.log('API example: GET /api/setups');
});
