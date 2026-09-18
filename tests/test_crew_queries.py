import tempfile
import os
from pocketvault.database import init_db, get_connection
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget, get_total_balance

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

def test_get_total_balance():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-4", "Checking", 51200))
        conn.execute("INSERT INTO pockets (crew_id, name, balance_cents) VALUES (?, ?, ?)", ("test-5", "Save: Buffer", 100000))
        conn.commit()
        conn.close()
        
        total = get_total_balance(db_path)
        assert total == 1512.00
    finally:
        os.unlink(db_path)
