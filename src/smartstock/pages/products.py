"""Products & Inventory page (TASK-016, TASK-017, TASK-018).

Products & Inventory page: product listing with search and filters
(TASK-016), product add/edit forms and soft-delete removal (TASK-017),
and stock adjustment/correction operations (TASK-018).

Data always comes from the application services — the page contains no
SQL and no business rules, only rendering, input collection, and error
display. Validation messages come from the services (ValueError) and
the database layer (DatabaseError) and are shown without changes.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.domain.inventory import (
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
)
from smartstock.pages.ui import flash, show_flash
from smartstock.services import inventory_service, product_service

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

    # Feedback messages survive the st.rerun() a successful action
    # triggers; inline st.error stays used for validation failures.
    show_flash()

    tab_list, tab_add, tab_edit, tab_stock = st.tabs(
        ["📋 Product list", "➕ Add product", "✏️ Edit product",
         "📦 Adjust stock"]
    )
    with tab_list:
        _render_listing()
    with tab_add:
        _render_add_form()
    with tab_edit:
        _render_edit_form()
    with tab_stock:
        _render_stock_panel()


# ---------------------------------------------------------------------------
# TASK-016: listing
# ---------------------------------------------------------------------------

def _render_listing() -> None:
    overview = inventory_service.get_stock_overview()

    if not overview:
        st.info(
            "No products yet — create your first product in the "
            "**Add product** tab above."
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
        "Category", [ALL] + categories, index=0, disabled=not categories,
        key="listing_category",
    )
    status = right.selectbox(
        "Stock status",
        [ALL, STATUS_IN_STOCK, STATUS_LOW_STOCK, STATUS_OUT_OF_STOCK],
        index=0,
        key="listing_status",
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
        rows = [
            product for product in rows if product["stock_status"] == status
        ]

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
        width="stretch",
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
        names = ", ".join(
            f"{product['sku']} ({product['name']})"
            for product in low_stock
        )
        st.warning(
            f"{len(low_stock)} product(s) are Out of Stock or Low Stock "
            f"and may need restocking: {names}."
        )


# ---------------------------------------------------------------------------
# TASK-017: product forms
# ---------------------------------------------------------------------------

def _render_add_form() -> None:
    st.subheader("➕ Add product")
    st.caption(
        "Required: name and SKU. Lead time defaults to 3 days and "
        "safety stock to 0."
    )
    with st.form("add_product_form", clear_on_submit=False):
        name = st.text_input("Name *", key="add_name")
        sku = st.text_input("SKU *", key="add_sku")
        category = st.text_input(
            "Category (optional)", key="add_category"
        )
        left, middle, right = st.columns(3)
        initial_stock = left.number_input(
            "Initial stock", min_value=0, value=0, step=1, key="add_stock"
        )
        lead_time_days = middle.number_input(
            "Lead time (days)", min_value=0, value=3, step=1, key="add_lead"
        )
        safety_stock = right.number_input(
            "Safety stock", min_value=0, value=0, step=1, key="add_safety"
        )
        submitted = st.form_submit_button("Create product", type="primary")

    if not submitted:
        return
    try:
        product = product_service.create_product(
            name=name,
            sku=sku,
            category=category,
            initial_stock=int(initial_stock),
            lead_time_days=int(lead_time_days),
            safety_stock=int(safety_stock),
        )
    except (ValueError, DatabaseError) as error:
        st.error(f"Product not created: {error}")
        return
    flash(
        "success",
        f"Created '{product['name']}' ({product['sku']}) with "
        f"{product['current_stock']} units in stock.",
    )
    st.rerun()


def _render_edit_form() -> None:
    st.subheader("✏️ Edit product")
    # All products (including deactivated) so they can be reactivated.
    products = product_service.list_products(
        active_only=False,
    )
    if not products:
        st.info("No products to edit yet — add one in the Add tab.")
        return

    selected_sku = st.selectbox(
        "Product to edit",
        options=[product["sku"] for product in products],
        format_func=lambda sku: _format_product_label(products, sku),
        key="edit_product",
    )
    product = _find_by_sku(products, selected_sku)

    with st.form(f"edit_form_{product['id']}", clear_on_submit=False):
        name = st.text_input(
            "Name *", value=product["name"], key=f"edit_name_{product['id']}"
        )
        sku = st.text_input(
            "SKU *", value=product["sku"], key=f"edit_sku_{product['id']}"
        )
        category = st.text_input(
            "Category (optional)",
            value=product["category"],
            key=f"edit_category_{product['id']}",
        )
        left, right = st.columns(2)
        lead_time_days = left.number_input(
            "Lead time (days)",
            min_value=0,
            value=product["lead_time_days"],
            step=1,
            key=f"edit_lead_{product['id']}",
        )
        safety_stock = right.number_input(
            "Safety stock",
            min_value=0,
            value=product["safety_stock"],
            step=1,
            key=f"edit_safety_{product['id']}",
        )
        submitted = st.form_submit_button("Save changes", type="primary")

    if product["is_active"]:
        st.caption(
            "Removal deactivates the product (soft delete): history is "
            "kept and the action is reversible (DEC-048)."
        )
        confirm = st.checkbox(
            "I understand this deactivates the product",
            key=f"edit_confirm_{product['id']}",
        )
        if st.button("Deactivate product", key=f"edit_discard_{product['id']}"):
            if not confirm:
                st.error("Tick the confirmation box first.")
            else:
                product_service.set_product_active(
                    product["id"], False,
                )
                flash(
                    "success",
                    f"'{product['name']}' deactivated. Its sales history "
                    "is preserved; reactivation is possible.",
                )
                st.rerun()
    else:
        st.caption(
            "This product is currently deactivated (not listed, not "
            "sold). You can edit it or reactivate it below."
        )
        if st.button(
            "Reactivate product", key=f"edit_reactivate_{product['id']}"
        ):
            product_service.set_product_active(
                product["id"], True,
            )
            flash(
                "success", f"'{product['name']}' reactivated."
            )
            st.rerun()

    if not submitted:
        return
    try:
        updated = product_service.update_product(
            product["id"],
            name=name,
            sku=sku,
            category=category,
            lead_time_days=int(lead_time_days),
            safety_stock=int(safety_stock),
        )
    except (ValueError, DatabaseError) as error:
        st.error(f"Changes not saved: {error}")
        return
    flash(
        "success", f"Updated '{updated['name']}' ({updated['sku']})."
    )
    st.rerun()


def _format_product_label(products: list, sku: str) -> str:
    product = _find_by_sku(products, sku)
    flag = "" if product["is_active"] else " (inactive)"
    return f"{product['name']} ({product['sku']}){flag}"


def _find_by_sku(products: list, sku: str) -> dict:
    matches = [product for product in products if product["sku"] == sku]
    # The selectbox only ever passes back a listed SKU; a stable data
    # layer change mid-run is the only realistic miss. Fall back to the
    # first product to avoid a crash in that unlikely case.
    if not matches:
        return products[0]
    return matches[0]


# ---------------------------------------------------------------------------
# TASK-018: stock adjustments
# ---------------------------------------------------------------------------

def _render_stock_panel() -> None:
    st.subheader("📦 Adjust stock")
    st.caption(
        "**Add / remove units** for receipts, damage, and manual "
        "changes. **Set exact stock** is a correction that overwrites "
        "the stored value — use it to fix wrong data."
    )
    products = product_service.list_products()
    if not products:
        st.info("No products yet — add one in the Add tab.")
        return

    mode = st.radio(
        "Operation",
        ["Add or remove units", "Set exact stock (correction)"],
        key="stock_mode",
    )
    selected_sku = st.selectbox(
        "Product",
        options=[product["sku"] for product in products],
        format_func=lambda sku: _format_product_label(products, sku),
        key="stock_product",
    )
    product = _find_by_sku(products, selected_sku)
    st.metric(
        "Current stock",
        product["current_stock"],
        border=True,
    )

    if mode == "Add or remove units":
        _render_adjust_by_change(product)
    else:
        _render_adjust_by_exact_level(product)


def _render_adjust_by_change(product: dict) -> None:
    change = st.number_input(
        "Change (+ receive / − remove)",
        value=1,
        step=1,
        key=f"stock_change_{product['id']}",
    )
    if st.button(
        "Apply adjustment", key=f"stock_apply_{product['id']}"
    ):
        try:
            new_stock = inventory_service.adjust_stock(
                product["id"], int(change),
            )
        except (ValueError, DatabaseError) as error:
            # Includes the DEC-034 negative-stock rejection.
            st.error(f"Adjustment rejected: {error}")
            return
        flash(
            "success",
            f"Stock adjusted. '{product['name']}' now has "
            f"{new_stock} units.",
        )
        st.rerun()


def _render_adjust_by_exact_level(product: dict) -> None:
    st.warning(
        "Corrections overwrite the stored stock without a recorded "
        "explanation. Prefer 'Add or remove units' for regular changes."
    )
    exact = st.number_input(
        "Exact stock count",
        min_value=0,
        value=product["current_stock"],
        step=1,
        key=f"stock_exact_{product['id']}",
    )
    if st.button(
        "Set stock level", key=f"stock_set_{product['id']}"
    ):
        try:
            new_stock = inventory_service.set_stock_level(
                product["id"], int(exact),
            )
        except (ValueError, DatabaseError) as error:
            st.error(f"Correction rejected: {error}")
            return
        flash(
            "success",
            f"Stock set to {new_stock} units for '{product['name']}'.",
        )
        st.rerun()
