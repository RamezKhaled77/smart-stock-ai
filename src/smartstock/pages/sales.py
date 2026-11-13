"""Sales Management page (TASK-020, TASK-021).

Renders the approved sales workflows:

- "Record sale": manual sale entry through the sales service, which
  validates stock and reduces inventory atomically (DEC-035, BR-012).
- "Sales history": stored sales with product and date filters
  (TASK-021).

Only active products are sellable (DEC-050); the history filter also
lists inactive products so their preserved records stay reviewable
(DEC-048). The page contains no SQL and no business rules.

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. The "All" history-filter sentinel stays a language-
independent constant — only its displayed label is translated — so
the filter logic works in both languages.
"""

from datetime import date, timedelta

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.pages.ui import (
    empty_state,
    flash,
    page_header,
    section,
    show_flash,
)
from smartstock.services import product_service, sales_service
from smartstock.utils.dates import utc_today_iso

ALL = "All"  # sentinel option value; displayed via "common.all"


def _utc_today() -> date:
    """Today as UTC-aware applications validate it (see DEC-051)."""
    return date.fromisoformat(utc_today_iso())


def render() -> None:
    """Render the Sales Management page."""
    page_header(
        "receipt_long",
        t("sales.title"),
        t("sales.description"),
    )

    show_flash()

    tab_entry, tab_history = st.tabs(
        [t("sales.tab_record"), t("sales.tab_history")]
    )
    with tab_entry:
        _render_sale_form()
    with tab_history:
        _render_sales_history()


# ---------------------------------------------------------------------------
# TASK-020: manual sales entry
# ---------------------------------------------------------------------------

def _render_sale_form() -> None:
    section("shopping_cart", t("sales.record_section"))
    try:
        products = product_service.list_products()  # active only (DEC-050)
    except DatabaseError as error:
        st.error(t("sales.load_products_error", error=error))
        return
    if not products:
        empty_state(
            t("sales.no_products_title"),
            t("sales.no_products_entry_message"),
            icon="shopping_cart",
        )
        return

    selected_sku = st.selectbox(
        t("sales.field_product"),
        options=[product["sku"] for product in products],
        format_func=lambda sku: _sale_product_label(products, sku),
        key="sale_product",
    )
    product = _find_by_sku(products, selected_sku)

    st.metric(
        t("sales.metric_available_stock"),
        product["current_stock"],
        icon=":material/package:",
        border=True,
    )

    left, right = st.columns(2)
    quantity = left.number_input(
        t("sales.field_quantity"),
        min_value=1,
        value=1,
        step=1,
        key="sale_quantity",
    )
    sale_date = right.date_input(
        t("sales.field_sale_date"),
        value=_utc_today(),
        key="sale_date",
        help=t("sales.sale_date_help"),
    )

    if st.button(
        t("sales.button_record"),
        key="sale_submit",
        type="primary",
        icon=":material/check:",
    ):
        if isinstance(sale_date, str):  # no date chosen
            st.error(t("sales.error_date_required"))
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
            st.error(t("sales.error_not_recorded", error=error))
            return
        except DatabaseError as error:
            st.error(t("sales.error_not_recorded", error=error))
            return
        new_stock = product["current_stock"] - sale["quantity"]
        flash(
            "success",
            t(
                "sales.success_recorded",
                quantity=sale["quantity"],
                name=product["name"],
                date=sale["sale_date"],
                stock=new_stock,
            ),
        )
        st.rerun()


def _sale_product_label(products: list, sku: str) -> str:
    product = _find_by_sku(products, sku)
    return t(
        "sales.product_label",
        name=product["name"],
        sku=product["sku"],
        stock=product["current_stock"],
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
    section("history", t("sales.history_section"))
    # Products of any state: deactivated products keep their records
    # visible (DEC-048).
    try:
        products = product_service.list_products(active_only=False)
        sales = None  # populated below after validation
    except DatabaseError as error:
        st.error(t("sales.load_history_error", error=error))
        return
    if not products:
        empty_state(
            t("sales.no_products_title"),
            t("sales.no_products_history_message"),
            icon="history",
        )
        return

    product_names = {product["id"]: product for product in products}

    def history_label(sku: str) -> str:
        return t("common.all") if sku == ALL else _sale_product_label(
            products, sku
        )

    filtered = st.selectbox(
        t("sales.filter_product"),
        options=[ALL] + [product["sku"] for product in products],
        format_func=history_label,
        key="history_product",
    )
    left, middle, right = st.columns([1, 1, 1.4])
    all_time = left.checkbox(
        t("sales.filter_all_time"), value=True, key="history_all_time"
    )
    start_date = middle.date_input(
        t("sales.filter_from"),
        value=_utc_today() - timedelta(days=30),
        disabled=all_time,
        key="history_start",
    )
    end_date = right.date_input(
        t("sales.filter_to"),
        value=_utc_today(),
        disabled=all_time,
        key="history_end",
    )

    product_id = None if filtered == ALL else _find_by_sku(
        products, filtered
    )["id"]
    if all_time:
        start, end = None, None
    else:
        if start_date > end_date:
            st.warning(
                t("sales.warning_date_order"),
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
        st.error(t("sales.load_history_error", error=error))
        return
    total_units = sum(sale["quantity"] for sale in sales)
    if all_time:
        st.caption(
            t("sales.caption_all_time", count=len(sales), units=total_units)
        )
    else:
        st.caption(
            t(
                "sales.caption_between",
                count=len(sales),
                units=total_units,
                start=start,
                end=end,
            )
        )
    if not sales:
        if all_time and filtered == ALL:
            empty_state(
                t("sales.empty_no_sales_title"),
                t("sales.empty_no_sales_message"),
                icon="receipt",
            )
        else:
            st.info(
                t("sales.info_no_match"),
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
            else t("sales.unknown_product", id=sale["product_id"])
        )
        rows.append(
            {
                t("sales.column_product"): product_label,
                t("sales.column_quantity"): sale["quantity"],
                t("sales.column_sale_date"): sale["sale_date"],
                t("sales.column_recorded_at"): sale["created_at"],
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
    )
