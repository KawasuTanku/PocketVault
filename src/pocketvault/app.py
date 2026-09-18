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
    #summary {
        height: 3;
        background: $surface;
        color: $text;
        padding: 1;
        text-align: center;
    }
    #pocket-table {
        height: 1fr;
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
            return
        
        # Build custom theme from TankuOS palette
        bg = os.environ.get("TANKUOS_THEME_BG", "")
        panel = os.environ.get("TANKUOS_THEME_PANEL", "")
        fg = os.environ.get("TANKUOS_THEME_FG", "")
        accent = os.environ.get("TANKUOS_THEME_ACCENT", "")
        secondary = os.environ.get("TANKUOS_THEME_SECONDARY", "")
        error = os.environ.get("TANKUOS_THEME_ERROR", "")
        
        theme = self.themes.get(theme_name)
        if theme:
            self.theme = theme_name
        elif bg and fg and accent:
            # Build a custom theme from the TankuOS palette
            from textual.theme import Theme
            custom = Theme(
                name=f"tankuos-{theme_name}",
                primary=Color.from_rgb(*map(int, accent.split(","))),
                background=Color.from_rgb(*map(int, bg.split(","))),
                surface=Color.from_rgb(*map(int, panel.split(","))) if panel else Color.from_rgb(*map(int, bg.split(","))),
                foreground=Color.from_rgb(*map(int, fg.split(","))),
            )
            self.register_theme(custom)
            self.theme = f"tankuos-{theme_name}"
    
    def on_mount(self):
        from pocketvault.screens import Dashboard
        self.push_screen(Dashboard(self.db_path))
