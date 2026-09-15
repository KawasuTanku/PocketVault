from datetime import datetime
from pocketvault.database import get_connection

def transfer_between_pockets(db_path: str, from_pocket: str, to_pocket: str, amount: float, note: str = ""):
    """Create paired entries for a transfer between pockets."""
    conn = get_connection(db_path)
    
    from_id = conn.execute("SELECT id FROM pockets WHERE name = ?", (from_pocket,)).fetchone()["id"]
    to_id = conn.execute("SELECT id FROM pockets WHERE name = ?", (to_pocket,)).fetchone()["id"]
    
    timestamp = datetime.now().isoformat()
    
    # Create outgoing entry
    cursor = conn.execute(
        "INSERT INTO entries (pocket_id, amount, title, timestamp, status, entry_type, note) VALUES (?, ?, ?, ?, 'cleared', 'manual', ?)",
        (from_id, -amount, f"Transfer to {to_pocket}", timestamp, note)
    )
    from_entry_id = cursor.lastrowid
    
    # Create incoming entry
    cursor = conn.execute(
        "INSERT INTO entries (pocket_id, amount, title, timestamp, status, entry_type, note, paired_entry_id) VALUES (?, ?, ?, ?, 'cleared', 'manual', ?, ?)",
        (to_id, amount, f"Transfer from {from_pocket}", timestamp, note, from_entry_id)
    )
    to_entry_id = cursor.lastrowid
    
    # Update outgoing entry with paired ID
    conn.execute("UPDATE entries SET paired_entry_id = ? WHERE id = ?", (to_entry_id, from_entry_id))
    
    conn.commit()
    conn.close()
