"""Entry point for running multiple applications under a single WSGI server.

This script mounts the following applications behind the same WSGI entrypoint:

- the Django project located in `project01_route_opt`,
- the Flask project located in `project02_auditing`,
- the FastAPI project contained in `project04` (wrapped by a tiny ASGI→WSGI
  adapter), and
- the Django marketplace project in `project03_market_place`, proxied through
  a managed background subprocess.

A lightweight Flask landing page provides navigation between the mounted apps.
"""

import asyncio
import atexit
import http.client
import mimetypes
import os
import subprocess
import sys
import time
from datetime import datetime
from importlib import import_module
from typing import List, Tuple

import requests
from flask import Flask, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure both project directories are discoverable by Python
PROJECT01_PATH = os.path.join(BASE_DIR, 'project01_route_opt')
PROJECT02_PATH = os.path.join(BASE_DIR, 'project02_auditing')
PROJECT03_PATH = os.path.join(BASE_DIR, 'project03_market_place')
PROJECT04_PATH = os.path.join(BASE_DIR, 'project04')

for path in (PROJECT01_PATH, PROJECT02_PATH, PROJECT03_PATH, PROJECT04_PATH):
    if path not in sys.path:
        sys.path.insert(0, path)


# Configure Django settings before importing the WSGI application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
os.environ.setdefault('FASTAPI_ROOT_PATH', '/ledger')


# Import Django WSGI application
from sahayog.wsgi import application as django_application  # type: ignore


# Import Flask application from project02_auditing/app.py
auditing_module = import_module('app')
flask_application = getattr(auditing_module, 'app')


# Import FastAPI application from project04/backend/main.py and expose as WSGI
from backend.main import app as fastapi_app  # type: ignore  # noqa: E402


