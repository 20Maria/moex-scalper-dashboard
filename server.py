#!/usr/bin/env python3
"""
MOEX FUTOI API Proxy Server
Deploybar auf Render.com / Railway / etc.
Mit einfachem Token-basiertem Zugangsschutz.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import ssl
import json
import os
import sys
import io
import hashlib
import hmac
import secrets
import time
from pathlib import Path

# UTF-8 Ausgabe (Windows)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ──────────────────────────────────────────────
# Configuration (Überschreibbar via ENV)
# ──────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8081))
HOST = os.environ.get("HOST", "0.0.0.0")

# MOEX API
MOEX_API_BASE = "https://apim.moex.com/iss/analyticalproducts/futoi"
MOEX_ISS_BASE = "https://iss.moex.com/iss"
API_KEY = ""

# Zugangsschutz: ACCESS_TOKEN via ENV setzen.
# Wenn nicht gesetzt → kein Passwortschutz (nur für lokales Dev).
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")

# Session-Cookie Name
SESSION_COOKIE = "moex_session"
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# SSL Context (Standard-Verifikation)
SSL_CONTEXT = ssl.create_default_context()

# Pfad relativ zum Script, nicht zum Working Directory
SCRIPT_DIR = Path(__file__).parent.resolve()
API_KEY_FILE = SCRIPT_DIR / "api_key.txt"

# Rate Limiting für Login (5 Versuche pro 60 Sekunden pro IP)
_login_attempts = {}  # {ip: [timestamp, ...]}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # Sekunden


def load_api_key():
    """API Key aus ENV oder Datei laden."""
    global API_KEY

    # 1) Aus Environment Variable (Production)
    env_key = os.environ.get("MOEX_API_KEY", "").strip()
    if env_key:
        API_KEY = env_key
        print(f"[OK] API Key aus ENV geladen (Länge: {len(API_KEY)})")
        return

    # 2) Aus Datei (lokale Entwicklung)
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r', encoding='utf-8-sig') as f:
            key = f.read().strip().lstrip('\ufeff').strip()
            if key:
                API_KEY = key
                print(f"[OK] API Key aus {API_KEY_FILE} geladen (Länge: {len(API_KEY)})")
                return

    print("[WARNING] Kein API Key gefunden. Daten haben 15 Tage Verzögerung.")


def make_session_token(nonce=None):
    """Erzeugt einen signierten Session-Token mit zufälligem Nonce."""
    if nonce is None:
        nonce = secrets.token_hex(16)
    payload = f"{ACCESS_TOKEN}:{SESSION_SECRET}:{nonce}"
    signature = hashlib.sha256(payload.encode()).hexdigest()[:32]
    return f"{nonce}.{signature}"


def verify_session_token(token):
    """Verifiziert einen Session-Token anhand des Nonce."""
    if not token or '.' not in token:
        return False
    parts = token.split('.', 1)
    if len(parts) != 2:
        return False
    nonce, provided_signature = parts
    expected = make_session_token(nonce)
    return hmac.compare_digest(token, expected)


def check_auth(cookie_header):
    """Prüft ob gültiges Session-Cookie vorhanden."""
    if not ACCESS_TOKEN:
        return True  # Kein Schutz konfiguriert
    if not cookie_header:
        return False
    # Cookie parsen: "moex_session=abc123; other=val"
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith(f"{SESSION_COOKIE}="):
            val = part.split('=', 1)[1]
            return verify_session_token(val)
    return False


# ──────────────────────────────────────────────
# Login HTML (inline, keine extra Datei nötig)
# ──────────────────────────────────────────────
LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Доступ | MOEX Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Tahoma, sans-serif;
    background: #0a0e1a;
    color: #e0e0e0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}
.login-box {
    background: linear-gradient(135deg, #1a1f2e, #252b3d);
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    width: 100%;
    max-width: 400px;
    text-align: center;
}
.login-box h1 { font-size: 1.5rem; margin-bottom: 8px; }
.login-box p { color: #888; margin-bottom: 24px; font-size: 0.9rem; }
input[type="password"] {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid #3a3f55;
    border-radius: 8px;
    background: #0d1117;
    color: #e0e0e0;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
}
input[type="password"]:focus { border-color: #58a6ff; }
button {
    width: 100%;
    padding: 12px;
    margin-top: 16px;
    border: none;
    border-radius: 8px;
    background: linear-gradient(135deg, #58a6ff, #388bfd);
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
}
button:hover { opacity: 0.9; }
.error { color: #f85149; margin-top: 12px; display: none; font-size: 0.9rem; }
</style>
</head>
<body>
<div class="login-box">
    <h1>🔐 MOEX Dashboard</h1>
    <p>Введите пароль для доступа</p>
    <form id="loginForm">
        <input type="password" id="password" placeholder="Пароль" autofocus>
        <button type="submit">Войти</button>
    </form>
    <div class="error" id="error">Неверный пароль</div>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const pw = document.getElementById('password').value;
    const res = await fetch('/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: pw})
    });
    if (res.ok) {
        window.location.href = '/scalper-dashboard.html';
    } else {
        document.getElementById('error').style.display = 'block';
    }
});
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
# Request Handler
# ──────────────────────────────────────────────
class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Handler mit API-Proxy und einfachem Auth."""

    def __init__(self, *args, **kwargs):
        # Statische Dateien immer aus dem Script-Verzeichnis laden
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self):
        # Favicon: leere Antwort, kein 404 in den Logs
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        # Login-Seite braucht keinen Auth
        if self.path == '/login' or self.path == '/login/':
            self.send_login_page()
            return

        # Auth-Check
        if not self.check_authenticated():
            self.redirect_to_login()
            return

        # API Proxy
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/auth/login':
            self.handle_login()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    # ── Auth ──

    def check_authenticated(self):
        if not ACCESS_TOKEN:
            return True
        cookie = self.headers.get('Cookie', '')
        return check_auth(cookie)

    def redirect_to_login(self):
        self.send_response(302)
        self.send_header('Location', '/login')
        self.end_headers()

    def send_login_page(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(LOGIN_PAGE.encode('utf-8'))

    def _check_rate_limit(self):
        """Prüft ob die IP das Rate Limit überschritten hat. Gibt True zurück wenn blockiert."""
        ip = self.client_address[0]
        now = time.time()
        if ip not in _login_attempts:
            _login_attempts[ip] = []
        # Alte Einträge aufräumen
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
        if len(_login_attempts[ip]) >= RATE_LIMIT_MAX:
            return True
        _login_attempts[ip].append(now)
        return False

    def handle_login(self):
        """POST /auth/login — prüft Token und setzt Cookie."""
        # Rate Limiting prüfen
        if self._check_rate_limit():
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Zu viele Versuche. Bitte 60 Sekunden warten."
            }).encode())
            print(f"[AUTH] Rate limit exceeded for {self.client_address[0]}")
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            token = body.get('token', '')

            if hmac.compare_digest(token, ACCESS_TOKEN):
                session_val = make_session_token()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                # Cookie: 30 Tage gültig, HttpOnly, Secure
                self.send_header(
                    'Set-Cookie',
                    f'{SESSION_COOKIE}={session_val}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax'
                )
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
                print(f"[AUTH] Successful login from {self.client_address[0]}")
            else:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "invalid"}).encode())
                print(f"[AUTH] Failed login attempt from {self.client_address[0]}")

        except Exception as e:
            self.send_response(400)
            self.end_headers()
            print(f"[AUTH] Error: {e}")

    # ── CORS ──

    def _get_allowed_origin(self):
        """Prüft ob der Origin-Header einer erlaubten Quelle entspricht."""
        origin = self.headers.get('Origin', '')
        if not origin:
            return None
        # Nur Requests vom eigenen Server erlauben (localhost oder eigene Domain)
        host = self.headers.get('Host', '')
        if host and origin.endswith('://' + host):
            return origin
        # Zusätzlich: ALLOWED_ORIGINS via ENV (kommagetrennt, für Production)
        extra = os.environ.get("ALLOWED_ORIGINS", "")
        if extra:
            allowed = [o.strip() for o in extra.split(',') if o.strip()]
            if origin in allowed:
                return origin
        return None

    def send_cors_headers(self):
        origin = self._get_allowed_origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')

    # ── API Proxy ──

    def handle_api_request(self):
        try:
            api_path = self.path[5:]  # '/api/' entfernen

            # Check if it's a price/ISS request (e.g. /api/iss/...)
            if api_path.startswith('iss/'):
                iss_path = api_path[4:]  # 'iss/' entfernen
                moex_url = f"{MOEX_ISS_BASE}/{iss_path}"
            else:
                moex_url = f"{MOEX_API_BASE}/{api_path}"

            print(f"-> Proxy: {moex_url}")

            req = urllib.request.Request(moex_url)
            req.add_header('User-Agent', 'MOEX-Dashboard/1.0')
            if API_KEY:
                req.add_header('Authorization', f'Bearer {API_KEY}')

            with urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT) as response:
                data = response.read()
                self.send_response(response.status)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                print(f"[OK] {response.status} ({len(data)} bytes)")

        except urllib.error.HTTPError as e:
            print(f"[ERROR] HTTP {e.code}: {e.reason}")
            self.send_error_response(e.code, str(e.reason))
        except urllib.error.URLError as e:
            print(f"[ERROR] Network: {e.reason}")
            self.send_error_response(503, "Network error")
        except Exception as e:
            print(f"[ERROR] {e}")
            self.send_error_response(500, str(e))

    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': message,
            'status': status_code
        }).encode('utf-8'))

    def log_message(self, format, *args):
        try:
            if args and isinstance(args[0], str) and not args[0].startswith('/api/'):
                super().log_message(format, args)
        except Exception:
            pass


# ──────────────────────────────────────────────
# Server Start
# ──────────────────────────────────────────────
def run_server():
    load_api_key()

    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer((HOST, PORT), ProxyHandler) as httpd:
        print()
        print("=" * 60)
        print("  MOEX FUTOI API Proxy Server")
        print("=" * 60)
        print(f"  Host:  {HOST}")
        print(f"  Port:  {PORT}")
        print(f"  Auth:  {'JA (ACCESS_TOKEN gesetzt)' if ACCESS_TOKEN else 'NEIN (offen)'}")
        print(f"  URL:   http://{'localhost' if HOST == '0.0.0.0' else HOST}:{PORT}/scalper-dashboard.html")
        print("=" * 60)
        print()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[OK] Server gestoppt")
            httpd.shutdown()


if __name__ == "__main__":
    run_server()
