"""Monster API client — read-only, Bearer <REDACTED> auth."""
import json
import os
import urllib.request
from typing import Optional

from pocketvault.database import get_env_path


def get_monster_url() -> str:
    url = os.environ.get("MONSTER_API_URL", "")
    if url:
        return url
    from pocketvault.config import load_config
    return load_config().get("monster_api_url", "")


def get_monster_token() -> str:
    token = os.environ.get("MONSTER_API_TOKEN", "")
    if token:
        return token
    env_path = get_env_path()
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("MONSTER_API_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    from pocketvault.config import load_config
    return load_config().get("monster_api_token", "")


def monster_get(path: str) -> Optional[dict]:
    """GET a Monster API endpoint. Returns dict or None on error."""
    base = get_monster_url().rstrip("/")
    token = get_monster_token()
    if not token:
        raise ValueError("No Monster API token. Set MONSTER_API_TOKEN env var or add to .env")
    req = urllib.request.Request(
        f"{base}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def fetch_stats() -> Optional[dict]:
    return monster_get("/api/stats")


def fetch_inventory() -> Optional[list[dict]]:
    data = monster_get("/api/inventory")
    return data.get("items") if data else None


def fetch_inventory_low() -> Optional[list[dict]]:
    data = monster_get("/api/inventory/low")
    return data.get("items") if data else None


def fetch_summary() -> Optional[dict]:
    return monster_get("/api/report/summary")


def fetch_monthly() -> Optional[list[dict]]:
    data = monster_get("/api/report/monthly")
    return data.get("months") if data else None
