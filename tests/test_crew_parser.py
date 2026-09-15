import pytest
from pocketvault.crew.parser import parse_crew_csv

def test_parse_basic_csv():
    csv_data = """Account Last Four,Account Name,Pocket,Title,Memo,Amount,Timestamp,Status,Type,Card Last Four,Note
XXXX,John,Spend: Food,Walmart,Test purchase,-40.20,2026-09-01T21:25:33Z,cleared,card,1036,"""
    
    entries = list(parse_crew_csv(csv_data))
    assert len(entries) == 1
    assert entries[0]["pocket_name"] == "Spend: Food"
    assert entries[0]["amount"] == -40.20
    assert entries[0]["title"] == "Walmart"

def test_parse_multiple_rows():
    csv_data = """Account Last Four,Account Name,Pocket,Title,Memo,Amount,Timestamp,Status,Type,Card Last Four,Note
XXXX,John,Spend: Food,Walmart,Groceries,-40.20,2026-09-01T21:25:33Z,cleared,card,1036,
XXXX,John,Spend: Fuel,Gas Station,Fill up,-39.88,2026-09-05T21:04:40Z,cleared,card,1036,
XXXX,John,Autopilot Reserve,Check deposit,,480.64,2026-09-02T13:07:25Z,cleared,check,,"""
    
    entries = list(parse_crew_csv(csv_data))
    assert len(entries) == 3
    assert entries[1]["pocket_name"] == "Spend: Fuel"
    assert entries[1]["amount"] == -39.88
    assert entries[2]["pocket_name"] == "Autopilot Reserve"
    assert entries[2]["amount"] == 480.64

def test_normalize_timestamp_with_timezone():
    csv_data = """Account Last Four,Account Name,Pocket,Title,Memo,Amount,Timestamp,Status,Type,Card Last Four,Note
XXXX,John,Spend: Food,Walmart,Test,-40.20,2026-09-01 08:56:25.848000Z,cleared,card,1036,"""
    
    entries = list(parse_crew_csv(csv_data))
    assert entries[0]["timestamp"] == "2026-09-01T08:56:25.848000"

def test_normalize_timestamp_with_offset():
    csv_data = """Account Last Four,Account Name,Pocket,Title,Memo,Amount,Timestamp,Status,Type,Card Last Four,Note
XXXX,John,Spend: Food,Walmart,Test,-40.20,2026-09-01 21:25:51.430089+00:00,cleared,subaccount,,"""
    
    entries = list(parse_crew_csv(csv_data))
    assert entries[0]["timestamp"] == "2026-09-01T21:25:51.430089"
