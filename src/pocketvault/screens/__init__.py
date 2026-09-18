from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Static, DataTable, Header, Footer
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget

class Dashboard(Screen):
    BINDINGS = [
        ("s", "sync_crew", "Sync"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: str, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def compose(self):
        yield Header()
        with Container(id="dashboard"):
            yield Static(id="summary")
            yield DataTable(id="pocket-table")
        yield Footer()

    def on_mount(self):
        self.refresh_data()

    def refresh_data(self):
        ready = get_ready_to_budget(self.db_path)
        pockets = get_pocket_balances(self.db_path)
        total = sum((p.get("balance_cents", 0) or 0) / 100.0 for p in pockets if p["active"])

        summary = self.query_one("#summary", Static)
        summary.update(f"Ready to Budget: ${ready:,.2f}  |  Total Pockets: ${total:,.2f}")

        table = self.query_one("#pocket-table", DataTable)
        table.clear()
        table.add_columns("Pocket", "Balance", "Goal", "Progress")

        for p in pockets:
            if not p["active"]:
                continue
            bal_cents = p.get("balance_cents") or 0
            goal_cents = p.get("goal_cents") or 0
            bal_str = f"${bal_cents/100:,.2f}"
            goal_str = f"${goal_cents/100:,.2f}" if goal_cents > 0 else "—"
            progress = ""
            if goal_cents > 0:
                pct = min(100, (bal_cents / goal_cents) * 100)
                progress = f"{pct:.0f}%"
            table.add_row(p["name"], bal_str, goal_str, progress)

    def action_sync_crew(self):
        try:
            from pocketvault.crew.sync import sync_crew_pockets
            result = sync_crew_pockets(self.db_path)
            self.notify(f"Synced: {result['new']} new, {result['updated']} updated", timeout=3)
        except Exception as e:
            self.notify(f"Sync failed: {e}", timeout=5, severity="error")
        self.refresh_data()

    def action_refresh(self):
        self.refresh_data()

    def action_quit(self):
        self.app.exit()
