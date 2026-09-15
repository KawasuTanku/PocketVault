import csv
import io
from typing import Iterator

def parse_crew_csv(csv_text: str) -> Iterator[dict]:
    """Parse Crew CSV export into entry dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        yield {
            "pocket_name": row["Pocket"].strip(),
            "title": row.get("Title", "").strip() or None,
            "memo": row.get("Memo", "").strip() or None,
            "amount": float(row["Amount"]),
            "timestamp": _normalize_timestamp(row["Timestamp"]),
            "status": row.get("Status", "cleared").strip(),
            "entry_type": row.get("Type", "").strip() or None,
            "card_last_four": row.get("Card Last Four", "").strip() or None,
            "note": row.get("Note", "").strip() or None,
        }

def _normalize_timestamp(ts: str) -> str:
    """Convert Crew timestamp to ISO 8601."""
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1]
    if " " in ts:
        date_part, time_part = ts.split(" ", 1)
        ts = date_part + "T" + time_part
        if "+" in ts:
            ts = ts.split("+")[0]
    return ts
