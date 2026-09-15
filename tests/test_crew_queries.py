import tempfile
import os
from pocketvault.database import init_db
from pocketvault.crew.importer import import_crew_entries
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget, get_total_crew_balance, get_entries_for_pocket

def test_get_pocket_balances():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Checking", "amount": 512.00, "timestamp": "2026-09-01T00:00:00", "title": "Paycheck", "memo": None, "status": "cleared", "entry_type": "check", "card_last_four": None, "note": None},
            {"pocket_name": "Autopilot Reserve", "amount": -109.00, "timestamp": "2026-09-01T00:00:00", "title": "Bills", "memo": None, "status": "cleared", "entry_type": "bill_subaccount", "card_last_four": None, "note": None},
        ]
        import_crew_entries(db_path, entries)
        
        balances = get_pocket_balances(db_path)
        assert len(balances) == 2
        checking = next(p for p in balances if p["name"] == "Checking")
        assert checking["balance"] == 512.00
    finally:
        os.unlink(db_path)

def test_get_ready_to_budget():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Autopilot Reserve", "amount": 127.32, "timestamp": "2026-09-01T00:00:00", "title": "Funding", "memo": None, "status": "cleared", "entry_type": "bill_subaccount", "card_last_four": None, "note": None},
        ]
        import_crew_entries(db_path, entries)
        
        ready = get_ready_to_budget(db_path)
        assert ready == 127.32
    finally:
        os.unlink(db_path)

def test_get_total_crew_balance():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        entries = [
            {"pocket_name": "Checking", "amount": 512.00, "timestamp": "2026-09-01T00:00:00", "title": "Paycheck", "memo": None, "status": "cleared", "entry_type": "check", "card_last_four": None, "note": None},
            {"pocket_name": "Save: Buffer", "amount": 1000.00, "timestamp": "2026-09-01T00:00:00", "title": "Overflow", "memo": None, "status": "cleared", "entry_type": "subaccount", "card_last_four": None, "note": None},
        ]
        import_crew_entries(db_path, entries)
        
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
