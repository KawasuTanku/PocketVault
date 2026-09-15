from textual.screen import Screen
from textual.containers import Container, Horizontal
from textual.widgets import Static, DataTable, Header, Button, Input, Label
from textual.binding import Binding
from pathlib import Path
from pocketvault.crew.queries import get_pocket_balances, get_ready_to_budget
from pocketvault.crew.parser import parse_crew_csv
from pocketvault.crew.importer import import_crew_entries

class Dashboard(Screen):
    BINDINGS = [
        ("i", "import_csv", "Import"),
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
        with Container(id="footer-bar"):
            yield Static("[i] Import  [r] Refresh  [q] Quit", id="help")
    
    def on_mount(self):
        self.refresh_data()
    
    def refresh_data(self):
        ready = get_ready_to_budget(self.db_path)
        pockets = get_pocket_balances(self.db_path)
        total = sum(p["balance"] for p in pockets if p["active"])
        
        summary = self.query_one("#summary", Static)
        summary.update(f"Ready to Budget: ${ready:,.2f}  |  Total Pockets: ${total:,.2f}")
        
        table = self.query_one("#pocket-table", DataTable)
        table.clear()
        table.add_columns("Pocket", "Balance")
        
        for p in pockets:
            if not p["active"]:
                continue
            table.add_row(p["name"], f"${p['balance']:,.2f}")
    
    def action_import_csv(self):
        self.app.push_screen(ImportScreen(self.db_path))
    
    def action_refresh(self):
        self.refresh_data()
    
    def action_quit(self):
        self.app.exit()


class ImportScreen(Screen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, db_path: str, **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self.parsed_entries = []
    
    def compose(self):
        yield Header()
        with Container(id="import-dialog"):
            yield Label("Import Crew CSV")
            yield Input(placeholder="Path to CSV file...", id="file-path")
            with Horizontal():
                yield Button("Preview", id="preview")
                yield Button("Import", id="import")
                yield Button("Cancel", id="cancel")
            yield DataTable(id="preview-table")
            yield Static(id="status")
    
    def on_button_pressed(self, event):
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "preview":
            self._preview()
        elif event.button.id == "import":
            self._import()
    
    def _preview(self):
        path = self.query_one("#file-path", Input).value
        if not Path(path).exists():
            self.query_one("#status", Static).update("File not found")
            return
        
        with open(path) as f:
            self.parsed_entries = list(parse_crew_csv(f.read()))
        
        table = self.query_one("#preview-table", DataTable)
        table.clear()
        table.add_columns("Pocket", "Amount", "Date", "Title")
        for e in self.parsed_entries[:50]:
            table.add_row(e["pocket_name"], f"${e['amount']:,.2f}", e["timestamp"][:10], e["title"] or "")
        
        self.query_one("#status", Static).update(f"{len(self.parsed_entries)} entries found.")
    
    def _import(self):
        if not self.parsed_entries:
            self._preview()
        
        result = import_crew_entries(self.db_path, self.parsed_entries)
        self.query_one("#status", Static).update(
            f"Imported {result['imported']} entries. {result['duplicates']} duplicates skipped. {result['new_pockets']} new pockets."
        )
    
    def dismiss(self):
        self.app.pop_screen()
    
    def action_cancel(self):
        self.dismiss()
