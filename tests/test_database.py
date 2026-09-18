import tempfile
import os
from pocketvault.database import init_db, get_connection

def test_init_db_creates_all_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        
        assert "pockets" in table_names
        assert "config" in table_names
        assert "pocket_aliases" in table_names
        assert "monster_products" in table_names
        assert "monster_snapshots" in table_names
        assert "retirement_holdings" in table_names
        assert "retirement_targets" in table_names
        
        views = conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
        view_names = {v[0] for v in views}
        assert "pocket_balances" in view_names
        assert "total_balance" in view_names
    finally:
        os.unlink(db_path)

def test_get_connection_returns_row_factory():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        row = conn.execute("SELECT 1 as test").fetchone()
        assert row["test"] == 1
        conn.close()
    finally:
        os.unlink(db_path)
