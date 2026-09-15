from pocketvault.database import get_connection

def get_pocket_balances(db_path: str) -> list[dict]:
    """Get all pockets with computed balances."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM pocket_balances").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_ready_to_budget(db_path: str) -> float:
    """Get Autopilot Reserve balance (ready to budget)."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT balance FROM ready_to_budget").fetchone()
    conn.close()
    return row["balance"] if row else 0.0

def get_total_crew_balance(db_path: str) -> float:
    """Get total balance across all active pockets."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT total FROM total_crew_balance").fetchone()
    conn.close()
    return row["total"] if row else 0.0

def get_pocket_by_name(db_path: str, name: str) -> dict | None:
    """Get single pocket by name."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM pockets WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_entries_for_pocket(db_path: str, pocket_name: str, limit: int = 100) -> list[dict]:
    """Get recent entries for a pocket."""
    conn = get_connection(db_path)
    rows = conn.execute("""
        SELECT e.* FROM entries e
        JOIN pockets p ON p.id = e.pocket_id
        WHERE p.name = ?
        ORDER BY e.timestamp DESC
        LIMIT ?
    """, (pocket_name, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
