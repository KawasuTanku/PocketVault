"""Crew API sync — fetch pockets from Crew and sync to local DB."""
from pocketvault.database import get_connection, get_db_path, init_db
from pocketvault.crew.api import fetch_pockets


def sync_crew_pockets(db_path=None, token=None) -> dict:
    """Fetch pockets from Crew API and sync to local database."""
    if db_path is None:
        db_path = get_db_path()

    init_db(db_path)
    conn = get_connection(db_path)

    pockets = fetch_pockets(token)

    new_count = 0
    updated_count = 0

    existing_by_crew = {row["crew_id"]: row for row in conn.execute("SELECT * FROM pockets WHERE crew_id IS NOT NULL")}

    for pocket in pockets:
        crew_id = pocket["crew_id"]

        if crew_id in existing_by_crew:
            conn.execute("""
                UPDATE pockets SET 
                    name = ?, display_name = ?, account_id = ?, account_name = ?,
                    is_primary = ?, piggy_banked = ?, owner = ?, updated_at = datetime('now'),
                    balance_cents = ?, goal_cents = ?
                WHERE crew_id = ?
            """, (
                pocket["name"], pocket["display_name"], pocket["account_id"], pocket["account_name"],
                pocket["is_primary"], pocket["piggy_banked"], pocket["owner"], crew_id,
                pocket.get("balance"), pocket.get("goal")
            ))
            updated_count += 1
        else:
            conn.execute("""
                INSERT INTO pockets (crew_id, name, display_name, account_id, account_name,
                                     is_primary, piggy_banked, owner, balance_cents, goal_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                crew_id, pocket["name"], pocket["display_name"], pocket["account_id"], pocket["account_name"],
                pocket["is_primary"], pocket["piggy_banked"], pocket["owner"],
                pocket.get("balance"), pocket.get("goal")
            ))
            new_count += 1

    conn.commit()
    conn.close()

    return {
        "new": new_count,
        "updated": updated_count,
        "total": len(pockets),
    }
