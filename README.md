# PocketVault

Unified personal finance TUI for [TankuOS](https://github.com/KawasuTanku/TankuOS). Tracks envelope budgeting (Crew), retirement accounts, and Monster P&L in one place.

## Features

- **Crew Import** — Parse Crew CSV exports, track pocket balances, detect unknown pockets
- **Monster Sync** — Pull P&L data from Monster API, track inventory and reorder alerts
- **Retirement** — Manage IRA/401k accounts, track holdings and allocation
- **Analysis** — Cross-domain net worth, natural language queries, reports

## Installation

```bash
pip install -e .
pocketvault
```

## TankuOS Integration

Add to `catalog.json`:
```json
{
  "name": "PocketVault",
  "repo": "github.com/KawasuTanku/PocketVault",
  "binary": "pocketvault",
  "description": "Unified personal finance TUI",
  "category": "Finance",
  "cli": false,
  "pty": true
}
```

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```

## License

MIT
