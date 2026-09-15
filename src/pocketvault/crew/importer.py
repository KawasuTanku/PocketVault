import uuid
from typing import Iterable
from pocketvault.database import get_connection

# Pocket naming convention — names matching these are actual pockets, not payees
POCKET_PREFIXES = ("spend:", "save:", "bill:", "outbox:", "reserve:", "invest:")
SYSTEM_POCKETS = {"checking", "autopilot reserve", "credit card reserve"}


def is_pocket(name: str) -> bool:
    """Check if a name is a pocket (not a payee/bill)."""
    name_lower = name.lower().strip()
    if name_lower in SYSTEM_POCKETS:
        return True
    return name_lower.startswith(POCKET_PREFIXES)


def import_crew_entries(db_path: str, entries: Iterable[dict]) -> dict:
    """Import Crew entries into database. Returns summary dict."""
    conn = get_connection(db_path)
    batch_id = str(uuid.uuid4())
    imported = 0
    new_pockets = 0
    duplicates = 0
    unknown_pockets = set()
    
    for entry in entries:
        pocket_name = entry["pocket_name"]
        
        # Skip payees — only import pockets
        if not is_pocket(pocket_name):
            continue
        
        # Get or create pocket
        pocket = conn.execute("SELECT id FROM pockets WHERE name = ?", (pocket_name,)).fetchone()
        if pocket:
            pocket_id = pocket["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO pockets (name) VALUES (?)",
                (pocket_name,)
            )
            pocket_id = cursor.lastrowid
            new_pockets += 1
            unknown_pockets.add(pocket_name)
        
        # Check for duplicate
        existing = conn.execute(
            "SELECT id FROM entries WHERE pocket_id = ? AND timestamp = ? AND amount = ? AND title = ?",
            (pocket_id, entry["timestamp"], entry["amount"], entry["title"])
        ).fetchone()
        
        if existing:
            duplicates += 1
            continue
        
        conn.execute(
            """INSERT INTO entries 
            (pocket_id, amount, title, memo, timestamp, status, entry_type, card_last_four, note, import_batch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pocket_id, entry["amount"], entry["title"], entry["memo"],
             entry["timestamp"], entry["status"], entry["entry_type"],
             entry["card_last_four"], entry["note"], batch_id)
        )
        imported += 1
    
    conn.execute(
        "INSERT INTO import_batches (id, row_count, new_pockets) VALUES (?, ?, ?)",
        (batch_id, imported + duplicates, new_pockets)
    )
    conn.commit()
    conn.close()
    
    return {
        "imported": imported,
        "duplicates": duplicates,
        "new_pockets": new_pockets,
        "unknown_pockets": list(unknown_pockets),
        "batch_id": batch_id,
    }
