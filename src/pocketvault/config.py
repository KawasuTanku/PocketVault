import os
from pathlib import Path
from dotenv import load_dotenv
from pocketvault.database import get_env_path, get_config_dir

def load_config() -> dict:
    """Load configuration from .env file and environment variables."""
    config = {}
    
    # Load from .env file if it exists
    env_path = get_env_path()
    if env_path.exists():
        load_dotenv(env_path)
    
    # Load from environment (TankuOS injects these)
    config["tankuos_theme"] = os.environ.get("TANKUOS_THEME", "")
    config["tankuos_theme_bg"] = os.environ.get("TANKUOS_THEME_BG", "")
    config["tankuos_theme_panel"] = os.environ.get("TANKUOS_THEME_PANEL", "")
    config["tankuos_theme_fg"] = os.environ.get("TANKUOS_THEME_FG", "")
    config["tankuos_theme_accent"] = os.environ.get("TANKUOS_THEME_ACCENT", "")
    config["tankuos_theme_secondary"] = os.environ.get("TANKUOS_THEME_SECONDARY", "")
    config["tankuos_theme_error"] = os.environ.get("TANKUOS_THEME_ERROR", "")
    
    # App-specific config
    config["monster_api_url"] = os.environ.get("MONSTER_API_URL", "")
    config["monster_api_token"] = os.environ.get("MONSTER_API_TOKEN", "")
    
    return config
