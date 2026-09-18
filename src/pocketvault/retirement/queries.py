"""Retirement queries."""
from pocketvault.database import get_connection


def get_holdings(db_path: str) -> list[dict]:
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM retirement_holdings ORDER BY current_value_cents DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_targets(db_path: str) -> list[dict]:
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM retirement_targets ORDER BY target_pct DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary(db_path: str) -> dict | None:
    conn = get_connection(db_path)
    row = conn.execute("""
        SELECT SUM(current_value_cents) as total_value_cents,
               SUM(gain_loss_cents) as total_gain_loss_cents
        FROM retirement_holdings
    """).fetchone()
    conn.close()
    if row and row["total_value_cents"] is not None:
        return dict(row)
    return None
