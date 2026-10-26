"""Localhost HTTP front for the Blender sandbox, so a training container can run
episodes without holding the Docker socket. It only ever runs code inside the
hardened sandbox image (envlib.sandbox, docker backend).

POST /run  {"code": str, "timeout": int}  ->  {"state": dict | null, "error": str | null}
GET  /health                                ->  {"ok": true, "inflight": int}

Usage: python -m sandbox.broker [--port 8765] [--workers 16]
"""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from envlib.sandbox import run_episode

MAX_BODY = 256 * 1024
MAX_TIMEOUT = 60


class Broker(BaseHTTPRequestHandler):
    slots: threading.Semaphore
    inflight = 0
    lock = threading.Lock()

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/health":
            return self._send(404, {"error": "not found"})
        self._send(200, {"ok": True, "inflight": Broker.inflight})

    def do_POST(self):
        if self.path != "/run":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            return self._send(413, {"error": f"body must be 1..{MAX_BODY} bytes"})
        try:
            req = json.loads(self.rfile.read(n))
            code = str(req["code"])
            timeout = min(int(req.get("timeout", 40)), MAX_TIMEOUT)
        except (ValueError, KeyError, TypeError) as e:
            return self._send(400, {"error": f"bad request: {e}"})
        with Broker.slots:
            with Broker.lock:
                Broker.inflight += 1
            try:
                state, err = run_episode(code, timeout=timeout, backend="docker")
            finally:
                with Broker.lock:
                    Broker.inflight -= 1
        self._send(200, {"state": state, "error": err})

    def log_message(self, fmt, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    Broker.slots = threading.Semaphore(a.workers)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Broker)
    srv.daemon_threads = True
    print(f"sandbox broker on 127.0.0.1:{a.port}, {a.workers} workers", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
