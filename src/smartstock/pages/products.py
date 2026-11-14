"""Products & Inventory page (TASK-016, TASK-017, TASK-018).

Products & Inventory page: product listing with search and filters
(TASK-016), product add/edit forms and soft-delete removal (TASK-017),
and stock adjustment/correction operations (TASK-018).

Data always comes from the application services — the page contains no
SQL and no business rules, only rendering, input collection, and error
display. Validation messages come from the services (ValueError) and
the database layer (DatabaseError) and are shown without changes.

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. The "All" filter sentinel and the stock-status
domain values stay language-independent — only their displayed labels
are translated — so filter comparisons work in both languages.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.domain.inventory import (
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
)
from smartstock.i18n import status_label, t
from smartstock.pages.ui import (
    empty_state,
    flash,
    page_header,
    section,
    show_flash,
)
from smartstock.services import inventory_service, product_service

ALL = "All"  # sentinel option value; displayed via "common.all"

# Semantic styling for the status column of the product table: a
# light background tint plus a matching bold text color, so In Stock /
# Low Stock / Out of Stock read as states at a glance (DEC-064, DEC-065).
STATUS_TINT = {
    STATUS_IN_STOCK: "#f0fdf4",  # green-50
    STATUS_LOW_STOCK: "#fff7ed",  # orange-50
    STATUS_OUT_OF_STOCK: "#fef2f2",  # red-50
}
STATUS_TEXT = {
    STATUS_IN_STOCK: "#16a34a",  # green-600
    STATUS_LOW_STOCK: "#ea580c",  # orange-600
    STATUS_OUT_OF_STOCK: "#dc2626",  # red-600
}
DEFAULT_TINT = "transparent"


def render() -> None:
    """Render the Products & Inventory page."""
    page_header(
        "inventory_2",
        t("products.title"),
        t("products.description"),
    )

    # Feedback messages survive the st.rerun() a successful action
    # triggers; inline st.error stays used for validation failures.
    show_flash()

    tab_list, tab_add, tab_edit, tab_stock = st.tabs(
        [
            t("products.tab_list"),
            t("products.tab_add"),
            t("products.tab_edit"),
            t("products.tab_stock"),
        ]
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
    try:
        overview = inventory_service.get_stock_overview()
    except DatabaseError as error:
        st.error(t("products.load_error", error=error))
        return

    if not overview:
        empty_state(
            t("products.no_products_title"),
            t("products.no_products_list_message"),
            icon="inventory_2",
        )
        return

    overview = _apply_filters(overview, len(overview))
    if not overview:
        st.warning(
            t("products.no_match_warning"),
            icon=":material/search_off:",
        )
        return

    _render_product_table(overview)


def _apply_filters(overview: list, total_products: int) -> list:
    """Search and filter widgets, returning the filtered rows."""
    search = st.text_input(
        t("products.search_label"),
        placeholder=t("products.search_placeholder"),
        help=t("products.search_help"),
    )
    left, right = st.columns(2)
    categories = sorted(
        {product["category"] for product in overview if product["category"]}
    )
    if any(not product["category"] for product in overview):
        categories.append("(no category)")

    def category_label(value: str) -> str:
        if value == ALL:
            return t("common.all")
        return (
            t("products.no_category")
            if value == "(no category)"
            else value
        )

    category = left.selectbox(
        t("products.filter_category"),
        [ALL] + categories,
        index=0,
        disabled=not categories,
        format_func=category_label,
        key="listing_category",
    )
    status = right.selectbox(
        t("products.filter_status"),
        [ALL, STATUS_IN_STOCK, STATUS_LOW_STOCK, STATUS_OUT_OF_STOCK],
        index=0,
        # Option values stay the domain constants so the comparison
        # below (and the pinned tests) are language-independent; only
        # the displayed label translates (DEC-066 sentinel pattern).
        format_func=lambda value: (
            t("common.all") if value == ALL else status_label(value)
        ),
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
        st.caption(
            t(
                "products.caption_showing",
                shown=len(rows),
                total=total_products,
            )
        )
    return rows


def _render_product_table(overview: list) -> None:
    """Render the product list as the main content table."""
    import pandas as pd

    name_label = t("products.column_name")
    stock_label = t("products.column_stock")
    demand_label = t("products.column_avg_demand")
    status_column = t("products.column_status")
    rows = []
    for product in overview:
        rows.append(
            {
                name_label: product["name"],
                t("products.column_sku"): product["sku"],
                t("products.column_category"): product["category"] or "—",
                stock_label: product["current_stock"],
                t("products.column_lead_time"): product["lead_time_days"],
                t("products.column_safety_stock"): product["safety_stock"],
                t("products.column_reorder_point"): product["reorder_point"],
                demand_label: product["average_daily_demand"],
                # Display value translates; the raw domain value stays
                # in the data for filters, warnings, and exports.
                status_column: status_label(product["stock_status"]),
            }
        )

    frame = pd.DataFrame(rows)
    # Tint the status cells with the approved state colors and show
    # them in their matching bold state color, so low and out-of-stock
    # rows stand out without any decorative styling (DEC-065). Cells
    # hold the translated status label (v1.1), so the tint/text maps
    # are keyed by the label in the active session language.
    tint_by_label = {
        status_label(value): color
        for value, color in STATUS_TINT.items()
    }
    text_by_label = {
        status_label(value): color
        for value, color in STATUS_TEXT.items()
    }
    style = frame.style.map(
        lambda status: (
            f"background-color: {tint_by_label.get(status, DEFAULT_TINT)}; "
            f"color: {text_by_label.get(status, 'inherit')}; "
            "font-weight: 700;"
        ),
        subset=[status_column],
    )
    st.dataframe(
        style,
        hide_index=True,
        width="stretch",
        column_config={
            name_label: st.column_config.TextColumn(name_label, width="medium"),
            stock_label: st.column_config.NumberColumn(stock_label),
            demand_label: st.column_config.NumberColumn(
                demand_label, format="%.2f"
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
            t(
                "products.low_stock_warning",
                count=len(low_stock),
                names=names,
            ),
            icon=":material/warning:",
        )


# ---------------------------------------------------------------------------
# TASK-017: product forms
# ---------------------------------------------------------------------------

def _render_add_form() -> None:
    section("add_circle", t("products.add_section"))
    st.caption(t("products.add_caption"))
    with st.form("add_product_form", clear_on_submit=False):
        name = st.text_input(t("products.field_name"), key="add_name")
        sku = st.text_input(t("products.field_sku"), key="add_sku")
        category = st.text_input(
            t("products.field_category"), key="add_category"
        )
        left, middle, right = st.columns(3)
        initial_stock = left.number_input(
            t("products.field_initial_stock"),
            min_value=0, value=0, step=1, key="add_stock",
        )
        lead_time_days = middle.number_input(
            t("products.field_lead_time"),
            min_value=0, value=3, step=1, key="add_lead",
        )
        safety_stock = right.number_input(
            t("products.field_safety_stock"),
            min_value=0, value=0, step=1, key="add_safety",
        )
        submitted = st.form_submit_button(
            t("products.button_create"),
            type="primary",
            icon=":material/check:",
        )

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
        st.error(t("products.error_not_created", error=error))
        return
    flash(
        "success",
        t(
            "products.success_created",
            name=product["name"],
            sku=product["sku"],
            stock=product["current_stock"],
        ),
    )
    st.rerun()


def _render_edit_form() -> None:
    section("edit_square", t("products.edit_section"))
    # All products (including deactivated) so they can be reactivated.
    try:
        products = product_service.list_products(
            active_only=False,
        )
    except DatabaseError as error:
        st.error(t("products.load_error", error=error))
        return
    if not products:
        empty_state(
            t("products.no_products_edit_title"),
            t("products.no_products_first_message"),
            icon="edit_square",
        )
        return

    selected_sku = st.selectbox(
        t("products.select_to_edit"),
        options=[product["sku"] for product in products],
        format_func=lambda sku: _format_product_label(products, sku),
        key="edit_product",
    )
    product = _find_by_sku(products, selected_sku)

    with st.form(f"edit_form_{product['id']}", clear_on_submit=False):
        name = st.text_input(
            t("products.field_name"),
            value=product["name"],
            key=f"edit_name_{product['id']}",
        )
        sku = st.text_input(
            t("products.field_sku"),
            value=product["sku"],
            key=f"edit_sku_{product['id']}",
        )
        category = st.text_input(
            t("products.field_category"),
            value=product["category"],
            key=f"edit_category_{product['id']}",
        )
        left, right = st.columns(2)
        lead_time_days = left.number_input(
            t("products.field_lead_time"),
            min_value=0,
            value=product["lead_time_days"],
            step=1,
            key=f"edit_lead_{product['id']}",
        )
        safety_stock = right.number_input(
            t("products.field_safety_stock"),
            min_value=0,
            value=product["safety_stock"],
            step=1,
            key=f"edit_safety_{product['id']}",
        )
        # DEC-060: optional link to the imported dataset's item number,
        # used by the Demand Forecast page.
        dataset_item_id = st.number_input(
            t("products.field_dataset_item"),
            min_value=1,
            value=product["dataset_item_id"]
            if product["dataset_item_id"] is not None
            else 1,
            step=1,
            key=f"edit_item_{product['id']}",
        )
        link_item = st.checkbox(
            t("products.field_link_item"),
            value=product["dataset_item_id"] is not None,
            key=f"edit_link_{product['id']}",
        )
        submitted = st.form_submit_button(
            t("products.button_save"),
            type="primary",
            icon=":material/save:",
        )

    if product["is_active"]:
        st.caption(t("products.caption_soft_delete"))
        confirm = st.checkbox(
            t("products.confirm_deactivate"),
            key=f"edit_confirm_{product['id']}",
        )
        if st.button(
            t("products.button_deactivate"),
            key=f"edit_discard_{product['id']}",
            icon=":material/inventory_2:",
        ):
            if not confirm:
                st.error(t("products.error_confirm_first"))
            else:
                try:
                    product_service.set_product_active(
                        product["id"], False,
                    )
                except (ValueError, DatabaseError) as error:
                    st.error(t("products.error_not_deactivated", error=error))
                    return
                flash(
                    "success",
                    t("products.success_deactivated", name=product["name"]),
                )
                st.rerun()
    else:
        st.caption(t("products.caption_inactive"))
        if st.button(
            t("products.button_reactivate"),
            key=f"edit_reactivate_{product['id']}",
            icon=":material/unarchive:",
        ):
            try:
                product_service.set_product_active(
                    product["id"], True,
                )
            except (ValueError, DatabaseError) as error:
                st.error(t("products.error_not_reactivated", error=error))
                return
            flash(
                "success",
                t("products.success_reactivated", name=product["name"]),
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
            dataset_item_id=(
                int(dataset_item_id) if link_item else None
            ),
        )
    except (ValueError, DatabaseError) as error:
        st.error(t("products.error_not_saved", error=error))
        return
    flash(
        "success",
        t(
            "products.success_updated",
            name=updated["name"],
            sku=updated["sku"],
        ),
    )
    st.rerun()


def _format_product_label(products: list, sku: str) -> str:
    product = _find_by_sku(products, sku)
    return t(
        "products.product_label",
        name=product["name"],
        sku=product["sku"],
        flag="" if product["is_active"] else t("products.inactive_flag"),
    )


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
    section("package_2", t("products.stock_section"))
    st.caption(t("products.stock_caption"))
    try:
        products = product_service.list_products()
    except DatabaseError as error:
        st.error(t("products.load_error", error=error))
        return
    if not products:
        empty_state(
            t("products.no_products_title"),
            t("products.no_products_first_message"),
            icon="package_2",
        )
        return

    # The radio's sentinel values stay language-independent; only the
    # displayed labels are translated, so the branch below works in
    # both languages.
    _MODE_CHANGE = "add-or-remove-units"
    _MODE_EXACT = "set-exact-stock"
    mode = st.radio(
        t("products.operation_label"),
        [_MODE_CHANGE, _MODE_EXACT],
        format_func=lambda value: (
            t("products.operation_change")
            if value == _MODE_CHANGE
            else t("products.operation_exact")
        ),
        key="stock_mode",
    )
    selected_sku = st.selectbox(
        t("products.stock_filter_product"),
        options=[product["sku"] for product in products],
        format_func=lambda sku: _format_product_label(products, sku),
        key="stock_product",
    )
    product = _find_by_sku(products, selected_sku)
    st.metric(
        t("products.metric_current_stock"),
        product["current_stock"],
        icon=":material/package:",
        border=True,
    )

    if mode == _MODE_CHANGE:
        _render_adjust_by_change(product)
    else:
        _render_adjust_by_exact_level(product)


def _render_adjust_by_change(product: dict) -> None:
    change = st.number_input(
        t("products.field_change"),
        value=1,
        step=1,
        key=f"stock_change_{product['id']}",
    )
    if st.button(
        t("products.button_apply"),
        key=f"stock_apply_{product['id']}",
        icon=":material/sync:",
    ):
        try:
            new_stock = inventory_service.adjust_stock(
                product["id"], int(change),
            )
        except (ValueError, DatabaseError) as error:
            # Includes the DEC-034 negative-stock rejection.
            st.error(t("products.error_adjustment_rejected", error=error))
            return
        flash(
            "success",
            t(
                "products.success_adjusted",
                name=product["name"],
                stock=new_stock,
            ),
        )
        st.rerun()


def _render_adjust_by_exact_level(product: dict) -> None:
    st.warning(t("products.exact_warning"))
    exact = st.number_input(
        t("products.field_exact"),
        min_value=0,
        value=product["current_stock"],
        step=1,
        key=f"stock_exact_{product['id']}",
    )
    if st.button(
        t("products.button_set"),
        key=f"stock_set_{product['id']}",
        icon=":material/edit:",
    ):
        try:
            new_stock = inventory_service.set_stock_level(
                product["id"], int(exact),
            )
        except (ValueError, DatabaseError) as error:
            st.error(t("products.error_correction_rejected", error=error))
            return
        flash(
            "success",
            t(
                "products.success_set",
                stock=new_stock,
                name=product["name"],
            ),
        )
        st.rerun()
