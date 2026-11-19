"""Lokalni statični poslužitelj koji aplikaciju poslužuje iz podmape (kao GitHub Pages: /<repo>/)."""
import contextlib
import functools
import http.server
import os
import socket
import threading
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
PODMAPA = "rucak-u-dva"


class Tihi(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


Tihi.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                       ".webmanifest": "application/manifest+json", ".js": "text/javascript",
                       ".svg": "image/svg+xml", ".json": "application/json"}


@contextlib.contextmanager
def posluzi():
    """Vraća osnovni URL, npr. http://127.0.0.1:PORT/rucak-u-dva/"""
    omot = KORIJEN / ".radno" / "posluzitelj"
    omot.mkdir(parents=True, exist_ok=True)
    veza = omot / PODMAPA
    if not veza.exists():
        os.symlink(KORIJEN, veza)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Tihi, directory=str(omot)))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://localhost:{port}/{PODMAPA}/"
    finally:
        srv.shutdown()
