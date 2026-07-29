"""Local server: static site + /api/submit (same handler as Vercel)."""
from __future__ import annotations

import importlib.util
import mimetypes
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent
API_FILE = BASE_DIR / 'api' / 'submit.py'
STATIC_EXT = {'.html', '.css', '.js', '.jpg', '.jpeg', '.png', '.svg', '.ico', '.webp', '.txt', '.json'}

spec = importlib.util.spec_from_file_location('plmlist_submit', API_FILE)
submit_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(submit_mod)


class LocalHandler(BaseHTTPRequestHandler):
    def _is_submit(self) -> bool:
        path = urlparse(self.path).path.rstrip('/')
        return path in ('/api/submit', '/submit')

    def do_OPTIONS(self):
        if self._is_submit():
            status, body = submit_mod.handle_submit('OPTIONS')
            submit_mod._send_json(self, status, body)
            return
        self.send_error(404)

    def do_GET(self):
        if self._is_submit():
            status, body = submit_mod.handle_submit('GET')
            submit_mod._send_json(self, status, body)
            return
        self._serve_static()

    def do_POST(self):
        if self._is_submit():
            length = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(length) if length else b'{}'
            status, body = submit_mod.handle_submit('POST', raw)
            submit_mod._send_json(self, status, body)
            return
        self.send_error(404)

    def _serve_static(self):
        parsed = urlparse(self.path)
        rel = unquote(parsed.path)
        if rel in ('', '/'):
            rel = '/index.html'
        elif rel in ('/locallist', '/hamsters'):
            rel = rel + '.html'
        rel = rel.lstrip('/')
        if not rel or '..' in rel.split('/') or rel.startswith('.'):
            self.send_error(400, 'Bad path')
            return

        target = (BASE_DIR / rel).resolve()
        try:
            target.relative_to(BASE_DIR.resolve())
        except ValueError:
            self.send_error(400, 'Bad path')
            return

        if target.suffix.lower() not in STATIC_EXT or not target.is_file():
            self.send_error(404, 'Not found')
            return

        ctype = mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
        data = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


def main():
    port = int(os.environ.get('PORT', 5000))
    server = ThreadingHTTPServer(('0.0.0.0', port), LocalHandler)
    print(f'Serving site at http://127.0.0.1:{port}')
    print('POST /api/submit → Supabase plmlist')
    server.serve_forever()


if __name__ == '__main__':
    main()
