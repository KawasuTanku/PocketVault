import os
from textual.app import App
from textual.color import Color
from pocketvault.database import init_db, get_db_path, get_config_dir
from pocketvault.config import load_config

class PocketVaultApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #dashboard {
        height: 100%;
        padding: 1;
    }
    .summary {
        height: 3;
        background: $surface;
        color: $text;
        padding: 1;
        text-align: center;
    }
    .spacer {
        height: 1;
    }
    #pocket-table {
        height: 1fr;
    }
    #settings-modal {
        width: 80%;
        height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }
    #settings-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $accent;
    }
    #settings-form {
        height: 1fr;
        overflow-y: auto;
    }
    #settings-buttons {
        height: 3;
        content-align: center middle;
    }
    #settings-actions {
        height: 3;
        content-align: center middle;
    }
    """
    
    def __init__(self, db_path: str | None = None, **kwargs):
        super().__init__(**kwargs)
        init_db(db_path)
        self.db_path = db_path or get_db_path()
        self.config = load_config()
        self._apply_tankuos_theme()
    
    def _apply_tankuos_theme(self):
        """Apply theme from TankuOS env vars if present."""
        theme_name = os.environ.get("TANKUOS_THEME", "")
        if not theme_name:
            self.theme = "textual-dark"
            return

        try:
            if theme_name in self.available_themes:
                self.theme = theme_name
                return

            bg = os.environ.get("TANKUOS_THEME_BG", "")
            fg = os.environ.get("TANKUOS_THEME_FG", "")
            accent = os.environ.get("TANKUOS_THEME_ACCENT", "")

            if bg and fg and accent:
                from textual.theme import Theme
                panel = os.environ.get("TANKUOS_THEME_PANEL", bg)
                custom = Theme(
                    name=f"tankuos-{theme_name}",
                    primary=Color.from_rgb(*map(int, accent.split(","))),
                    background=Color.from_rgb(*map(int, bg.split(","))),
                    surface=Color.from_rgb(*map(int, panel.split(","))),
                    foreground=Color.from_rgb(*map(int, fg.split(","))),
                )
                self.register_theme(custom)
                self.theme = f"tankuos-{theme_name}"
            else:
                self.theme = "textual-dark"
        except Exception as e:
            import sys
            print(f"PocketVault theme error: {e}", file=sys.stderr)
            self.theme = "textual-dark"
    
    def on_mount(self):
        from pocketvault.screens import Dashboard
        self.push_screen(Dashboard(self.db_path))
