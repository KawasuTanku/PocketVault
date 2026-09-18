"""Monster sync — fetch data from Monster API and store locally."""
from pocketvault.database import get_connection, get_db_path, init_db
from pocketvault.monster.api import fetch_stats, fetch_inventory, fetch_summary


def sync_monster(db_path=None) -> dict:
    """Fetch Monster data and sync to local database."""
    if db_path is None:
        db_path = get_db_path()

    init_db(db_path)
    conn = get_connection(db_path)

    products = fetch_inventory()
    stats = fetch_stats()
    summary = fetch_summary()

    product_count = 0
    low_stock_count = 0
    stock_value_cents = 0

    if products:
        conn.execute("DELETE FROM monster_products")
        for p in products:
            pid = str(p.get("id", ""))
            qty = int(p.get("qty_on_hand", 0) or 0)
            cost_cents = int(round((p.get("unit_cost", 0) or 0) * 100))
            price_cents = int(round((p.get("unit_price", 0) or 0) * 100))
            sv_cents = int(round((p.get("stock_value", 0) or 0) * 100))
            discontinued = 1 if p.get("discontinued") else 0
            is_low = 1 if p.get("needs_reorder") else 0
            sku = p.get("sku", "") or ""
            name = p.get("name", pid)
            variant = p.get("variant", "") or ""

            if is_low:
                low_stock_count += 1
            stock_value_cents += sv_cents

            conn.execute("""
                INSERT INTO monster_products (id, name, variant, sku, qty_on_hand, unit_cost_cents,
                    unit_price_cents, discontinued, low_stock, stock_value_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, name, variant, sku, qty, cost_cents, price_cents, discontinued, is_low, sv_cents))
            product_count += 1

    # Snapshot P&L
    revenue_cents = 0
    expenses_cents = 0
    net_cents = 0
    if summary:
        revenue_cents = int((summary.get("revenue", 0) or 0) * 100)
        expenses_cents = int((summary.get("expenses", 0) or 0) * 100)
        net_cents = int((summary.get("net", 0) or 0) * 100)

    # Prefer stats endpoint for stock value if available
    if stats:
        total_sv = stats.get("total_stock_value")
        if total_sv is not None:
            stock_value_cents = int(total_sv * 100)
        low_from_stats = stats.get("low_stock_count")
        if low_from_stats is not None:
            low_stock_count = low_from_stats

    conn.execute("""
        INSERT INTO monster_snapshots (total_revenue_cents, total_expenses_cents,
            net_profit_cents, total_stock_value_cents, low_stock_count)
        VALUES (?, ?, ?, ?, ?)
    """, (revenue_cents, expenses_cents, net_cents, stock_value_cents, low_stock_count))

    conn.commit()
    conn.close()

    return {
        "products": product_count,
        "low_stock": low_stock_count,
        "stock_value_cents": stock_value_cents,
        "net_profit_cents": net_cents,
    }
