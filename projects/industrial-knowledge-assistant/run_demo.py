"""Run a localhost-only demo server for the static portfolio and RAG API."""

from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from engine import DEFAULT_RETRIEVER, answer


REPO_ROOT = Path(__file__).resolve().parents[2]


class DemoHandler(SimpleHTTPRequestHandler):
    server_version = "PortfolioDemo"
    sys_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.endswith("/api/health"):
            self.send_json(200, {
                "status": "ok",
                "documents": len(DEFAULT_RETRIEVER.documents),
                "retrieval": "local lexical ranking",
            })
            return
        if parsed.path.endswith("/api/ask"):
            query = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not query or len(query) > 240:
                self.send_json(400, {"error": "question must contain between 1 and 240 characters"})
                return
            self.send_json(200, answer(query))
            return
        self.path = parsed.path
        return super().do_GET()

    def send_json(self, status: int, body: dict):
        payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        # Avoid writing visitors' questions to the terminal as access-log queries.
        if "/api/ask" in self.path:
            sys.stderr.write(f"{self.address_string()} - API request [query omitted]\n")
        else:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DemoHandler)
    print("Demo server: http://127.0.0.1:8000/projects/industrial-knowledge-assistant/")
    print("Bound to localhost only. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server.")
        server.server_close()
        sys.exit(0)
