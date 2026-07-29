import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')


def is_finite_number(value):
    try:
        f = float(value)
        return f == f and f not in (float('inf'), float('-inf'))
    except (TypeError, ValueError):
        return False


def supabase_config():
    url = str(
        os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
        or os.environ.get('NEXT_PUBLIC_SUBABASE_URL')  # typo fallback
        or os.environ.get('SUPABASE_URL')
        or ''
    ).strip().rstrip('/')
    key = str(
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        or os.environ.get('SUPABASE_ANON_KEY')
        or ''
    ).strip()
    table = str(os.environ.get('SUPABASE_SETUPS_TABLE') or 'plmlist').strip() or 'plmlist'
    return url, key, table


def insert_setup(row):
    url, key, table = supabase_config()
    if not url or not key:
        raise RuntimeError('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required')

    endpoint = f'{url}/rest/v1/{table}'
    req = urllib.request.Request(
        endpoint,
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
        with urllib.request.urlopen(req, timeout=15) as resp:
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


def handle_submit():
    try:
        if request.method == 'OPTIONS':
            return '', 204

        url, key, table = supabase_config()

        if request.method == 'GET':
            return jsonify({
                'ok': True,
                'configured': bool(url and key),
                'path': request.path,
                'transport': 'supabase',
                'table': table,
            })

        if not url or not key:
            return jsonify({
                'error': 'Supabase is not configured',
                'detail': 'Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in env.',
            }), 500

        payload = request.get_json(silent=True, force=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'Invalid JSON'}), 400

        version_url = str(payload.get('version_url') or payload.get('link') or '').strip()
        hardware = str(payload.get('hardware') or payload.get('specs') or '').strip()
        speed = str(payload.get('speed') or payload.get('decode') or '').strip()
        kv_ctx = payload.get('kv_ctx') if payload.get('kv_ctx') is not None else payload.get('context')
        has_kv_ctx = kv_ctx is not None and str(kv_ctx).strip() != '' and is_finite_number(kv_ctx)

        if not version_url or not hardware or not speed or not has_kv_ctx:
            return jsonify({
                'error': 'Link, hardware, decode speed, and context length are required',
                'received': list(payload.keys()),
            }), 400

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
            return jsonify({'error': 'Failed to save setup', 'detail': str(err)}), 502

        return jsonify({'ok': True, 'id': (saved or {}).get('id')})
    except Exception as err:
        return jsonify({'error': 'Submit failed', 'detail': str(err)}), 500


@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')


@app.route('/api/submit', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/submit', methods=['GET', 'POST', 'OPTIONS'])
def submit():
    return handle_submit()


@app.route('/', methods=['POST', 'OPTIONS'])
def submit_at_root():
    return handle_submit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
