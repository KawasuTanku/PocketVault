#!/usr/bin/env python3
"""Minimal Crew webhook receiver — logs all requests."""
import json, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        ts = datetime.now().isoformat()
        try:
            data = json.loads(body)
            print(f"\n[{ts}] POST {self.path}\n{json.dumps(data, indent=2)}")
        except:
            print(f"\n[{ts}] POST {self.path} (raw)\n{body.decode()}")
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8989
print(f"Listening on :{port} — use ngrok or localtunnel to expose to Crew")
HTTPServer(("0.0.0.0", port), H).serve_forever()
