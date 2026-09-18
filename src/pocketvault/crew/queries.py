from pocketvault.database import get_connection

def get_pocket_balances(db_path: str) -> list[dict]:
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM pocket_balances").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_ready_to_budget(db_path: str) -> float:
    conn = get_connection(db_path)
    row = conn.execute("SELECT balance_cents FROM pockets WHERE name = 'Autopilot Reserve' AND active = 1").fetchone()
    conn.close()
    return (row["balance_cents"] or 0) / 100.0 if row else 0.0

def get_total_balance(db_path: str) -> float:
    conn = get_connection(db_path)
    row = conn.execute("SELECT total FROM total_balance").fetchone()
    conn.close()
    return (row["total"] or 0) / 100.0
