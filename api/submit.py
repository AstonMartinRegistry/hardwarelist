import json
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler


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
        return not (float(value) != float(value) or float(value) in (float('inf'), float('-inf')))
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


class handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        payload = json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        configured = bool(
            os.environ.get('SENDER_EMAIL')
            and os.environ.get('SENDER_PASSWORD')
            and (os.environ.get('RECEIVER_EMAIL') or os.environ.get('SENDER_EMAIL'))
        )
        self._json(200, {'ok': True, 'configured': configured})

    def do_POST(self):
        user = str(os.environ.get('SENDER_EMAIL') or '').strip()
        password = re.sub(r'\s+', '', str(os.environ.get('SENDER_PASSWORD') or ''))
        to = str(os.environ.get('RECEIVER_EMAIL') or user).strip()

        if not user or not password or not to:
            return self._json(500, {'error': 'Email is not configured on the server'})

        try:
            length = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(length).decode('utf-8').strip() if length else ''
            payload = json.loads(raw) if raw else {}
            if not isinstance(payload, dict):
                payload = {}
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {'error': 'Invalid JSON'})

        version_url = str(payload.get('version_url') or payload.get('link') or '').strip()
        hardware = str(payload.get('hardware') or payload.get('specs') or '').strip()
        speed = str(payload.get('speed') or payload.get('decode') or '').strip()
        kv_ctx = payload.get('kv_ctx') if payload.get('kv_ctx') is not None else payload.get('context')
        has_kv_ctx = kv_ctx is not None and str(kv_ctx).strip() != '' and is_finite_number(kv_ctx)

        if not version_url or not hardware or not speed or not has_kv_ctx:
            return self._json(400, {
                'error': 'Link, hardware, decode speed, and context length are required',
                'received': list(payload.keys()),
            })

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
            return self._json(502, {'error': 'Failed to send email', 'detail': str(err)})

        return self._json(200, {'ok': True})
