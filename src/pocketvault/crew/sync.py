"""Crew API sync — fetch pockets from Crew and sync to local DB."""
import json
from pocketvault.database import get_connection, get_db_path, init_db
from pocketvault.crew.api import fetch_pockets, fetch_autopilot_reserve


def sync_crew_pockets(db_path=None, token=None) -> dict:
    """Fetch pockets from Crew API and sync to local database.
    
    Returns summary of changes.
    """
    if db_path is None:
        db_path = get_db_path()
    
    init_db(db_path)
    conn = get_connection(db_path)
    
    # Fetch from Crew API
    pockets = fetch_pockets(token)
    autopilot = fetch_autopilot_reserve(token)
    
    # Track changes
    new_count = 0
    updated_count = 0
    
    # Get existing pocket crew_ids
    existing = {row["crew_id"]: row for row in conn.execute("SELECT * FROM pockets WHERE crew_id IS NOT NULL")}
    
    for pocket in pockets:
        crew_id = pocket["crew_id"]
        
        if crew_id in existing:
            # Update existing
            conn.execute("""
                UPDATE pockets SET 
                    name = ?, display_name = ?, account_id = ?, account_name = ?,
                    is_primary = ?, piggy_banked = ?, owner = ?, updated_at = datetime('now')
                WHERE crew_id = ?
            """, (
                pocket["name"], pocket["display_name"], pocket["account_id"], pocket["account_name"],
                pocket["is_primary"], pocket["piggy_banked"], pocket["owner"],
                crew_id
            ))
            updated_count += 1
        else:
            # Insert new
            conn.execute("""
                INSERT INTO pockets (crew_id, name, display_name, account_id, account_name,
                                     is_primary, piggy_banked, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                crew_id, pocket["name"], pocket["display_name"], pocket["account_id"], pocket["account_name"],
                pocket["is_primary"], pocket["piggy_banked"], pocket["owner"]
            ))
            new_count += 1
    
    conn.commit()
    conn.close()
    
    return {
        "new": new_count,
        "updated": updated_count,
        "total": len(pockets),
        "autopilot_reserve": autopilot,
    }
