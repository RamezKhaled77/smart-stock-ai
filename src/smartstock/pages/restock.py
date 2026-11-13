"""Restocking Recommendations page (TASK-036).

Displays the advisory recommendations from the restock service
(TASK-035): which active products need attention, how much to order to
reach target stock, and why — with every supporting input (current
stock, average daily demand, lead time, safety stock, reorder point).

Per DEC-031 the page is purely informational: nothing is purchased and
no stock is changed here. Stock changes stay on the Products &
Inventory page; the decision to order stays with the user.

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. The per-product calculation walk-through
(``explanation``) and the unavailability reasons come from the restock
service and stay in English in v1, like other service-layer messages.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.pages.ui import (
    empty_state,
    formula_box,
    hero_stat,
    page_header,
    section,
    show_flash,
)
from smartstock.services import restock_service
from smartstock.utils.export import to_csv


def render() -> None:
    """Render the restocking recommendations page."""
    page_header(
        "package_2",
        t("restock.title"),
        t("restock.description"),
    )

    show_flash()

    try:
        recommendations = restock_service.get_restock_recommendations()
    except DatabaseError as error:
        st.error(t("restock.load_error", error=error))
        return

    if not recommendations:
        empty_state(
            t("restock.empty_title"),
            t("restock.empty_message"),
            icon="inventory_2",
        )
        return

    needs_attention = [
        row for row in recommendations if row["needs_reorder"]
    ]
    available = [
        row for row in recommendations if row["available"]
    ]
    unavailable = [
        row for row in recommendations if not row["available"]
    ]

    columns = st.columns(3)
    columns[0].metric(
        t("restock.metric_needs_reorder"),
        len(needs_attention),
        icon=":material/priority_high:",
        border=True,
    )
    columns[1].metric(
        t("restock.metric_available"),
        len(available),
        icon=":material/fact_check:",
        border=True,
    )
    columns[2].metric(
        t("restock.metric_no_data"),
        len(unavailable),
        help=t("restock.metric_no_data_help"),
        icon=":material/pending:",
        border=True,
    )

    if needs_attention:
        section("shopping_cart", t("restock.section_restock"))
        _render_recommendation_table(needs_attention)
        _render_explanations(needs_attention)
        _download_recommendations(needs_attention)
    else:
        st.success(
            t("restock.all_ok"),
            icon=":material/check_circle:",
        )

    if unavailable:
        section("info", t("restock.section_unavailable"))
        for row in unavailable:
            st.info(
                f"**{row['product_name']}** ({row['product_sku']}): "
                f"{row['unavailable_reason']}",
                icon=":material/info:",
            )


def _download_recommendations(rows: list) -> None:
    """CSV export of the restocking advice (TASK-049, DEC-063).

    Serializes the raw service rows so the file matches source data;
    unavailable rows carry their reason in ``unavailable_reason``.
    """
    columns = [
        "product_name", "product_sku", "current_stock",
        "average_daily_demand", "lead_time_days", "safety_stock",
        "reorder_point", "target_stock", "recommended_order_quantity",
        "stock_status",
    ]
    st.download_button(
        t("restock.export_button"),
        data=to_csv(rows, columns),
        file_name="restocking-recommendations.csv",
        mime="text/csv",
        key="export_recommendations",
        icon=":material/download:",
    )


def _render_recommendation_table(rows: list) -> None:
    """Main content table for products at or below their reorder point."""
    import pandas as pd

    name_label = t("restock.column_name")
    demand_label = t("restock.column_avg_demand")
    table = [
        {
            name_label: row["product_name"],
            t("restock.column_sku"): row["product_sku"],
            t("restock.column_stock"): row["current_stock"],
            demand_label: row["average_daily_demand"],
            t("restock.column_lead_time"): row["lead_time_days"],
            t("restock.column_safety_stock"): row["safety_stock"],
            t("restock.column_reorder_point"): row["reorder_point"],
            t("restock.column_target"): row["target_stock"],
            t("restock.column_order"): row["recommended_order_quantity"],
        }
        for row in rows
    ]
    st.dataframe(
        pd.DataFrame(table),
        hide_index=True,
        width="stretch",
        column_config={
            name_label: st.column_config.TextColumn(name_label, width="medium"),
            demand_label: st.column_config.NumberColumn(
                demand_label, format="%.2f",
            ),
        },
    )


def _render_explanations(rows: list) -> None:
    """One expander per product with the formula walk-through.

    Each expander leads with the suggested order as a hero stat
    (orange — the "needs attention" tone, DEC-065) and shows the
    calculation inputs in a monospace formula panel, so the number a
    decision hangs on and the arithmetic behind it are visually
    distinct from ordinary text.
    """
    for row in rows:
        with st.expander(
            t(
                "restock.expander_title",
                name=row["product_name"],
                sku=row["product_sku"],
                count=row["recommended_order_quantity"],
            ),
            icon=":material/lightbulb:",
        ):
            hero_stat(
                f"{row['recommended_order_quantity']}",
                t(
                    "restock.hero_label",
                    name=row["product_name"],
                    sku=row["product_sku"],
                ),
                tone="warn",
            )
            formula_box(row["explanation"])
