import os
import sqlite3
from pathlib import Path

SCHEMA = """
-- Crew tables
CREATE TABLE IF NOT EXISTS pockets (
    id INTEGER PRIMARY KEY,
    crew_id TEXT UNIQUE NOT NULL,           -- Stable subaccount UUID from Crew API
    name TEXT NOT NULL,                      -- User-facing pocket name (may have duplicates)
    display_name TEXT,                       -- System display name (e.g., "Autopilot Reserve" for reserve-linked)
    account_id TEXT,                         -- Parent account ID
    account_name TEXT,                       -- Parent account display name
    is_primary INTEGER DEFAULT 0,            -- Whether this is the primary pocket
    piggy_banked INTEGER DEFAULT 0,          -- Whether pocket is piggy banked
    owner TEXT,                              -- Owner display name
    active INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    pocket_id INTEGER NOT NULL REFERENCES pockets(id),
    paired_entry_id INTEGER REFERENCES entries(id),
    amount REAL NOT NULL,
    title TEXT,
    memo TEXT,
    timestamp TEXT NOT NULL,
    status TEXT DEFAULT 'cleared',
    entry_type TEXT,
    card_last_four TEXT,
    note TEXT,
    import_batch TEXT,
    UNIQUE(pocket_id, timestamp, amount, title)
);

CREATE TABLE IF NOT EXISTS import_batches (
    id TEXT PRIMARY KEY,
    imported_at TEXT DEFAULT (datetime('now')),
    row_count INTEGER,
    new_pockets INTEGER
);

CREATE TABLE IF NOT EXISTS pocket_aliases (
    old_name TEXT PRIMARY KEY,
    new_name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Crew views
CREATE VIEW IF NOT EXISTS pocket_balances AS
SELECT
    p.id, p.crew_id, p.name, p.display_name, p.active,
    p.account_name, p.is_primary, p.owner,
    COALESCE(SUM(e.amount), 0) AS balance,
    p.sort_order
FROM pockets p
LEFT JOIN entries e ON e.pocket_id = p.id
GROUP BY p.id
ORDER BY p.sort_order, p.name;

CREATE VIEW IF NOT EXISTS ready_to_budget AS
SELECT COALESCE(SUM(e.amount), 0) as balance
FROM pockets p
LEFT JOIN entries e ON e.pocket_id = p.id
WHERE p.name = 'Autopilot Reserve' AND p.active = 1
GROUP BY p.id;

CREATE VIEW IF NOT EXISTS total_crew_balance AS
SELECT COALESCE(SUM(balance), 0) as total FROM pocket_balances WHERE active = 1;
"""


def get_data_dir() -> Path:
    """Get data directory. Uses XDG_DATA_HOME if set (TankuOS), else default."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "pocketvault"
    return Path.home() / ".local" / "share" / "pocketvault"


def get_config_dir() -> Path:
    """Get config directory. Uses XDG_CONFIG_HOME if set (TankuOS), else default."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "pocketvault"
    return Path.home() / ".config" / "pocketvault"


def get_db_path() -> Path:
    """Get database file path."""
    return get_data_dir() / "pocketvault.db"


def get_env_path() -> Path:
    """Get .env file path."""
    return get_config_dir() / ".env"


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize database with full schema."""
    if db_path is None:
        db_path = get_db_path()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get a database connection with Row factory."""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
