#!/usr/bin/env python3
"""Webhook receiver for Crew — logs all incoming requests to discover the payload format."""

import json
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

LOG_FILE = Path.home() / ".local" / "share" / "pocketvault" / "webhooks.jsonl"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        # Log the full request
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "method": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body": body.decode("utf-8", errors="replace")
        }
        
        # Try to pretty-print JSON
        try:
            parsed = json.loads(body)
            log_entry["json"] = parsed
            print(f"\n{'='*60}")
            print(f"Webhook received at {timestamp}")
            print(f"Path: {self.path}")
            print(f"Headers: {json.dumps(dict(self.headers), indent=2)}")
            print(f"Body: {json.dumps(parsed, indent=2)}")
            print(f"{'='*60}")
        except json.JSONDecodeError:
            print(f"\n{'='*60}")
            print(f"Webhook received at {timestamp}")
            print(f"Path: {self.path}")
            print(f"Headers: {json.dumps(dict(self.headers), indent=2)}")
            print(f"Body (raw): {body.decode('utf-8', errors='replace')}")
            print(f"{'='*60}")
        
        # Append to log file
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Send 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Crew webhook receiver is running. POST to /webhook")
    
    def log_message(self, format, *args):
        pass  # Suppress default logging


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8989
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"Crew webhook receiver listening on port {port}")
    print(f"Logging to: {LOG_FILE}")
    print(f"URL: http://localhost:{port}/webhook")
    print("Waiting for webhooks...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
