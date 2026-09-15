#!/bin/bash
# Setup for Crew webhook receiver with self-signed SSL

# 1. Install deps
pip install fastapi uvicorn

# 2. Generate self-signed cert
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem \
  -days 365 -nodes \
  -subj "/CN=vault.pcitsolutions.com"

# 3. Run
python crew_webhook_fastapi.py
