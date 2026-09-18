"""Retirement sync — fetch from Robinhood and store locally."""
import os
from datetime import datetime
from pocketvault.database import get_connection, get_db_path, init_db
from pocketvault.retirement.client import fetch_holdings


# Default targets if user hasn't configured
DEFAULT_TARGETS = {
    "VTI": {"target_pct": 80.0, "asset_class": "US Stock"},
    "SCHH": {"target_pct": 10.0, "asset_class": "REIT"},
    "BND": {"target_pct": 10.0, "asset_class": "Bond"},
}


def sync_retirement(db_path=None) -> dict:
    """Fetch retirement holdings and store to local DB."""
    if db_path is None:
        db_path = get_db_path()

    init_db(db_path)
    conn = get_connection(db_path)

    data = fetch_holdings()

    if not data:
        conn.close()
        return {"holdings": 0, "total_value_cents": 0, "total_gain_loss_cents": 0}

    # Clear old holdings
    conn.execute("DELETE FROM retirement_holdings")

    combined = data.get("combined", [])
    for h in combined:
        conn.execute("""
            INSERT INTO retirement_holdings (symbol, name, quantity, average_cost_cents,
                current_price_cents, current_value_cents, gain_loss_cents, asset_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            h["symbol"],
            h["name"],
            h["quantity"],
            int(round(h["average_cost"] * 100)),
            int(round(h["current_price"] * 100)),
            int(round(h["current_value"] * 100)),
            int(round(h["gain_loss"] * 100)),
            _classify_asset(h["symbol"]),
        ))

    # Seed default targets if empty
    target_count = conn.execute("SELECT COUNT(*) FROM retirement_targets").fetchone()[0]
    if target_count == 0:
        for sym, info in DEFAULT_TARGETS.items():
            conn.execute(
                "INSERT OR IGNORE INTO retirement_targets (symbol, target_pct, asset_class) VALUES (?, ?, ?)",
                (sym, info["target_pct"], info["asset_class"])
            )

    conn.commit()
    conn.close()

    return {
        "holdings": len(combined),
        "total_value_cents": int(round(data.get("total_value", 0) * 100)),
        "total_gain_loss_cents": int(round(data.get("total_gain_loss", 0) * 100)),
    }


def _classify_asset(symbol: str) -> str:
    """Classify symbol into asset class."""
    stock_etfs = {"VTI", "VOO", "SPY", "QQQ", "IWM", "VT", "VXUS"}
    reit_etfs = {"SCHH", "VNQ", "VNQI", "REET"}
    bond_etfs = {"BND", "AGG", "TLT", "IEF", "SHY", "LQD", "VTEB"}

    if symbol in stock_etfs:
        return "US Stock"
    if symbol in reit_etfs:
        return "REIT"
    if symbol in bond_etfs:
        return "Bond"
    return "Other"
