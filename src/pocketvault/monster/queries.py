"""Monster queries."""
from pocketvault.database import get_connection


def get_latest_snapshot(db_path: str) -> dict | None:
    conn = get_connection(db_path)
    row = conn.execute("""
        SELECT * FROM monster_snapshots ORDER BY captured_at DESC LIMIT 1
    """).fetchone()
    conn.close()
    return dict(row) if row else None


def get_monster_products(db_path: str, low_only: bool = False) -> list[dict]:
    conn = get_connection(db_path)
    query = "SELECT * FROM monster_products"
    if low_only:
        query += " WHERE low_stock = 1"
    query += " ORDER BY name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monster_monthly(db_path: str, limit: int = 6) -> list[dict]:
    """Get monthly P&L history from local snapshots or API."""
    from pocketvault.monster.api import fetch_monthly
    data = fetch_monthly()
    if data:
        return data[-limit:]
    return []
