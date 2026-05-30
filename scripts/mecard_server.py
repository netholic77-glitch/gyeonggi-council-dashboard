#!/usr/bin/env python3
"""터닝메카드 식별 & 중고가 조회 로컬 서버"""

import os, json, base64, urllib.parse, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = 8080
ROOT = Path(__file__).parent.parent


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 네이버 쇼핑 가격 조회 프록시 (CORS 우회)
        if path == '/api/naver-price':
            self._handle_naver_price(parsed.query)
            return

        # 정적 파일 서빙
        if path == '/' or path == '':
            path = '/index.html'

        file_path = ROOT / path.lstrip('/')
        if file_path.exists() and file_path.is_file():
            self._serve_file(file_path)
        else:
            self._send_404()

    def do_OPTIONS(self):
        self.send_response(200)
        self._add_cors()
        self.end_headers()

    def _handle_naver_price(self, query_string):
        params = urllib.parse.parse_qs(query_string)
        query = params.get('query', [''])[0]
        client_id = params.get('clientId', [''])[0]
        client_secret = params.get('clientSecret', [''])[0]

        # 환경 변수 우선
        client_id = client_id or os.environ.get('NAVER_CLIENT_ID', '')
        client_secret = client_secret or os.environ.get('NAVER_CLIENT_SECRET', '')

        if not client_id or not client_secret:
            self._send_json([], 200)
            return

        try:
            api_url = (
                'https://openapi.naver.com/v1/search/shop.json'
                f'?query={urllib.parse.quote(query)}&display=5&sort=sim'
            )
            req = urllib.request.Request(api_url, headers={
                'X-Naver-Client-Id': client_id,
                'X-Naver-Client-Secret': client_secret,
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            self._send_json(data.get('items', []))
        except Exception as e:
            print(f'Naver API 오류: {e}')
            self._send_json([])

    def _serve_file(self, path: Path):
        ext = path.suffix.lower()
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
        }
        ct = content_types.get(ext, 'application/octet-stream')
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', len(data))
        self._add_cors()
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._add_cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        body = b'Not Found'
        self.send_response(404)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _add_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')


if __name__ == '__main__':
    server = HTTPServer(('localhost', PORT), Handler)
    print(f'터닝메카드 서버 시작: http://localhost:{PORT}/turningmecard.html')
    print(f'Ctrl+C로 종료')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n서버 종료')
