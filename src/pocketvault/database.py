import os
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS pockets (
    id INTEGER PRIMARY KEY,
    crew_id TEXT UNIQUE,
    name TEXT NOT NULL,
    display_name TEXT,
    account_id TEXT,
    account_name TEXT,
    is_primary INTEGER DEFAULT 0,
    piggy_banked INTEGER DEFAULT 0,
    owner TEXT,
    balance_cents INTEGER DEFAULT 0,
    goal_cents INTEGER,
    active INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS pocket_aliases (
    old_name TEXT PRIMARY KEY,
    new_name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE VIEW IF NOT EXISTS pocket_balances AS
SELECT
    p.id, p.crew_id, p.name, p.display_name, p.active,
    p.account_name, p.is_primary, p.owner, p.balance_cents, p.goal_cents,
    p.sort_order
FROM pockets p
ORDER BY p.sort_order, p.name;

CREATE VIEW IF NOT EXISTS total_balance AS
SELECT COALESCE(SUM(balance_cents), 0) as total FROM pockets WHERE active = 1;
"""


def get_data_dir() -> Path:
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "pocketvault"
    return Path.home() / ".local" / "share" / "pocketvault"


def get_config_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "pocketvault"
    return Path.home() / ".config" / "pocketvault"


def get_db_path() -> Path:
    return get_data_dir() / "pocketvault.db"


def get_env_path() -> Path:
    return get_config_dir() / ".env"


def init_db(db_path: str | Path | None = None) -> None:
    if db_path is None:
        db_path = get_db_path()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
