"""Retirement client — fetches holdings from Robinhood IRAs."""
import os
import sys
from typing import Optional
from datetime import datetime


def _robin_stocks():
    try:
        import robin_stocks.robinhood as r
        return r
    except ImportError:
        return None


def login() -> bool:
    r = _robin_stocks()
    if not r:
        return False

    username = os.environ.get("ROBINHOOD_USERNAME", "")
    password = os.environ.get("ROBINHOOD_PASSWORD", "")
    totp = os.environ.get("ROBINHOOD_TOTP", "")

    if not username or not password:
        return False

    try:
        if totp:
            r.login(username, password, mfa_code=totp)
        else:
            r.login(username, password)
        return True
    except Exception:
        return False


def logout():
    r = _robin_stocks()
    if r:
        try:
            r.logout()
        except Exception:
            pass


def fetch_holdings() -> Optional[dict]:
    """Fetch combined holdings from all Robinhood IRA accounts."""
    r = _robin_stocks()
    if not r:
        return None

    if not login():
        return None

    try:
        # Discover accounts
        import robin_stocks.robinhood.urls as urls
        import robin_stocks.robinhood.helper as helper

        all_accounts = helper.request_get(urls.account_profile_url(), dataType='pagination')
        cash_accounts = [a["account_number"] for a in (all_accounts or [])
                         if a.get("type", "").lower() == "cash"]

        # Fetch positions
        all_holdings = {}
        for acct_num in cash_accounts:
            positions = r.get_open_stock_positions(account_number=acct_num) or []
            for pos in positions:
                quantity = float(pos.get("quantity", 0))
                if quantity <= 0:
                    continue

                instrument_url = pos.get("instrument", "")
                symbol = "N/A"
                name = "N/A"

                try:
                    import requests
                    resp = requests.get(instrument_url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        inst = resp.json()
                        symbol = inst.get("symbol", "N/A")
                        name = inst.get("name", "N/A")
                except Exception:
                    pass

                if symbol not in all_holdings:
                    all_holdings[symbol] = {
                        "symbol": symbol,
                        "name": name,
                        "total_quantity": 0.0,
                        "total_cost_basis": 0.0,
                    }
                all_holdings[symbol]["total_quantity"] += quantity
                all_holdings[symbol]["total_cost_basis"] += quantity * float(pos.get("average_buy_price", 0))

        if not all_holdings:
            return None

        # Fetch current prices
        symbols = list(all_holdings.keys())
        prices = {}
        for sym in symbols:
            try:
                p = r.get_latest_price(sym)
                prices[sym] = float(p[0]) if p else 0.0
            except Exception:
                prices[sym] = 0.0

        # Build combined
        combined = []
        for symbol, data in all_holdings.items():
            qty = data["total_quantity"]
            avg_cost = data["total_cost_basis"] / qty if qty > 0 else 0
            current_price = prices.get(symbol, 0.0)
            current_value = qty * current_price
            gain_loss = current_value - data["total_cost_basis"]

            combined.append({
                "symbol": symbol,
                "name": data["name"],
                "quantity": round(qty, 4),
                "average_cost": round(avg_cost, 2),
                "total_cost_basis": round(data["total_cost_basis"], 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "gain_loss": round(gain_loss, 2),
            })

        combined.sort(key=lambda x: x["current_value"], reverse=True)

        return {
            "combined": combined,
            "total_value": round(sum(h["current_value"] for h in combined), 2),
            "total_cost_basis": round(sum(h["total_cost_basis"] for h in combined), 2),
            "total_gain_loss": round(sum(h["gain_loss"] for h in combined), 2),
        }
    finally:
        logout()
