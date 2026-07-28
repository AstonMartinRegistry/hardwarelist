import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

app = Flask(__name__, static_folder=OUTPUT_DIR, static_url_path='')


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

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
    try:
        server.login(user, password)
        server.send_message(msg)
    finally:
        server.quit()


@app.route('/')
def index():
    return send_from_directory(OUTPUT_DIR, 'index.html')


@app.route('/api/submit', methods=['GET', 'POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        return '', 204

    user = str(os.environ.get('SENDER_EMAIL') or '').strip()
    password = re.sub(r'\s+', '', str(os.environ.get('SENDER_PASSWORD') or ''))
    to = str(os.environ.get('RECEIVER_EMAIL') or user).strip()

    if request.method == 'GET':
        configured = bool(user and password and to)
        return jsonify({'ok': True, 'configured': configured})

    if not user or not password or not to:
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

    try:
        send_with_gmail(user, password, to, submitter, subject, format_body(payload))
    except Exception as err:
        return jsonify({'error': 'Failed to send email', 'detail': str(err)}), 502

    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
