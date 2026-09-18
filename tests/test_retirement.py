import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from pocketvault.database import init_db, get_connection
from pocketvault.retirement.sync import sync_retirement, _classify_asset
from pocketvault.retirement.queries import get_holdings, get_summary, get_targets


def test_classify_asset():
    assert _classify_asset("VTI") == "US Stock"
    assert _classify_asset("SCHH") == "REIT"
    assert _classify_asset("BND") == "Bond"
    assert _classify_asset("XYZ") == "Other"


def test_sync_retirement_no_robinhood():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        with patch("pocketvault.retirement.sync.fetch_holdings", return_value=None):
            result = sync_retirement(db_path)
        assert result["holdings"] == 0
        assert result["total_value_cents"] == 0
    finally:
        os.unlink(db_path)


def test_sync_retirement_with_data():
    mock_data = {
        "combined": [
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "quantity": 100.0,
                "average_cost": 220.00,
                "total_cost_basis": 22000.00,
                "current_price": 240.00,
                "current_value": 24000.00,
                "gain_loss": 2000.00,
            },
            {
                "symbol": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "quantity": 50.0,
                "average_cost": 75.00,
                "total_cost_basis": 3750.00,
                "current_price": 74.00,
                "current_value": 3700.00,
                "gain_loss": -50.00,
            },
        ],
        "total_value": 27700.00,
        "total_cost_basis": 25750.00,
        "total_gain_loss": 1950.00,
    }

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        with patch("pocketvault.retirement.sync.fetch_holdings", return_value=mock_data):
            result = sync_retirement(db_path)

        assert result["holdings"] == 2
        assert result["total_value_cents"] == 2770000
        assert result["total_gain_loss_cents"] == 195000

        # Verify holdings stored
        holdings = get_holdings(db_path)
        assert len(holdings) == 2
        vti = next(h for h in holdings if h["symbol"] == "VTI")
        assert vti["current_value_cents"] == 2400000
        assert vti["gain_loss_cents"] == 200000
        assert vti["asset_class"] == "US Stock"

        bnd = next(h for h in holdings if h["symbol"] == "BND")
        assert bnd["asset_class"] == "Bond"

        # Verify summary
        summary = get_summary(db_path)
        assert summary is not None
        assert summary["total_value_cents"] == 2770000
        assert summary["total_gain_loss_cents"] == 195000

        # Verify default targets seeded
        targets = get_targets(db_path)
        assert len(targets) == 3
        vti_target = next(t for t in targets if t["symbol"] == "VTI")
        assert vti_target["target_pct"] == 80.0

    finally:
        os.unlink(db_path)


def test_sync_retirement_replaces_old():
    mock_data_1 = {
        "combined": [{"symbol": "VTI", "name": "VTI", "quantity": 10, "average_cost": 100,
                       "total_cost_basis": 1000, "current_price": 110, "current_value": 1100, "gain_loss": 100}],
        "total_value": 1100, "total_cost_basis": 1000, "total_gain_loss": 100,
    }
    mock_data_2 = {
        "combined": [{"symbol": "BND", "name": "BND", "quantity": 20, "average_cost": 50,
                       "total_cost_basis": 1000, "current_price": 55, "current_value": 1100, "gain_loss": 100}],
        "total_value": 1100, "total_cost_basis": 1000, "total_gain_loss": 100,
    }

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        with patch("pocketvault.retirement.sync.fetch_holdings", return_value=mock_data_1):
            sync_retirement(db_path)
        holdings1 = get_holdings(db_path)
        assert len(holdings1) == 1
        assert holdings1[0]["symbol"] == "VTI"

        with patch("pocketvault.retirement.sync.fetch_holdings", return_value=mock_data_2):
            sync_retirement(db_path)
        holdings2 = get_holdings(db_path)
        assert len(holdings2) == 1
        assert holdings2[0]["symbol"] == "BND"
    finally:
        os.unlink(db_path)
