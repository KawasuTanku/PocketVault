"""Settings screen — configure API tokens and credentials."""
import os

from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Static, Input, Button, Label
from textual.binding import Binding

from pocketvault.database import get_connection, get_env_path


CONFIG_KEYS = {
    "crew_bearer_token": "Crew Bearer Token",
    "monster_api_url": "Monster API URL",
    "monster_api_token": "Monster API Token",
    "robinhood_username": "Robinhood Username",
    "robinhood_password": "Robinhood Password",
    "robinhood_totp": "Robinhood TOTP (optional)",
}


def load_config(db_path: str) -> dict:
    """Load config from DB, fallback to environment/.env."""
    config = {}
    
    # First: load from DB
    conn = get_connection(db_path)
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    for row in rows:
        config[row["key"]] = row["value"]
    
    # Second: fill from environment if not in DB
    env_map = {
        "crew_bearer_token": "CREW_BEARER_TOKEN",
        "monster_api_url": "MONSTER_API_URL",
        "monster_api_token": "MONSTER_API_TOKEN",
        "robinhood_username": "ROBINHOOD_USERNAME",
        "robinhood_password": "ROBINHOOD_PASSWORD",
        "robinhood_totp": "ROBINHOOD_TOTP",
    }
    
    for cfg_key, env_key in env_map.items():
        if not config.get(cfg_key):
            val = os.environ.get(env_key, "")
            if val:
                config[cfg_key] = val
    
    # Third: try .env file
    env_path = get_env_path()
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    env_key, val = line.split("=", 1)
                    env_key = env_key.strip()
                    val = val.strip().strip('"').strip("'")
                    for cfg_key, ek in env_map.items():
                        if ek == env_key and not config.get(cfg_key):
                            config[cfg_key] = val
    
    return config


def save_config(db_path: str, config: dict):
    """Save config to DB."""
    conn = get_connection(db_path)
    for key, value in config.items():
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
    conn.commit()
    conn.close()


def write_env(config: dict):
    """Write config to .env file."""
    env_path = get_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing .env to preserve other keys
    existing = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    existing[key.strip()] = val.strip().strip('"').strip("'")

    # Map config keys to env var names
    env_map = {
        "crew_bearer_token": "CREW_BEARER_TOKEN",
        "monster_api_url": "MONSTER_API_URL",
        "monster_api_token": "MONSTER_API_TOKEN",
        "robinhood_username": "ROBINHOOD_USERNAME",
        "robinhood_password": "ROBINHOOD_PASSWORD",
        "robinhood_totp": "ROBINHOOD_TOTP",
    }

    for cfg_key, env_key in env_map.items():
        if cfg_key in config and config[cfg_key]:
            existing[env_key] = config[cfg_key]

    with open(env_path, "w") as f:
        for key, val in existing.items():
            f.write(f'{key}="{val}"\n')


class SettingsScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "save", "Save"),
    ]

    def __init__(self, db_path: str, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.inputs = {}
        self.status = {}

    def compose(self):
        with Container(id="settings-modal"):
            yield Label("Settings", id="settings-title")

            with Vertical(id="settings-form"):
                for key, label in CONFIG_KEYS.items():
                    yield Label(f"{label}:")
                    inp = Input(
                        placeholder=f"Enter {label.lower()}...",
                        id=f"input-{key}",
                        password="password" in key.lower() or "token" in key.lower(),
                    )
                    self.inputs[key] = inp
                    yield inp
                    status = Static("", id=f"status-{key}")
                    self.status[key] = status
                    yield status

            with Horizontal(id="settings-buttons"):
                yield Button("Test Crew", id="test-crew")
                yield Button("Test Monster", id="test-monster")
                yield Button("Test Robinhood", id="test-robinhood")

            with Horizontal(id="settings-actions"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self):
        """Load existing config into inputs."""
        config = load_config(self.db_path)
        for key, inp in self.inputs.items():
            if key in config and config[key]:
                inp.value = config[key]

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "test-crew":
            self._test_crew()
        elif event.button.id == "test-monster":
            self._test_monster()
        elif event.button.id == "test-robinhood":
            self._test_robinhood()

    def action_save(self):
        config = {}
        for key, inp in self.inputs.items():
            if inp.value:
                config[key] = inp.value

        save_config(self.db_path, config)
        write_env(config)
        self.notify("Settings saved!", timeout=2)
        self.dismiss()

    def action_cancel(self):
        self.dismiss()

    def _test_crew(self):
        token = self.inputs["crew_bearer_token"].value
        if not token:
            self.status["crew_bearer_token"].update("[red]No token[/red]")
            return
        try:
            from pocketvault.crew.api import fetch_accounts
            fetch_accounts(token=token)
            self.status["crew_bearer_token"].update("[green]Connected![/green]")
        except Exception as e:
            self.status["crew_bearer_token"].update(f"[red]Failed: {e}[/red]")

    def _test_monster(self):
        url = self.inputs["monster_api_url"].value
        token = self.inputs["monster_api_token"].value
        if not url or not token:
            self.status["monster_api_token"].update("[red]Need URL + token[/red]")
            return
        try:
            from pocketvault.monster.api import monster_get
            old_url = os.environ.get("MONSTER_API_URL", "")
            old_token = os.environ.get("MONSTER_API_TOKEN", "")
            os.environ["MONSTER_API_URL"] = url
            os.environ["MONSTER_API_TOKEN"] = token
            try:
                result = monster_get("/api/stats")
            finally:
                if old_url:
                    os.environ["MONSTER_API_URL"] = old_url
                if old_token:
                    os.environ["MONSTER_API_TOKEN"] = old_token
            if result is not None:
                self.status["monster_api_token"].update("[green]Connected![/green]")
            else:
                self.status["monster_api_token"].update("[red]No response[/red]")
        except Exception as e:
            self.status["monster_api_token"].update(f"[red]Failed: {e}[/red]")

    def _test_robinhood(self):
        username = self.inputs["robinhood_username"].value
        password = self.inputs["robinhood_password"].value
        if not username or not password:
            self.status["robinhood_password"].update("[red]Need username + password[/red]")
            return
        try:
            from pocketvault.retirement.client import login, logout
            os.environ["ROBINHOOD_USERNAME"] = username
            os.environ["ROBINHOOD_PASSWORD"] = password
            totp = self.inputs["robinhood_totp"].value
            if totp:
                os.environ["ROBINHOOD_TOTP"] = totp
            if login():
                logout()
                self.status["robinhood_password"].update("[green]Connected![/green]")
            else:
                self.status["robinhood_password"].update("[red]Login failed[/red]")
        except Exception as e:
            self.status["robinhood_password"].update(f"[red]Failed: {e}[/red]")
