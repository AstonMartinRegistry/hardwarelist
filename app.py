import json
import os
import re
import smtplib
import ssl
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')


def line(label, value):
    v = str(value).strip() if value is not None else ''
    return f'{label}: {v}' if v else None


def format_body(payload):
    lines = [
        line('Model', payload.get('model')),
        line('Provider', payload.get('provider')),
        line('Quant', payload.get('quant_bits')),
        line('Version', payload.get('version_label')),
        line('Link', payload.get('version_url')),
        line('Context', payload.get('kv_ctx')),
        line('Hardware', payload.get('hardware')),
        line('Price', payload.get('price')),
        line('Decode', payload.get('speed')),
        line('Prefill', payload.get('pp')),
        line('Info', payload.get('info')),
        line('Email', payload.get('email')),
    ]
    lines = [l for l in lines if l]
    return '\n'.join(lines) + '\n\n---\nJSON\n' + json.dumps(payload, indent=2) + '\n'


def is_finite_number(value):
    try:
        f = float(value)
        return f == f and f not in (float('inf'), float('-inf'))
    except (TypeError, ValueError):
        return False


def send_with_gmail(user, password, to, submitter, subject, text):
    msg = MIMEMultipart()
    msg['From'] = f'PLM List <{user}>'
    msg['To'] = to
    msg['Subject'] = subject
    if submitter:
        msg['Reply-To'] = submitter
    msg.attach(MIMEText(text, 'plain'))

    ctx = ssl.create_default_context()
    errors = []

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)
            return
    except Exception as err:
        errors.append(f'587/starttls: {err!r}')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=12, context=ctx) as server:
            server.login(user, password)
            server.send_message(msg)
            return
    except Exception as err:
        errors.append(f'465/ssl: {err!r}')

    raise RuntimeError(' | '.join(errors))


def send_with_resend(api_key, from_addr, to, submitter, subject, text):
    body = {
        'from': from_addr,
        'to': [to],
        'subject': subject,
        'text': text,
    }
    if submitter:
        body['reply_to'] = submitter
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except urllib.error.HTTPError as err:
        detail = err.read().decode('utf-8', 'replace')
        raise RuntimeError(f'Resend HTTP {err.code}: {detail}') from err


def send_with_https_relay(to, submitter, subject, text):
    """
    HTTPS form relay (works on Vercel; Gmail SMTP often crashes serverless).
    Delivers to `to`. First use may require clicking an activation email.
    """
    body = {
        'name': 'PLM List',
        'email': submitter or to,
        '_subject': subject,
        'message': text,
    }
    url = 'https://formsubmit.co/ajax/' + urllib.request.quote(to, safe='@')
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {'raw': raw}
            if isinstance(data, dict) and data.get('success') == 'false':
                raise RuntimeError(data.get('message') or raw or 'relay rejected')
    except urllib.error.HTTPError as err:
        detail = err.read().decode('utf-8', 'replace')
        raise RuntimeError(f'Relay HTTP {err.code}: {detail}') from err


def handle_submit():
    try:
        if request.method == 'OPTIONS':
            return '', 204

        user = str(os.environ.get('SENDER_EMAIL') or '').strip()
        password = re.sub(r'\s+', '', str(os.environ.get('SENDER_PASSWORD') or ''))
        to = str(os.environ.get('RECEIVER_EMAIL') or user).strip()
        resend_key = str(os.environ.get('RESEND_API_KEY') or '').strip()
        on_vercel = bool(os.environ.get('VERCEL'))

        if request.method == 'GET':
            configured = bool(to and (resend_key or ((user and password) and not on_vercel)))
            transport = (
                'resend' if resend_key
                else ('needs-resend' if on_vercel else 'gmail-smtp')
            )
            return jsonify({
                'ok': True,
                'configured': configured,
                'path': request.path,
                'transport': transport,
            })

        if not to:
            return jsonify({'error': 'RECEIVER_EMAIL is not configured on the server'}), 500
        if on_vercel and not resend_key:
            return jsonify({
                'error': 'Email transport not configured for Vercel',
                'detail': (
                    'Add RESEND_API_KEY in Vercel project env vars and redeploy. '
                    'Gmail SMTP crashes on this host (502).'
                ),
            }), 500
        if not on_vercel and not (user and password):
            return jsonify({'error': 'Email is not configured on the server'}), 500

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

        payload['version_url'] = version_url
        payload['hardware'] = hardware
        payload['speed'] = speed
        payload['kv_ctx'] = float(kv_ctx)

        submitter = str(payload.get('email') or '').strip()
        model = str(payload.get('model') or '').strip() or 'setup'
        subject = f'PLM List setup: {model} on {hardware}'
        text = format_body(payload)

        try:
            if resend_key:
                from_addr = str(os.environ.get('RESEND_FROM') or user or 'onboarding@resend.dev').strip()
                send_with_resend(resend_key, from_addr, to, submitter, subject, text)
            elif on_vercel:
                # Gmail SMTP (and some raw SSL outbound) crashes this Vercel+Cloudflare
                # setup with a generic 502. Require Resend (HTTPS) in production.
                return jsonify({
                    'error': 'Email transport not configured for Vercel',
                    'detail': (
                        'Gmail SMTP does not work on this serverless host. '
                        'Add RESEND_API_KEY (and optional RESEND_FROM) in Vercel env, '
                        'then redeploy. Free at https://resend.com — set RECEIVER_EMAIL '
                        'to your inbox.'
                    ),
                }), 500
            else:
                send_with_gmail(user, password, to, submitter, subject, text)
        except Exception as err:
            return jsonify({'error': 'Failed to send email', 'detail': str(err)}), 502

        return jsonify({'ok': True})
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
