import tempfile
import os
from pocketvault.database import init_db, get_connection
from pocketvault.crew.importer import import_crew_entries

def test_import_creates_pockets_and_entries():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Spend: Food", "amount": -40.20, "timestamp": "2026-09-01T21:25:33", "title": "Walmart", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
            {"pocket_name": "Spend: Food", "amount": 150.00, "timestamp": "2026-09-02T13:07:52", "title": "Pocket plan", "memo": None, "status": "cleared", "entry_type": "bill_subaccount", "card_last_four": None, "note": None},
        ]
        result = import_crew_entries(db_path, entries)
        assert result["imported"] == 2
        assert result["new_pockets"] == 1
        
        conn = get_connection(db_path)
        pockets = conn.execute("SELECT name FROM pockets").fetchall()
        assert len(pockets) == 1
        assert pockets[0]["name"] == "Spend: Food"
        
        balance = conn.execute("SELECT COALESCE(SUM(amount), 0) as bal FROM entries WHERE pocket_id = 1").fetchone()["bal"]
        assert balance == 109.80
        conn.close()
    finally:
        os.unlink(db_path)

def test_import_duplicate_detection():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Spend: Food", "amount": -40.20, "timestamp": "2026-09-01T21:25:33", "title": "Walmart", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
        ]
        
        # First import
        result1 = import_crew_entries(db_path, entries)
        assert result1["imported"] == 1
        assert result1["duplicates"] == 0
        
        # Second import (same data)
        result2 = import_crew_entries(db_path, entries)
        assert result2["imported"] == 0
        assert result2["duplicates"] == 1
    finally:
        os.unlink(db_path)

def test_import_unknown_pockets():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Spend: Food", "amount": -40.20, "timestamp": "2026-09-01T21:25:33", "title": "Walmart", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
            {"pocket_name": "Spend: Fuel", "amount": -39.88, "timestamp": "2026-09-05T21:04:40", "title": "Gas Station", "memo": None, "status": "cleared", "entry_type": "card", "card_last_four": "1036", "note": None},
        ]
        result = import_crew_entries(db_path, entries)
        assert result["new_pockets"] == 2
    finally:
        os.unlink(db_path)
