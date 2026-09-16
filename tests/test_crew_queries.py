import tempfile
import os
from pocketvault.database import init_db, get_connection
from pocketvault.crew.importer import import_crew_entries
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget, get_total_crew_balance, get_entries_for_pocket

def test_get_pocket_balances():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-1", "Checking", 51200))
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-2", "Autopilot Reserve", 0))
        conn.commit()
        conn.close()
        
        balances = get_pocket_balances(db_path)
        assert len(balances) == 2
        checking = next(p for p in balances if p["name"] == "Checking")
        assert checking["balance_cents"] == 51200
    finally:
        os.unlink(db_path)

def test_get_ready_to_budget():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-3", "Autopilot Reserve", 12732))
        conn.commit()
        conn.close()
        
        ready = get_ready_to_budget(db_path)
        assert ready == 127.32
    finally:
        os.unlink(db_path)

def test_get_total_crew_balance():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-4", "Checking", 51200))
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-5", "Save: Buffer", 100000))
        conn.commit()
        conn.close()
        
        total = get_total_crew_balance(db_path)
        assert total == 1512.00
    finally:
        os.unlink(db_path)

def test_get_entries_for_pocket():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Spend: Food", "amount": -40.20, "timestamp": "2026-09-01T21:25:33", "title": "Walmart", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
            {"pocket_name": "Spend: Food", "amount": -19.20, "timestamp": "2026-09-04T15:19:44", "title": "Subway", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
        ]
        import_crew_entries(db_path, entries)
        
        food_entries = get_entries_for_pocket(db_path, "Spend: Food")
        assert len(food_entries) == 2
        assert food_entries[0]["title"] == "Subway"
        assert food_entries[1]["title"] == "Walmart"
    finally:
        os.unlink(db_path)
