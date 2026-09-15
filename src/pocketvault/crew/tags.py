import json
import os
from pathlib import Path
from pocketvault.database import get_config_dir

DEFAULT_TAGS = {
    "system_pockets": ["checking", "autopilot reserve", "credit card reserve"],
    "prefixes": {
        "spend:": "Spending envelope",
        "save:": "Savings goal",
        "bill:": "Manual bill tracking",
        "outbox:": "Pending transfers",
        "reserve:": "System-managed",
        "invest:": "Investment pocket",
        "monster:": "Monster project tracking",
        "future:": "Future use pocket"
    }
}


def get_tags_path() -> Path:
    """Get pocket tags config file path."""
    return get_config_dir() / "pocket_tags.json"


def load_tags() -> dict:
    """Load pocket tags config, creating default if missing."""
    path = get_tags_path()
    if not path.exists():
        save_tags(DEFAULT_TAGS)
    with open(path) as f:
        return json.load(f)


def save_tags(tags: dict) -> None:
    """Save pocket tags config."""
    path = get_tags_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(tags, f, indent=2)


def is_pocket(name: str) -> bool:
    """Check if a name is a pocket based on tags config."""
    tags = load_tags()
    name_lower = name.lower().strip()
    
    # System pockets (exact match)
    if name_lower in [p.lower() for p in tags["system_pockets"]]:
        return True
    
    # Prefix match
    for prefix in tags["prefixes"]:
        if name_lower.startswith(prefix.lower()):
            return True
    
    return False
