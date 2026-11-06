"""Products & Inventory page (TASK-016).

Renders the approved product listing: product table with stock status
(BR-008), search, and filters. Data always comes from the application
services — the page contains no SQL and no business rules, only
rendering and user interaction.

Product forms (add/edit), stock adjustments, and removal actions are
added by TASK-017 and TASK-018 and are intentionally out of scope here.
"""

import streamlit as st

from smartstock.domain.inventory import (
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
)
from smartstock.services import inventory_service

# Marker chosen for quick visual scanning next to the status text.
STATUS_MARKERS = {
    STATUS_IN_STOCK: "🟢",
    STATUS_LOW_STOCK: "🟠",
    STATUS_OUT_OF_STOCK: "🔴",
}

ALL = "All"


def render() -> None:
    """Render the Products & Inventory page."""
    st.title("🏷️ Products & Inventory")
    st.caption(
        "Active products with their current stock and stock status "
        "(reorder point = average daily demand of the last 30 days × "
        "lead time + safety stock)."
    )

    overview = inventory_service.get_stock_overview()

    if not overview:
        st.info(
            "No products yet. Once the product form is added, create "
            "your first product here — this listing will update "
            "automatically."
        )
        return

    overview = _apply_filters(overview, len(overview))
    if not overview:
        st.warning("No products match the current search and filters.")
        return

    _render_product_table(overview)


def _apply_filters(overview: list, total_products: int) -> list:
    """Search and filter widgets, returning the filtered rows."""
    search = st.text_input(
        "Search products",
        placeholder="Type a product name or SKU…",
        help="Filters by product name or SKU, case-insensitive.",
    )
    left, right = st.columns(2)
    categories = sorted(
        {product["category"] for product in overview if product["category"]}
    )
    if any(not product["category"] for product in overview):
        categories.append("(no category)")
    category = left.selectbox(
        "Category", [ALL] + categories, index=0, disabled=not categories
    )
    status = right.selectbox(
        "Stock status",
        [ALL, STATUS_IN_STOCK, STATUS_LOW_STOCK, STATUS_OUT_OF_STOCK],
        index=0,
    )

    rows = overview
    if search:
        needle = search.casefold()
        rows = [
            product
            for product in rows
            if needle in product["name"].casefold()
            or needle in product["sku"].casefold()
        ]
    if category != ALL:
        wanted = "" if category == "(no category)" else category
        rows = [product for product in rows if product["category"] == wanted]
    if status != ALL:
        rows = [product for product in rows if product["stock_status"] == status]

    if len(rows) != total_products:
        st.caption(f"Showing {len(rows)} of {total_products} products.")
    return rows


def _render_product_table(overview: list) -> None:
    """Render the product list as the main content table."""
    import pandas as pd

    rows = []
    for product in overview:
        marker = STATUS_MARKERS.get(product["stock_status"], "")
        rows.append(
            {
                "Name": product["name"],
                "SKU": product["sku"],
                "Category": product["category"] or "—",
                "Stock": product["current_stock"],
                "Lead time (days)": product["lead_time_days"],
                "Safety stock": product["safety_stock"],
                "Reorder point": product["reorder_point"],
                "Avg daily demand": product["average_daily_demand"],
                "Status": f"{marker} {product['stock_status']}",
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Stock": st.column_config.NumberColumn("Stock"),
            "Avg daily demand": st.column_config.NumberColumn(
                "Avg daily demand", format="%.2f"
            ),
        },
    )
    low_stock = [
        product
        for product in overview
        if product["stock_status"] != STATUS_IN_STOCK
    ]
    if low_stock:
        st.warning(
            f"{len(low_stock)} product(s) are Out of Stock or Low Stock "
            "and may need restocking."
        )
