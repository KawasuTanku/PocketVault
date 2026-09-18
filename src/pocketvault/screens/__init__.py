from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Static, DataTable, Header, Footer
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget
from pocketvault.monster.queries import get_latest_snapshot, get_monster_products

class Dashboard(Screen):
    BINDINGS = [
        ("s", "sync_all", "Sync All"),
        ("c", "sync_crew", "Sync Crew"),
        ("m", "sync_monster", "Sync Monster"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, db_path, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path

    def compose(self):
        yield Header()
        with Container(id="dashboard"):
            yield Static(id="crew-summary", classes="summary")
            yield DataTable(id="pockets-table")
            yield Static(id="monster-summary", classes="summary")
            yield DataTable(id="monster-table")
        yield Footer()

    def on_mount(self):
        self.refresh_data()

    def refresh_data(self):
        pockets = get_pocket_balances(self.db_path)
        total_cash = sum((p.get("balance_cents", 0) or 0) / 100.0 for p in pockets if p["active"])
        ready = get_ready_to_budget(self.db_path)

        crew_summ = self.query_one("#crew-summary", Static)
        crew_summ.update(f"Cash Pockets  |  Ready to Budget: ${ready:,.2f}  |  Total: ${total_cash:,.2f}")

        pt = self.query_one("#pockets-table", DataTable)
        pt.clear()
        pt.add_columns("Pocket", "Balance", "Goal", "Progress")
        for p in pockets:
            if not p["active"]:
                continue
            bal = (p.get("balance_cents") or 0) / 100
            goal_cents = p.get("goal_cents") or 0
            goal_str = f"${goal_cents/100:,.2f}" if goal_cents > 0 else "—"
            prog = ""
            if goal_cents > 0:
                prog = f"{min(100, ((p.get('balance_cents') or 0) / goal_cents) * 100):.0f}%"
            pt.add_row(p["name"], f"${bal:,.2f}", goal_str, prog)

        snap = get_latest_snapshot(self.db_path)
        if snap:
            rev = snap["total_revenue_cents"] / 100
            exp = snap["total_expenses_cents"] / 100
            net = snap["net_profit_cents"] / 100
            sv = snap["total_stock_value_cents"] / 100
            low = snap["low_stock_count"]
            self.query_one("#monster-summary", Static).update(
                f"Monster P&L  |  Revenue: ${rev:,.2f}  |  Expenses: ${exp:,.2f}  |  Net: ${net:,.2f}  |  Stock: ${sv:,.2f}  |  Low Stock: {low}"
            )
        else:
            self.query_one("#monster-summary", Static).update("Monster P&L  —  press 'm' to sync")

        mt = self.query_one("#monster-table", DataTable)
        mt.clear()
        mt.add_columns("Product", "SKU", "Qty", "Cost", "Price", "Value", "Status")
        products = get_monster_products(self.db_path)
        products.sort(key=lambda p: (not p["low_stock"], p["name"]))
        for prod in products:
            mt.add_row(
                prod["name"],
                prod["sku"] or "",
                str(prod["qty_on_hand"]),
                f"${prod['unit_cost_cents']/100:,.2f}",
                f"${prod['unit_price_cents']/100:,.2f}",
                f"${prod['stock_value_cents']/100:,.2f}",
                "LOW" if prod["low_stock"] else "",
            )
        if not products:
            mt.add_row("No products — press 'm' to sync", "", "", "", "", "", "")

    def action_sync_all(self):
        self._sync_crew()
        self._sync_monster()
        self.refresh_data()

    def action_sync_crew(self):
        self._sync_crew()
        self.refresh_data()

    def action_sync_monster(self):
        self._sync_monster()
        self.refresh_data()

    def _sync_crew(self):
        try:
            from pocketvault.crew.sync import sync_crew_pockets
            result = sync_crew_pockets(self.db_path)
            self.notify(f"Crew: {result['new']} new, {result['updated']} updated", timeout=3)
        except Exception as e:
            self.notify(f"Crew sync failed: {e}", timeout=5, severity="error")

    def _sync_monster(self):
        try:
            from pocketvault.monster.sync import sync_monster
            result = sync_monster(self.db_path)
            self.notify(f"Monster: {result['products']} products, {result['low_stock']} low stock", timeout=3)
        except Exception as e:
            self.notify(f"Monster sync failed: {e}", timeout=5, severity="error")

    def action_refresh(self):
        self.refresh_data()

    def action_quit(self):
        self.app.exit()