class SubprocessProxyApplication:
    """WSGI app that proxies requests to a managed subprocess."""

    def __init__(
        self,
        name: str,
        command: List[str],
        base_url: str,
        cwd: str | None = None,
        env: dict | None = None,
        mount_path: str = '',
        frontend_dir: str | None = None,
    ) -> None:
        self.name = name
        self.command = command
        self.base_url = base_url.rstrip('/')
        self.cwd = cwd
        self.extra_env = env or {}
        self.mount_path = ('/' + mount_path.strip('/')) if mount_path else ''
        self.frontend_dir = frontend_dir
        self.session = requests.Session()
        self.process: subprocess.Popen | None = None

        self._start_subprocess()
        atexit.register(self._shutdown)

    def _start_subprocess(self) -> None:
        if self.process and self.process.poll() is None:
            return

        env = os.environ.copy()
        env.update(self.extra_env)

        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 20
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"Failed to start {self.name} subprocess (command: {' '.join(self.command)})."
                )
            try:
                response = self.session.get(self.base_url + '/api/health', timeout=1)
                if response.status_code < 500:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"Timed out waiting for {self.name} subprocess to start")

    def _shutdown(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __call__(self, environ, start_response):
        if not self.process or self.process.poll() is not None:
            self._start_subprocess()

        content_length = environ.get('CONTENT_LENGTH')
        try:
            length = int(content_length) if content_length else 0
        except ValueError:
            length = 0
        body = environ['wsgi.input'].read(length) if length > 0 else b''

        path = environ.get('PATH_INFO', '') or '/'
        query = environ.get('QUERY_STRING', '')
        forward_path = path
        if self.mount_path and path.startswith(self.mount_path):
            forward_path = path[len(self.mount_path):] or '/'

        if (
            self.frontend_dir
            and environ['REQUEST_METHOD'] == 'GET'
            and environ.get('QUERY_STRING', '') == ''
        ):
            relative_path = forward_path.lstrip('/')
            if relative_path in ('', 'index.html', 'home', 'home.html'):
                relative_path = 'LAUNCH_MARKETPLACE.html'
            file_path = os.path.join(self.frontend_dir, relative_path)
            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'text/html; charset=utf-8'
                with open(file_path, 'rb') as fh:
                    content = fh.read()
                start_response('200 OK', [('Content-Type', mime_type), ('Content-Length', str(len(content)))])
                return [content]

        url = f"{self.base_url}{forward_path}"
        if query:
            url = f"{url}?{query}"

        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        content_type = environ.get('CONTENT_TYPE')
        if content_type and 'Content-Type' not in headers:
            headers['Content-Type'] = content_type
        content_length = environ.get('CONTENT_LENGTH')
        if content_length and 'Content-Length' not in headers:
            headers['Content-Length'] = content_length
        if 'Host' not in headers:
            headers['Host'] = self.base_url.replace('http://', '').replace('https://', '')
        if self.mount_path:
            headers['X-Forwarded-Prefix'] = self.mount_path
        headers['X-Forwarded-For'] = environ.get('REMOTE_ADDR', '')
        headers['X-Forwarded-Proto'] = environ.get('wsgi.url_scheme', 'http')

        try:
            upstream_response = self.session.request(
                environ['REQUEST_METHOD'],
                url,
                data=body if body else None,
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as exc:
            start_response('502 Bad Gateway', [('Content-Type', 'text/plain')])
            return [f"Upstream {self.name} service unavailable: {exc}".encode('utf-8')]

        response_headers = [
            (key, value)
            for key, value in upstream_response.headers.items()
            if key.lower() not in {'transfer-encoding', 'connection'}
        ]

        status_line = f"{upstream_response.status_code} {upstream_response.reason}"
        start_response(status_line, response_headers)

        if environ['REQUEST_METHOD'] == 'HEAD':
            return [b'']
        return [upstream_response.content]


class AsgiToWsgi:
    """Minimal adapter that allows running ASGI apps under a WSGI server."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    def __call__(self, environ, start_response):
        content_length = environ.get('CONTENT_LENGTH')
        try:
            length = int(content_length) if content_length else 0
        except ValueError:
            length = 0
        body = environ['wsgi.input'].read(length) if length > 0 else b''

        server_name = environ.get('SERVER_NAME', 'localhost')
        server_port = environ.get('SERVER_PORT', '80')
        client_addr = environ.get('REMOTE_ADDR')
        client_port = environ.get('REMOTE_PORT', '')

        headers: List[Tuple[bytes, bytes]] = []
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').lower().encode('latin1')
                headers.append((header_name, value.encode('latin1')))
        if environ.get('CONTENT_TYPE'):
            headers.append((b'content-type', environ['CONTENT_TYPE'].encode('latin1')))
        if environ.get('CONTENT_LENGTH'):
            headers.append((b'content-length', environ['CONTENT_LENGTH'].encode('latin1')))

        if client_addr:
            try:
                client_tuple = (client_addr, int(client_port)) if str(client_port).isdigit() else (client_addr, 0)
            except (TypeError, ValueError):
                client_tuple = (client_addr, 0)
        else:
            client_tuple = None

        path_info = environ.get('PATH_INFO', '') or '/'

        scope = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': environ.get('SERVER_PROTOCOL', 'HTTP/1.1').split('/')[-1],
            'method': environ['REQUEST_METHOD'],
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'path': path_info,
            'raw_path': environ.get('RAW_URI', path_info).encode('latin1', 'ignore'),
            'query_string': environ.get('QUERY_STRING', '').encode('latin1'),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'headers': headers,
            'client': client_tuple,
            'server': (server_name, int(server_port) if server_port.isdigit() else 0),
        }

        response_status = None
        response_headers: List[Tuple[str, str]] = []
        response_body: List[bytes] = []

        async def receive():
            return {'type': 'http.request', 'body': body, 'more_body': False}

        async def send(message):
            nonlocal response_status, response_headers, response_body
            if message['type'] == 'http.response.start':
                response_status = message['status']
                response_headers = [
                    (name.decode('latin1'), value.decode('latin1'))
                    for name, value in message.get('headers', [])
                ]
            elif message['type'] == 'http.response.body':
                response_body.append(message.get('body', b''))

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.asgi_app(scope, receive, send))
        finally:
            loop.close()

        if response_status is None:
            response_status = 500
            if not response_headers:
                response_headers = [('content-type', 'text/plain; charset=utf-8')]
            if not response_body:
                response_body = [b'Internal Server Error']

        status_line = f"{response_status} {http.client.responses.get(response_status, '')}"
        start_response(status_line, response_headers)
        return response_body


fastapi_application = AsgiToWsgi(fastapi_app)


def create_landing_app() -> Flask:
    """Create a small Flask app for the root landing page and feature previews."""

    landing_app = Flask("landing_app")

    landing_template = """
    <!doctype html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Sahayog Platform</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>♻️</text></svg>">
        <style>
          :root {
            color-scheme: dark;
            font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
            --bg-1: #070b1f;
            --bg-2: #12183d;
            --bg-3: #281c4f;
            --accent: #7c5cff;
            --accent-soft: rgba(124, 92, 255, 0.2);
            --accent-alt: #4ec6ff;
            --text-main: #f6f8ff;
            --text-muted: rgba(216, 221, 255, 0.72);
            --panel-bg: rgba(13, 18, 38, 0.68);
            --panel-border: rgba(255, 255, 255, 0.18);
            --panel-inner: rgba(255, 255, 255, 0.08);
          }

          *, *::before, *::after {
            box-sizing: border-box;
          }

          body {
            margin: 0;
            min-height: 100vh;
            background: linear-gradient(140deg, var(--bg-1), var(--bg-2), var(--bg-3));
            background-size: 220% 220%;
            animation: bodyGradient 18s ease-in-out infinite alternate;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: clamp(2.8rem, 6vw, 4.6rem) clamp(1.6rem, 5vw, 3.4rem);
            color: var(--text-main);
            overflow-x: hidden;
            overflow-y: auto;
          }

          body::before,
          body::after {
            content: "";
            position: fixed;
            width: clamp(260px, 42vw, 460px);
            height: clamp(260px, 42vw, 460px);
            border-radius: 50%;
            filter: blur(140px);
            opacity: 0.55;
            mix-blend-mode: screen;
            pointer-events: none;
            z-index: 0;
          }

          body::before {
            top: -150px;
            left: -130px;
            background: radial-gradient(circle, rgba(124, 92, 255, 0.6), transparent 70%);
            animation: drift 22s linear infinite;
          }

          body::after {
            bottom: -180px;
            right: -150px;
            background: radial-gradient(circle, rgba(78, 198, 255, 0.55), transparent 72%);
            animation: drift 26s linear infinite reverse;
          }

          .portal {
            position: relative;
            max-width: 1080px;
            width: 100%;
            padding: clamp(3rem, 6vw, 4.6rem);
            border-radius: 34px;
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            box-shadow:
              0 70px 120px rgba(5, 10, 26, 0.65),
              0 0 0 1px rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(26px) saturate(150%);
            overflow: hidden;
          }

          .portal::before {
            content: "";
            position: absolute;
            inset: -60% -35% 45% -35%;
            background: conic-gradient(from 115deg, rgba(124, 92, 255, 0.42), rgba(78, 198, 255, 0.32), transparent 70%);
            filter: blur(180px);
            opacity: 0.85;
            animation: halo 32s linear infinite;
            pointer-events: none;
          }

          .portal::after {
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: 32px;
            background: linear-gradient(180deg, rgba(255,255,255,0.08), transparent);
            pointer-events: none;
          }

          .noise {
            position: absolute;
            inset: 0;
            pointer-events: none;
            mix-blend-mode: soft-light;
            opacity: 0.2;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 140 140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E");
          }

          .brand-bar,
          header,
          .experience-grid,
          .insight-ribbon,
          footer {
            position: relative;
            z-index: 2;
          }

          .brand-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.6rem;
            margin-bottom: clamp(2rem, 4vw, 3rem);
          }

          .brand-logo {
            display: flex;
            align-items: center;
            gap: 1rem;
          }

          .brand-logo > span:first-child {
            width: 64px;
            height: 64px;
            border-radius: 20px;
            display: grid;
            place-items: center;
            font-size: 1.9rem;
            background: linear-gradient(135deg, rgba(124,92,255,0.95), rgba(78,198,255,0.92));
            box-shadow: 0 30px 48px rgba(78, 198, 255, 0.34);
          }

          .brand-logo strong {
            font-size: 1.28rem;
            letter-spacing: -0.015em;
          }

          .brand-logo span.meta {
            display: block;
            margin-top: 0.15rem;
            font-size: 0.95rem;
            color: var(--text-muted);
            width: auto;
            height: auto;
            border-radius: 0;
            background: none;
            box-shadow: none;
            font-size: 0.95rem;
          }

          .brand-cta {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.72rem 1.6rem;
            border-radius: 999px;
            font-weight: 600;
            color: #101835;
            background: linear-gradient(135deg, rgba(124,92,255,0.96), rgba(78,198,255,0.96));
            text-decoration: none;
            box-shadow: 0 26px 48px rgba(78, 198, 255, 0.36);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
          }

          .brand-cta:hover {
            transform: translateY(-4px);
            box-shadow: 0 34px 54px rgba(78,198,255,0.4);
          }

          header {
            text-align: center;
            margin-bottom: clamp(2.4rem, 5vw, 3.6rem);
          }

          .hero-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.52rem 1.35rem;
            border-radius: 999px;
            font-size: 0.84rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.82);
            background: var(--accent-soft);
            border: 1px solid rgba(124,92,255,0.32);
          }

          h1 {
            margin: 1.5rem 0 0.85rem;
            font-size: clamp(2.6rem, 5vw, 3.6rem);
            font-weight: 800;
            letter-spacing: -0.035em;
            line-height: 1.08;
            background: linear-gradient(120deg, rgba(255,255,255,0.96), rgba(124,92,255,0.98), rgba(78,198,255,0.92));
            -webkit-background-clip: text;
            color: transparent;
          }

          .subtitle {
            margin: 0 auto;
            max-width: 640px;
            color: var(--text-muted);
            font-size: 1.08rem;
            line-height: 1.68;
          }

          .experience-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: clamp(1.7rem, 3vw, 2.2rem);
          }

          .experience-card {
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding: 2.3rem 2rem;
            border-radius: 24px;
            background: linear-gradient(150deg, rgba(17,22,45,0.9), rgba(18,25,52,0.7));
            border: 1px solid rgba(124,92,255,0.3);
            box-shadow: inset 0 0 0 1px var(--panel-inner);
            transform-style: preserve-3d;
            transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
            --tilt-x: 0deg;
            --tilt-y: 0deg;
            --glow: rgba(124,92,255,0.4);
          }

          .experience-card::before {
            content: "";
            position: absolute;
            inset: -2px;
            border-radius: inherit;
            background: linear-gradient(145deg, var(--glow), rgba(78,198,255,0.32), transparent 70%);
            opacity: 0;
            transition: opacity 0.4s ease;
            pointer-events: none;
          }

          .experience-card::after {
            content: "";
            position: absolute;
            inset: 1.4rem;
            border-radius: 20px;
            background: radial-gradient(circle at var(--glow-x, 50%) var(--glow-y, 50%), var(--glow), transparent 65%);
            opacity: 0;
            transition: opacity 0.35s ease;
            pointer-events: none;
          }

          .experience-card:hover {
            transform: rotateX(var(--tilt-x)) rotateY(var(--tilt-y));
            border-color: rgba(124,92,255,0.48);
            box-shadow:
              0 32px 60px rgba(6,10,27,0.55),
              0 18px 32px rgba(124,92,255,0.32);
          }

          .experience-card:hover::before,
          .experience-card:hover::after {
            opacity: 1;
          }

          .experience-card .chip {
            align-self: flex-start;
            padding: 0.36rem 0.96rem;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.78);
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(12px);
          }

          .experience-card .icon {
            width: 64px;
            height: 64px;
            border-radius: 20px;
            display: grid;
            place-items: center;
            font-size: 1.85rem;
            background: linear-gradient(145deg, rgba(124,92,255,0.94), rgba(78,198,255,0.92));
            box-shadow: 0 24px 42px rgba(78,198,255,0.28);
            animation: float 8s ease-in-out infinite;
          }

          .experience-card h2 {
            margin: 0;
            font-size: 1.4rem;
            letter-spacing: -0.01em;
          }

          .experience-card p {
            margin: 0;
            color: rgba(224,228,255,0.82);
            line-height: 1.62;
            font-size: 1rem;
          }

          .experience-card a {
            margin-top: auto;
            align-self: flex-start;
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.74rem 1.28rem;
            border-radius: 14px;
            font-weight: 600;
            color: rgba(14,19,40,0.9);
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(210,222,255,0.9));
            text-decoration: none;
            box-shadow: 0 22px 34px rgba(124,92,255,0.28);
            transition: transform 0.28s ease, box-shadow 0.28s ease;
          }

          .experience-card a:hover {
            transform: translateX(6px);
            box-shadow: 0 28px 40px rgba(124,92,255,0.32);
          }

          .experience-card[data-theme=\"audits\"] { --glow: rgba(146,104,255,0.36); }
          .experience-card[data-theme=\"marketplace\"] { --glow: rgba(26,188,156,0.34); }
          .experience-card[data-theme=\"ledger\"] { --glow: rgba(255,167,111,0.36); }

          .insight-ribbon {
            margin-top: clamp(2.6rem, 5vw, 3.8rem);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 1.2rem;
            padding: 1.4rem 1.2rem;
            border-radius: 24px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(124,92,255,0.12);
          }

          .insight-pill {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.7rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.82);
            color: rgba(13,18,36,0.9);
            box-shadow: 0 18px 30px rgba(12,18,38,0.18);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
          }

          .insight-pill strong {
            color: rgba(13,18,36,0.92);
          }

          .insight-pill:hover {
            transform: translateY(-4px);
            box-shadow: 0 24px 36px rgba(12,18,38,0.22);
          }

          .insight-pill .spark {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            font-size: 1.2rem;
            background: rgba(124,92,255,0.18);
            color: rgba(124,92,255,0.95);
          }

          footer {
            margin-top: clamp(2.6rem, 5vw, 4.2rem);
            text-align: center;
            color: rgba(214, 220, 255, 0.64);
            font-size: 0.96rem;
          }

          @keyframes bodyGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }

          @keyframes drift {
            0% { transform: translate3d(0,0,0); }
            50% { transform: translate3d(18px, -20px, 0); }
            100% { transform: translate3d(0,0,0); }
          }

          @keyframes float {
            0%, 100% { transform: translate3d(0,0,0); }
            50% { transform: translate3d(20px, -18px, 0); }
          }

          @keyframes halo {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }

          @media (max-width: 900px) {
            .brand-bar {
              flex-direction: column;
              align-items: flex-start;
            }

            .brand-cta {
              align-self: flex-start;
            }

            .insight-ribbon {
              grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            }
          }

          @media (max-width: 640px) {
            body {
              padding: 2.4rem 1.2rem;
            }

            .portal {
              padding: 2.4rem 1.8rem;
            }

            .experience-grid {
              grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            }
          }
        </style>
      </head>
      <body>
        <main class="portal">
          <div class="noise" aria-hidden="true"></div>
          <div class="brand-bar">
            <div class="brand-logo">
              <span>♻️</span>
              <div>
                <strong>Sahayog Platform</strong>
                <span class="meta">Integrated sustainability suite</span>
              </div>
            </div>
            <a class="brand-cta" href="#suite">Explore suite</a>
          </div>

          <header>
            <span class="hero-tag">Integrated Sustainability Suite</span>
            <h1>Sahayog Master Platform</h1>
            <p class="subtitle">
              Choose an experience below to explore operational intelligence across waste management,
              auditing, trading, and finance. Launch-ready modules are one click away.
            </p>
          </header>

          <section id="suite" class="experience-grid" aria-label="Available applications">
            <article class="experience-card" data-theme="routes">
              <span class="chip">Logistics</span>
              <div class="icon">🚚</div>
              <h2>Route Optimizer</h2>
              <p>
                Plan efficient collection routes, visualize fleets, and unlock AI-driven logistics recommendations tailored for
                urban waste ecosystems.
              </p>
              <a href="/experience/route-optimizer">Explore details →</a>
            </article>

            <article class="experience-card" data-theme="audits">
              <span class="chip">Compliance</span>
              <div class="icon">🧾</div>
              <h2>Auditing Suite</h2>
              <p>
                Run advanced waste audits, upload evidence, and leverage AI insights to produce actionable compliance
                and sustainability reports.
              </p>
              <a href="/experience/auditing-suite">Explore details →</a>
            </article>

            <article class="experience-card" data-theme="marketplace">
              <span class="chip">Trading</span>
              <div class="icon">🛒</div>
              <h2>Waste Marketplace</h2>
              <p>
                Discover AI-curated listings, track bids in real time, and connect buyers & sellers within the circular
                economy marketplace.
              </p>
              <a href="/experience/marketplace">Explore details →</a>
            </article>

            <article class="experience-card" data-theme="ledger">
              <span class="chip">Finance</span>
              <div class="icon">📊</div>
              <h2>Financial Ledger</h2>
              <p>
                Generate net waste valuations, benchmark performance, and download investor-ready financial intelligence in
                seconds.
              </p>
              <a href="/experience/financial-ledger">Explore details →</a>
            </article>
          </section>

          <section class="insight-ribbon" aria-label="Platform highlights">
            <div class="insight-pill">
              <span class="spark">⚡</span>
              <div>
                <strong>Real-time</strong><br />
                Orchestrated operations
              </div>
            </div>
            <div class="insight-pill">
              <span class="spark">🌐</span>
              <div>
                <strong>Connected</strong><br />
                Audits · Logistics · Trading
              </div>
            </div>
            <div class="insight-pill">
              <span class="spark">📈</span>
              <div>
                <strong>Financial grade</strong><br />
                Intelligence & reporting
              </div>
            </div>
            <div class="insight-pill">
              <span class="spark">🔐</span>
              <div>
                <strong>Enterprise</strong><br />
                Security & governance
              </div>
            </div>
          </section>

          <footer>
            Crafted with sustainability in mind · Sahayog Platform © {{ year }}
          </footer>
        </main>
      </body>
    </html>
    """

    feature_template = """
    <!doctype html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{{ title }} · Sahayog Platform</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>♻️</text></svg>">
        <style>
          :root {
            color-scheme: dark;
            font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
            --bg-1: #050914;
            --bg-2: #0d132d;
            --accent: {{ accent }};
            --accent-soft: {{ accent_soft }};
            --text-main: #f6f8ff;
            --text-muted: rgba(216, 221, 255, 0.72);
            --panel-bg: rgba(12, 18, 38, 0.74);
            --panel-border: rgba(255, 255, 255, 0.16);
          }

          *, *::before, *::after {
            box-sizing: border-box;
          }

          body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: clamp(2.4rem, 6vw, 4rem) clamp(1.4rem, 5vw, 3.2rem);
            background: radial-gradient(circle at 18% 22%, rgba(124, 92, 255, 0.28), transparent 55%),
                        radial-gradient(circle at 82% 78%, rgba(78, 198, 255, 0.26), transparent 60%),
                        linear-gradient(145deg, var(--bg-1), var(--bg-2));
            color: var(--text-main);
            overflow-x: hidden;
            overflow-y: auto;
          }

          .page {
            position: relative;
            max-width: 960px;
            width: 100%;
            padding: clamp(2.6rem, 6vw, 4.2rem);
            border-radius: 30px;
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            box-shadow:
              0 60px 120px rgba(4, 8, 20, 0.65),
              0 0 0 1px rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(26px) saturate(150%);
            overflow: hidden;
          }

          .page::after {
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: 28px;
            background: linear-gradient(180deg, rgba(255,255,255,0.08), transparent);
            pointer-events: none;
          }

          nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.2rem;
            margin-bottom: clamp(2rem, 4vw, 3rem);
          }

          .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
          }

          .logo span {
            width: 56px;
            height: 56px;
            border-radius: 18px;
            display: grid;
            place-items: center;
            font-size: 1.7rem;
            background: linear-gradient(135deg, rgba(124,92,255,0.92), rgba(78,198,255,0.88));
            box-shadow: 0 24px 42px rgba(78,198,255,0.3);
          }

          .logo strong {
            font-size: 1.18rem;
            letter-spacing: -0.01em;
          }

          .nav-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem 1.35rem;
            border-radius: 999px;
            font-weight: 600;
            color: rgba(10,15,36,0.92);
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(208,220,255,0.9));
            text-decoration: none;
            box-shadow: 0 20px 36px rgba(124,92,255,0.28);
            transition: transform 0.28s ease, box-shadow 0.28s ease;
          }

          .nav-link:hover {
            transform: translateY(-3px);
            box-shadow: 0 26px 42px rgba(124,92,255,0.32);
          }

          header {
            text-align: left;
          }

          .tag {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1.3rem;
            border-radius: 999px;
            font-size: 0.82rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.82);
            background: var(--accent-soft);
            border: 1px solid rgba(255,255,255,0.18);
          }

          h1 {
            margin: 1.45rem 0 0.85rem;
            font-size: clamp(2.4rem, 5vw, 3.4rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.12;
            background: linear-gradient(120deg, rgba(255,255,255,0.96), var(--accent));
            -webkit-background-clip: text;
            color: transparent;
          }

          .lead {
            margin: 0;
            max-width: 580px;
            color: var(--text-muted);
            font-size: 1.04rem;
            line-height: 1.68;
          }

          .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: clamp(1.8rem, 4vw, 2.6rem);
            margin-top: clamp(2.2rem, 5vw, 3.4rem);
          }

          .panel {
            padding: 1.9rem;
            border-radius: 22px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
          }

          .panel h2 {
            margin: 0 0 1rem;
            font-size: 1.2rem;
            letter-spacing: -0.01em;
          }

          .panel p,
          .panel li {
            margin: 0;
            color: rgba(216,221,255,0.8);
            line-height: 1.62;
            font-size: 0.98rem;
          }

          .panel ul {
            margin: 0;
            padding-left: 1.15rem;
            list-style: none;
          }

          .panel ul li::before {
            content: "•";
            margin-right: 0.6rem;
            color: var(--accent);
          }

          .panel.metrics ul li::before {
            content: "▲";
            font-size: 0.75rem;
            transform: translateY(-1px);
            display: inline-block;
            margin-right: 0.4rem;
            color: var(--accent);
          }

          .launch {
            padding: 2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255,255,255,0.08), transparent);
            border: 1px solid rgba(255,255,255,0.14);
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
          }

          .launch a {
            display: inline-flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.85rem 1.6rem;
            border-radius: 16px;
            font-weight: 600;
            color: #0d1328;
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(208,220,255,0.9));
            text-decoration: none;
            box-shadow: 0 24px 38px rgba(124,92,255,0.32);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
          }

          .launch a:hover {
            transform: translateY(-3px);
            box-shadow: 0 30px 44px rgba(124,92,255,0.36);
          }

          footer {
            margin-top: clamp(2.4rem, 5vw, 3.6rem);
            text-align: center;
            color: rgba(214,220,255,0.66);
            font-size: 0.94rem;
          }

          @media (max-width: 820px) {
            nav {
              flex-direction: column;
              align-items: flex-start;
              gap: 1.3rem;
            }
          }

          @media (max-width: 600px) {
            body {
              padding: 2.2rem 1.1rem;
            }

            .page {
              padding: 2.2rem 1.6rem;
            }
          }
        </style>
      </head>
      <body>
        <main class="page">
          <nav>
            <div class="logo">
              <span>{{ icon }}</span>
              <strong>{{ title }}</strong>
            </div>
            <a class="nav-link" href="/">← Back to master suite</a>
          </nav>

          <header>
            <span class="tag">{{ tag }}</span>
            <h1>{{ headline }}</h1>
            <p class="lead">{{ intro }}</p>
          </header>

          <section class="grid" aria-label="Highlights">
            <div class="panel">
              <h2>Why teams love it</h2>
              <ul>
                {% for point in highlights %}
                  <li>{{ point }}</li>
                {% endfor %}
              </ul>
            </div>
            <div class="panel">
              <h2>{{ story_title }}</h2>
              <p>{{ story_body }}</p>
            </div>
            <div class="panel">
              <h2>How it works</h2>
              <p>{{ workflow }}</p>
            </div>
            <div class="panel">
              <h2>Signature capabilities</h2>
              <ul>
                {% for item in capabilities %}
                  <li>{{ item }}</li>
                {% endfor %}
              </ul>
            </div>
            <div class="panel">
              <h2>High-impact use cases</h2>
              <ul>
                {% for use_case in use_cases %}
                  <li>{{ use_case }}</li>
                {% endfor %}
              </ul>
            </div>
            <div class="panel metrics">
              <h2>Success metrics</h2>
              <ul>
                {% for metric in metrics %}
                  <li>{{ metric }}</li>
                {% endfor %}
              </ul>
            </div>
            <div class="launch">
              <div>
                <strong>Launch the live platform</strong>
                <p style="margin:0;color:rgba(214,220,255,0.72);font-size:0.95rem;">
                  Opens the production-ready experience in a dedicated view.
                </p>
              </div>
              <a href="{{ launch_url }}">Launch {{ title }} ↗</a>
            </div>
          </section>

          <footer>Crafted with sustainability in mind · Sahayog Platform © {{ year }}</footer>
        </main>
      </body>
    </html>
    """

    feature_configs = {
        "route-optimizer": {
            "title": "Route Optimizer",
            "icon": "🚚",
            "tag": "Logistics Control Center",
            "headline": "AI-first logistics for zero-waste fleets.",
            "intro": "Model fleet capacity, design collection windows, and respond to last-mile disruptions with predictive routing intelligence.",
            "highlights": [
                "Dynamic route simulation with congestion awareness.",
                "Live fleet overlays with exception alerts.",
                "Volume forecasting that adapts to seasonality automatically.",
            ],
            "story_title": "From depot to street in minutes",
            "story_body": "The Route Optimizer ingests depot constraints, vehicle capacities, and disposal site rules to engineer hyper-efficient collection sequences. Interactive sandboxes help operations test contingencies and deploy with confidence.",
            "workflow": "Telemetry from trucks, fill-level sensors, and ERP orders is federated into a single planning graph. Optimization engines evaluate millions of route combinations, surface the top scenarios, and publish dispatch sheets or API payloads back into your TMS.",
            "capabilities": [
                "Scenario designer for storms, strikes, or special events.",
                "Geo-fenced service level warnings and missed-pickup recovery plans.",
                "Smart fuel and emissions calculator anchored to route output.",
                "Collaboration timeline so fleet, dispatch, and customer success stay synchronized.",
            ],
            "use_cases": [
                "Municipal recycling routes with day-of-week variability.",
                "Industrial campus collection with hazardous transfer windows.",
                "Smart city pilot programs seeking to cut mileage by double digits.",
            ],
            "metrics": [
                "Up to 18% reduction in total miles driven across pilot cities.",
                "12–15% lift in on-time collection performance for critical accounts.",
                "Verified 9% decrease in fuel spend through optimized dispatching.",
            ],
            "launch_url": "/django/",
            "accent": "#7c5cff",
            "accent_soft": "rgba(124, 92, 255, 0.2)",
        },
        "auditing-suite": {
            "title": "Auditing Suite",
            "icon": "🧾",
            "tag": "Compliance Intelligence",
            "headline": "Evidence-driven audits with executive-ready insight.",
            "intro": "Digitize audit trails, benchmark performance, and surface non-compliance in minutes—not weeks.",
            "highlights": [
                "Guided audit workflows with multimedia capture.",
                "Comparative scoring against regulatory thresholds.",
                "Instant sustainability storyboards for stakeholders.",
            ],
            "story_title": "Regulation-ready in every cycle",
            "story_body": "Upload photographic evidence, annotate contamination hotspots, and turn on anomaly alerts. Automated playbooks translate raw inspections into sustainability narratives that resonate with leadership.",
            "workflow": "Frontline crews capture photos, video, and voice notes that sync instantly to the portal. The auditing engine tags findings, assigns severity, and links corrective actions. Compliance teams approve, escalate, or archive with full version history.",
            "capabilities": [
                "Offline-friendly mobile capture with automatic cloud sync.",
                "Regulation templates (EPA, CPCB, ISO 14001) ready out-of-the-box.",
                "Root-cause clustering that groups repeat violations by material, site, or vendor.",
                "Executive briefing generator translating audit data into KPI slides in seconds.",
            ],
            "use_cases": [
                "Monthly compliance sweeps across multi-site manufacturing networks.",
                "Third-party audits for vendor certification and ESG disclosures.",
                "Corrective action programs where progress must be tracked across quarters.",
            ],
            "metrics": [
                "30% faster audit cycle time reported by municipal clients.",
                "40% uptick in closure rate for corrective actions within 60 days.",
                "Audit evidence retrieval time down from hours to seconds thanks to tagging.",
            ],
            "launch_url": "/flask/",
            "accent": "#b388ff",
            "accent_soft": "rgba(179, 136, 255, 0.2)",
        },
        "marketplace": {
            "title": "Waste Marketplace",
            "icon": "🛒",
            "tag": "Circular Trading Hub",
            "headline": "Match waste streams with buyers in real-time.",
            "intro": "Curated listings, smart bid orchestration, and transparent negotiation tools for the circular economy.",
            "highlights": [
                "AI-ranked offers tuned to quality and logistics cost.",
                "Negotiation trails with compliance documentation built in.",
                "Demand heatmaps that flag emerging recovery opportunities.",
            ],
            "story_title": "Price discovery without guesswork",
            "story_body": "The Marketplace exposes supply to verified buyers, orchestrates bids, and captures price intelligence in one place. Machine learning adjusts guidance continuously, letting you monetise recyclables at their peak value.",
            "workflow": "Suppliers publish lots with specs, imagery, and compliance certificates. Buyers receive instant fit scores, place bids, and execute smart contracts. Settlement documents and logistics instructions flow back into your ERP with zero swivel-chair work.",
            "capabilities": [
                "Lot intelligence showing historical price curves and contamination penalties.",
                "Preferred buyer routing based on distance, capacity, and past performance.",
                "Digital contracting with e-signature and automated compliance attachments.",
                "Bid war room for category managers to monitor live negotiations.",
            ],
            "use_cases": [
                "Municipal material recovery facility sourcing higher-value buyers for baled fiber.",
                "Industrial by-product exchange connecting chemical producers with recyclers.",
                "Compost cooperatives selling verified organic material to agriculture off-takers.",
            ],
            "metrics": [
                "Average realized price uplift of 11–17% versus static broker lists.",
                "Bid-to-award cycle times cut from days to under two hours.",
                "95% reduction in email-based negotiation clutter for trading desks.",
            ],
            "launch_url": "/marketplace/",
            "accent": "#22ddb0",
            "accent_soft": "rgba(34, 221, 176, 0.2)",
        },
        "financial-ledger": {
            "title": "Financial Ledger",
            "icon": "📊",
            "tag": "Waste Financial Cloud",
            "headline": "Transform waste into auditable financial impact.",
            "intro": "Generate net waste value, model price sensitivity, and export CFO-ready insights from a single ledger.",
            "highlights": [
                "Automated NWV computation with variance tracking.",
                "Scenario explorer for market price and contamination swings.",
                "Audit-proof PDF narrating revenue, risk, and sustainability wins.",
            ],
            "story_title": "Where finance meets materials",
            "story_body": "The Financial Ledger fuses transactional waste data with pricing intelligence to surface risk, upside, and compliance posture. Finance teams see the full P&L context while operations gain clear levers to drive profitability.",
            "workflow": "Transactions stream in from ERP, hauling, and audit systems. Pricing services enrich the data. Calculators derive revenue, cost, and margin, while dashboards benchmark performance. One click exports investor-ready packs and regulatory filings.",
            "capabilities": [
                "Material-level profit and loss with drill-down to individual collection points.",
                "Scenario sandbox to test market price, quality, or volume shocks.",
                "Automated PDF and spreadsheet report generation for CFO, ESG, and board audiences.",
                "Alerting engine that flags margin erosion or compliance risk in real time.",
            ],
            "use_cases": [
                "Enterprise waste teams needing quarterly ESG and financial disclosures.",
                "Recyclers tracking commodity exposure and hedging strategies.",
                "Integrated facilities balancing contract hauling costs against revenue share.",
            ],
            "metrics": [
                "8–12% improvement in net waste value realized within the first six months.",
                "Financial closing time for waste reporting cut from two weeks to two days.",
                "Stakeholder reporting effort reduced by 65% thanks to automated PDF briefs.",
            ],
            "launch_url": "/ledger/",
            "accent": "#ffa973",
            "accent_soft": "rgba(255, 169, 115, 0.2)",
        },
    }

    @landing_app.route("/")
    def index():  # type: ignore
        return render_template_string(landing_template, year=datetime.utcnow().year)

    def make_feature_view(cfg: dict):
        def view() -> str:
            return render_template_string(
                feature_template,
                year=datetime.utcnow().year,
                **cfg,
            )

        return view

    for slug, cfg in feature_configs.items():
        landing_app.add_url_rule(
            f"/experience/{slug}",
            endpoint=f"experience_{slug}",
            view_func=make_feature_view(cfg),  # type: ignore[arg-type]
        )

    return landing_app


landing_application = create_landing_app()

# Managed subprocess proxy for the marketplace Django project
MARKETPLACE_MANAGE = os.path.join(PROJECT03_PATH, 'manage.py')
marketplace_proxy_application = SubprocessProxyApplication(
    name='Marketplace',
    command=[
        sys.executable,
        MARKETPLACE_MANAGE,
        'runserver',
        '127.0.0.1:9100',
        '--noreload',
    ],
    base_url='http://127.0.0.1:9100',
    cwd=PROJECT03_PATH,
    env={
        'FORCE_SCRIPT_NAME': '/marketplace',
        'DJANGO_SETTINGS_MODULE': 'sahayog_marketplace.settings',
    },
    mount_path='/marketplace',
    frontend_dir=PROJECT03_PATH,
)


# Mount the applications using DispatcherMiddleware
application = DispatcherMiddleware(
    landing_application,
    {
        '/django': django_application,
        '/flask': flask_application,
        '/marketplace': marketplace_proxy_application,
        '/ledger': fastapi_application,
    },
)


def run(host: str = '0.0.0.0', port: int = 8000, use_reloader: bool = True) -> None:
    """Run a development server that serves the combined WSGI application."""

    run_simple(host, port, application, use_reloader=use_reloader, use_debugger=True, threaded=True)


if __name__ == '__main__':
    run()


