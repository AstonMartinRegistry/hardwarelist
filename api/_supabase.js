/** Shared Supabase REST helpers for Vercel API routes (CommonJS). */

function supabaseConfig() {
  const url = (
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    process.env.SUPABASE_URL ||
    ''
  ).replace(/\/$/, '');
  const key =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_ANON_KEY ||
    '';
  return { url, key };
}

function supabaseHeaders(key, prefer = 'return=representation') {
  const headers = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    'Content-Type': 'application/json',
  };
  if (prefer) headers.Prefer = prefer;
  return headers;
}

async function supabaseFetch(path, { method = 'GET', body, prefer } = {}) {
  const { url, key } = supabaseConfig();
  if (!url || !key) {
    const err = new Error('Supabase is not configured');
    err.status = 500;
    throw err;
  }
  const res = await fetch(`${url}/rest/v1/${path}`, {
    method,
    headers: supabaseHeaders(key, prefer),
    body: body != null ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!res.ok) {
    const err = new Error(
      typeof data === 'object' && data && data.message
        ? data.message
        : `Supabase ${res.status}`,
    );
    err.status = res.status;
    err.detail = data;
    throw err;
  }
  return data;
}

module.exports = {
  supabaseConfig,
  supabaseHeaders,
  supabaseFetch,
};
