"""Sales Management page (TASK-020, TASK-021).

Renders the approved sales workflows:

- "Record sale": manual sale entry through the sales service, which
  validates stock and reduces inventory atomically (DEC-035, BR-012).
- "Sales history": stored sales with product and date filters
  (TASK-021).

Only active products are sellable (DEC-050); the history filter also
lists inactive products so their preserved records stay reviewable
(DEC-048). The page contains no SQL and no business rules.
"""

from datetime import date, timedelta

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.pages.ui import (
    empty_state,
    flash,
    page_header,
    section,
    show_flash,
)
from smartstock.services import product_service, sales_service
from smartstock.utils.dates import utc_today_iso

ALL = "All"


def _utc_today() -> date:
    """Today as UTC-aware applications validate it (see DEC-051)."""
    return date.fromisoformat(utc_today_iso())


def render() -> None:
    """Render the Sales Management page."""
    page_header(
        "receipt_long",
        "Sales Management",
        "Recorded sales reduce stock automatically. Recording is "
        "rejected when the requested quantity exceeds the available "
        "stock — the sale is not stored and the inventory stays "
        "unchanged.",
    )

    show_flash()

    tab_entry, tab_history = st.tabs(["Record sale", "Sales history"])
    with tab_entry:
        _render_sale_form()
    with tab_history:
        _render_sales_history()


# ---------------------------------------------------------------------------
# TASK-020: manual sales entry
# ---------------------------------------------------------------------------

def _render_sale_form() -> None:
    section("shopping_cart", "Record a sale")
    try:
        products = product_service.list_products()  # active only (DEC-050)
    except DatabaseError as error:
        st.error(f"Could not load products: {error}")
        return
    if not products:
        empty_state(
            "No products yet",
            "A sale needs a product. Add one on the Products & "
            "Inventory page first.",
            icon="shopping_cart",
        )
        return

    selected_sku = st.selectbox(
        "Product *",
        options=[product["sku"] for product in products],
        format_func=lambda sku: _sale_product_label(products, sku),
        key="sale_product",
    )
    product = _find_by_sku(products, selected_sku)

    st.metric(
        "Available stock",
        product["current_stock"],
        icon=":material/package:",
        border=True,
    )

    left, right = st.columns(2)
    quantity = left.number_input(
        "Quantity *",
        min_value=1,
        value=1,
        step=1,
        key="sale_quantity",
    )
    sale_date = right.date_input(
        "Sale date *",
        value=_utc_today(),
        key="sale_date",
        help="Backdated entries are allowed; future dates are rejected.",
    )

    if st.button(
        "Record sale",
        key="sale_submit",
        type="primary",
        icon=":material/check:",
    ):
        if isinstance(sale_date, str):  # no date chosen
            st.error("Sale date is required.")
            return
        try:
            sale = sales_service.record_sale(
                product["id"],
                int(quantity),
                sale_date.isoformat(),
            )
        except ValueError as error:
            # Includes the insufficient-stock rejection (DEC-035) with
            # requested/available quantities in the message.
            st.error(f"Sale not recorded: {error}")
            return
        except DatabaseError as error:
            st.error(f"Sale not recorded: {error}")
            return
        new_stock = product["current_stock"] - sale["quantity"]
        flash(
            "success",
            f"Recorded sale of {sale['quantity']} unit(s) of "
            f"'{product['name']}' on {sale['sale_date']}. "
            f"Remaining stock: {new_stock}.",
        )
        st.rerun()


def _sale_product_label(products: list, sku: str) -> str:
    product = _find_by_sku(products, sku)
    return (
        f"{product['name']} ({product['sku']}) — "
        f"{product['current_stock']} in stock"
    )


def _find_by_sku(products: list, sku: str) -> dict:
    matches = [product for product in products if product["sku"] == sku]
    if not matches:
        return products[0]
    return matches[0]


# ---------------------------------------------------------------------------
# TASK-021: sales history
# ---------------------------------------------------------------------------

def _render_sales_history() -> None:
    section("history", "Sales history")
    # Products of any state: deactivated products keep their records
    # visible (DEC-048).
    try:
        products = product_service.list_products(active_only=False)
        sales = None  # populated below after validation
    except DatabaseError as error:
        st.error(f"Could not load sales history: {error}")
        return
    if not products:
        empty_state(
            "No products yet",
            "Sales history appears here once products and sales exist.",
            icon="history",
        )
        return

    product_names = {product["id"]: product for product in products}

    filtered = st.selectbox(
        "Product",
        options=[ALL] + [product["sku"] for product in products],
        format_func=lambda sku: ALL if sku == ALL else (
            _sale_product_label(products, sku)
        ),
        key="history_product",
    )
    left, middle, right = st.columns([1, 1, 1.4])
    all_time = left.checkbox(
        "All time", value=True, key="history_all_time"
    )
    start_date = middle.date_input(
        "From",
        value=_utc_today() - timedelta(days=30),
        disabled=all_time,
        key="history_start",
    )
    end_date = right.date_input(
        "To", value=_utc_today(), disabled=all_time, key="history_end",
    )

    product_id = None if filtered == ALL else _find_by_sku(
        products, filtered
    )["id"]
    if all_time:
        start, end = None, None
    else:
        if start_date > end_date:
            st.warning(
                "The 'From' date is after the 'To' date.",
                icon=":material/event_busy:",
            )
            return
        start = start_date.isoformat()
        end = end_date.isoformat()

    try:
        sales = sales_service.list_sales(
            product_id=product_id, start_date=start, end_date=end
        )
    except DatabaseError as error:
        st.error(f"Could not load sales history: {error}")
        return
    total_units = sum(sale["quantity"] for sale in sales)
    st.caption(
        f"{len(sales)} sale(s), {total_units} unit(s) total"
        + (" (all time)" if all_time else f" between {start} and {end}")
        + "."
    )
    if not sales:
        if all_time and filtered == ALL:
            empty_state(
                "No sales recorded yet",
                "Record the first sale in the **Record sale** tab.",
                icon="receipt",
            )
        else:
            st.info(
                "No sales match the current filters.",
                icon=":material/filter_alt:",
            )
        return

    _render_sales_table(sales, product_names)


def _render_sales_table(
    sales: list, product_names: dict
) -> None:
    """Render sales rows with product labels (pandas.DataFrame)."""
    import pandas as pd

    rows = []
    for sale in sales:
        product = product_names.get(sale["product_id"])
        product_label = (
            f"{product['name']} ({product['sku']})"
            if product is not None
            else f"Product {sale['product_id']}"
        )
        rows.append(
            {
                "Product": product_label,
                "Quantity": sale["quantity"],
                "Sale date": sale["sale_date"],
                "Recorded at": sale["created_at"],
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
    )
