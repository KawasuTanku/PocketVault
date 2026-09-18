import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from pocketvault.database import init_db, get_connection
from pocketvault.monster.api import monster_get, get_monster_url, get_monster_token
from pocketvault.monster.sync import sync_monster
from pocketvault.monster.queries import get_latest_snapshot, get_monster_products


def test_get_monster_url_env(monkeypatch):
    monkeypatch.setenv("MONSTER_API_URL", "https://custom.monster")
    assert get_monster_url() == "https://custom.monster"


def test_get_monster_token_env(monkeypatch):
    monkeypatch.setenv("MONSTER_API_TOKEN", "test-token-123")
    assert get_monster_token() == "test-token-123"


def test_monster_get_success():
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"revenue": 100.0}).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    
    with patch("pocketvault.monster.api.get_monster_url", return_value="https://test.monster"), \
         patch("pocketvault.monster.api.get_monster_token", return_value="tok123"), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        result = monster_get("/api/report/summary")
    
    assert result == {"revenue": 100.0}


def test_monster_get_error():
    with patch("pocketvault.monster.api.get_monster_url", return_value="https://test.monster"), \
         patch("pocketvault.monster.api.get_monster_token", return_value="tok123"), \
         patch("urllib.request.urlopen", side_effect=Exception("timeout")):
        result = monster_get("/api/report/summary")
    
    assert result is None


def test_sync_monster():
    mock_products = [
        {
            "id": "p1",
            "name": "Monster Energy Original",
            "sku": "ME-001",
            "qtyOnHand": 24,
            "unitCostCents": 120,
            "unitPriceCents": 250,
            "stockValueCents": 2880,
            "discontinued": False,
            "needsReorder": False,
        },
        {
            "id": "p2",
            "name": "Monster Ultra",
            "sku": "ME-002",
            "qtyOnHand": 2,
            "unitCostCents": 130,
            "unitPriceCents": 260,
            "stockValueCents": 260,
            "discontinued": False,
            "needsReorder": True,
        },
    ]
    mock_stats = {"low_stock_count": 1, "total_stock_value": 3140}
    mock_summary = {"revenue": 5000.0, "expenses": 3200.0, "net": 1800.0}
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        with patch("pocketvault.monster.sync.fetch_inventory", return_value=mock_products), \
             patch("pocketvault.monster.sync.fetch_stats", return_value=mock_stats), \
             patch("pocketvault.monster.sync.fetch_summary", return_value=mock_summary):
            result = sync_monster(db_path)
        
        assert result["products"] == 2
        assert result["low_stock"] == 1
        assert result["net_profit_cents"] == 180000
        
        snap = get_latest_snapshot(db_path)
        assert snap is not None
        assert snap["total_revenue_cents"] == 500000
        assert snap["net_profit_cents"] == 180000
        assert snap["low_stock_count"] == 1
        
        products = get_monster_products(db_path)
        assert len(products) == 2
        low = get_monster_products(db_path, low_only=True)
        assert len(low) == 1
        assert low[0]["name"] == "Monster Ultra"
    finally:
        os.unlink(db_path)


def test_sync_monster_empty():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        with patch("pocketvault.monster.sync.fetch_inventory", return_value=None), \
             patch("pocketvault.monster.sync.fetch_stats", return_value=None), \
             patch("pocketvault.monster.sync.fetch_summary", return_value=None):
            result = sync_monster(db_path)
        
        assert result["products"] == 0
        snap = get_latest_snapshot(db_path)
        assert snap is not None
        assert snap["total_revenue_cents"] == 0
    finally:
        os.unlink(db_path)
