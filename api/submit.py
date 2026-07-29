"""
POST /api/submit — save a setup row to Supabase (plmlist).

Vercel Python serverless entry (class name must be `handler`).
Also importable by the local server in app.py.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()


def _env(*names: str) -> str:
    for name in names:
        value = str(os.environ.get(name) or '').strip()
        if value:
            return value
    return ''


def supabase_config():
    url = _env(
        'NEXT_PUBLIC_SUPABASE_URL',
        'NEXT_PUBLIC_SUBABASE_URL',
        'SUPABASE_URL',
    ).rstrip('/')
    key = _env(
        'SUPABASE_SERVICE_ROLE_KEY',
        'NEXT_PUBLIC_SUPABASE_ROLE_KEY',
        'SUPABASE_ANON_KEY',
    )
    table = _env('SUPABASE_SETUPS_TABLE') or 'plmlist'
    return url, key, table


def is_finite_number(value) -> bool:
    try:
        f = float(value)
        return f == f and f not in (float('inf'), float('-inf'))
    except (TypeError, ValueError):
        return False


def insert_setup(row: dict):
    url, key, table = supabase_config()
    if not url or not key:
        raise RuntimeError('NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required')

    req = urllib.request.Request(
        f'{url}/rest/v1/{table}',
        data=json.dumps(row).encode('utf-8'),
        headers={
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            if not raw:
                return None
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data[0]
            return data
    except urllib.error.HTTPError as err:
        detail = err.read().decode('utf-8', 'replace')
        raise RuntimeError(f'Supabase HTTP {err.code}: {detail}') from err


def handle_submit(method: str, raw_body: bytes | None = None):
    """Return (status_code, response_dict)."""
    method = (method or 'GET').upper()
    url, key, table = supabase_config()

    if method == 'OPTIONS':
        return 204, None

    if method == 'GET':
        return 200, {
            'ok': True,
            'configured': bool(url and key),
            'transport': 'supabase',
            'table': table,
        }

    if method != 'POST':
        return 405, {'error': 'Method not allowed'}

    if not url or not key:
        return 500, {
            'error': 'Supabase is not configured',
            'detail': 'Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the host.',
        }

    try:
        payload = json.loads(raw_body.decode('utf-8') if raw_body else '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, {'error': 'Invalid JSON'}

    if not isinstance(payload, dict):
        return 400, {'error': 'Invalid JSON'}

    version_url = str(payload.get('version_url') or payload.get('link') or '').strip()
    hardware = str(payload.get('hardware') or payload.get('specs') or '').strip()
    speed = str(payload.get('speed') or payload.get('decode') or '').strip()
    kv_ctx = payload.get('kv_ctx') if payload.get('kv_ctx') is not None else payload.get('context')
    has_kv_ctx = kv_ctx is not None and str(kv_ctx).strip() != '' and is_finite_number(kv_ctx)

    if not version_url or not hardware or not speed or not has_kv_ctx:
        return 400, {
            'error': 'Link, hardware, decode speed, and context length are required',
            'received': list(payload.keys()),
        }

    row = {
        'model': str(payload.get('model') or '').strip() or None,
        'provider': str(payload.get('provider') or '').strip() or None,
        'quant_bits': str(payload.get('quant_bits') or '').strip() or None,
        'version_label': str(payload.get('version_label') or '').strip() or None,
        'version_url': version_url,
        'kv_ctx': float(kv_ctx),
        'hardware': hardware,
        'price': str(payload.get('price') or '').strip() or None,
        'speed': speed,
        'pp': str(payload.get('pp') or '').strip() or None,
        'info': str(payload.get('info') or '').strip() or None,
        'email': str(payload.get('email') or '').strip() or None,
        'payload': payload,
    }

    try:
        saved = insert_setup(row)
    except Exception as err:
        return 502, {'error': 'Failed to save setup', 'detail': str(err)}

    return 200, {'ok': True, 'id': (saved or {}).get('id')}


def _send_json(handler: BaseHTTPRequestHandler, status: int, body):
    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    if status == 204 or body is None:
        handler.send_response(status)
        for k, v in cors.items():
            handler.send_header(k, v)
        handler.end_headers()
        return

    data = json.dumps(body).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(data)))
    for k, v in cors.items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(data)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        status, body = handle_submit('OPTIONS')
        _send_json(self, status, body)

    def do_GET(self):
        status, body = handle_submit('GET')
        _send_json(self, status, body)

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length) if length else b'{}'
        status, body = handle_submit('POST', raw)
        _send_json(self, status, body)

    def log_message(self, format, *args):
        return
