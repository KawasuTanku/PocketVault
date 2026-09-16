import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from pocketvault.database import init_db, get_connection
from pocketvault.crew.api import fetch_pockets, fetch_autopilot_reserve, crew_query
from pocketvault.crew.sync import sync_crew_pockets


def test_fetch_pockets():
    """Test parsing pocket data from Crew API response."""
    mock_response = {
        "data": {
            "currentUser": {
                "accounts": [
                    {
                        "id": "acc1",
                        "displayName": "Checking",
                        "subaccounts": [
                            {
                                "id": "sub1",
                                "name": "Save: Cabin",
                                "displayName": "Save: Cabin",
                                "overallBalance": 57000,
                                "goal": 3000000,
                                "type": "SUBACCOUNT",
                                "isPrimary": False,
                                "piggyBanked": False,
                                "owner": {"displayName": "John"},
                                "account": {"id": "acc1", "displayName": "Checking"}
                            },
                            {
                                "id": "sub2",
                                "name": "Autopilot Reserve",
                                "displayName": "Autopilot Reserve",
                                "overallBalance": 0,
                                "goal": None,
                                "type": "SUBACCOUNT",
                                "isPrimary": False,
                                "piggyBanked": False,
                                "owner": {"displayName": "John"},
                                "account": {"id": "acc1", "displayName": "Checking"}
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    with patch("pocketvault.crew.api.crew_query", return_value=mock_response):
        pockets = fetch_pockets()
    
    assert len(pockets) == 2
    assert pockets[0]["crew_id"] == "sub1"
    assert pockets[0]["name"] == "Save: Cabin"
    assert pockets[0]["balance"] == 57000
    assert pockets[0]["goal"] == 3000000
    assert pockets[1]["name"] == "Autopilot Reserve"


def test_fetch_autopilot_reserve():
    """Test parsing autopilot reserve data."""
    mock_response = {
        "data": {
            "currentUser": {
                "accounts": [
                    {
                        "billReserve": {
                            "nextFundingDate": "2026-09-17",
                            "totalReservedAmount": 223605,
                            "estimatedNextFundingAmount": 51063,
                            "settings": {
                                "funding": {
                                    "subaccount": {"displayName": "Save: Buffer"}
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
    
    with patch("pocketvault.crew.api.crew_query", return_value=mock_response):
        reserve = fetch_autopilot_reserve()
    
    assert reserve is not None
    assert reserve["next_funding_date"] == "2026-09-17"
    assert reserve["total_reserved"] == 223605
    assert reserve["estimated_next_funding"] == 51063
    assert reserve["funding_subaccount"] == "Save: Buffer"


def test_sync_crew_pockets():
    """Test syncing pockets from Crew API to local DB."""
    mock_pockets = [
        {
            "crew_id": "sub1",
            "name": "Save: Cabin",
            "display_name": "Save: Cabin",
            "balance": 57000,
            "goal": 3000000,
            "type": "SUBACCOUNT",
            "is_primary": False,
            "piggy_banked": False,
            "owner": "John",
            "account_id": "acc1",
            "account_name": "Checking"
        }
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        init_db(db_path)
        
        with patch("pocketvault.crew.sync.fetch_pockets", return_value=mock_pockets), \
             patch("pocketvault.crew.sync.fetch_autopilot_reserve", return_value=None):
            result = sync_crew_pockets(db_path)
        
        assert result["new"] == 1
        assert result["updated"] == 0
        assert result["total"] == 1
        
        # Verify pocket was saved
        conn = get_connection(db_path)
        row = conn.execute("SELECT * FROM pockets WHERE crew_id = ?", ("sub1",)).fetchone()
        conn.close()
        
        assert row is not None
        assert row["name"] == "Save: Cabin"
        assert row["display_name"] == "Save: Cabin"
    finally:
        os.unlink(db_path)


def test_sync_updates_existing():
    """Test that sync updates existing pockets."""
    mock_pockets = [
        {
            "crew_id": "sub1",
            "name": "Save: Cabin Updated",
            "display_name": "Save: Cabin Updated",
            "balance": 60000,
            "goal": 3000000,
            "type": "SUBACCOUNT",
            "is_primary": False,
            "piggy_banked": False,
            "owner": "John",
            "account_id": "acc1",
            "account_name": "Checking"
        }
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        init_db(db_path)
        
        # First sync
        with patch("pocketvault.crew.sync.fetch_pockets", return_value=mock_pockets), \
             patch("pocketvault.crew.sync.fetch_autopilot_reserve", return_value=None):
            sync_crew_pockets(db_path)
        
        # Second sync (update)
        with patch("pocketvault.crew.sync.fetch_pockets", return_value=mock_pockets), \
             patch("pocketvault.crew.sync.fetch_autopilot_reserve", return_value=None):
            result = sync_crew_pockets(db_path)
        
        assert result["new"] == 0
        assert result["updated"] == 1
        
        conn = get_connection(db_path)
        row = conn.execute("SELECT * FROM pockets WHERE crew_id = ?", ("sub1",)).fetchone()
        conn.close()
        
        assert row["name"] == "Save: Cabin Updated"
    finally:
        os.unlink(db_path)
