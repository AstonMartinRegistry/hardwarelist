/**
 * SSR homepage: static index.html + embedded setups from Supabase.
 * Rewritten from / and /index.html via vercel.json (and local dev server).
 */
const path = require('path');

// Bust require cache so local edits to embed helpers apply without restart
const embedPath = require.resolve('./_embed_html');
delete require.cache[embedPath];
const { embedSetupsIntoHtml } = require('./_embed_html');

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    return res.end();
  }
  try {
    const { html, count } = await embedSetupsIntoHtml(
      path.join(__dirname, '..', 'index.html'),
    );
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=300');
    res.setHeader('X-PLM-Embedded-Setups', String(count));
    res.statusCode = 200;
    res.end(html);
  } catch (err) {
    res.statusCode = err.status || 500;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(
      `<!DOCTYPE html><html><body><h1>PLM List</h1><p>Could not render setups.</p><p>${String(err.message || err)}</p><p><a href="/index.html?raw=1">Try static shell</a></p></body></html>`,
    );
  }
};
