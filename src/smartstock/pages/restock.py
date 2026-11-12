"""Restocking Recommendations page (TASK-036).

Displays the advisory recommendations from the restock service
(TASK-035): which active products need attention, how much to order to
reach target stock, and why — with every supporting input (current
stock, average daily demand, lead time, safety stock, reorder point).

Per DEC-031 the page is purely informational: nothing is purchased and
no stock is changed here. Stock changes stay on the Products &
Inventory page; the decision to order stays with the user.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.pages.ui import (
    empty_state,
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
        "Restocking Recommendations",
        "Advisory only — nothing is ordered automatically. Demand is "
        "the average daily sold quantity up to the most recent sale "
        "(days without sales count as zero).",
    )

    show_flash()

    try:
        recommendations = restock_service.get_restock_recommendations()
    except DatabaseError as error:
        st.error(f"Could not load recommendations: {error}")
        return

    if not recommendations:
        empty_state(
            "No active products yet",
            "Add products on the Products & Inventory page to receive "
            "restocking recommendations.",
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
        "Products needing reorder",
        len(needs_attention),
        icon=":material/priority_high:",
        border=True,
    )
    columns[1].metric(
        "Recommendations available",
        len(available),
        icon=":material/fact_check:",
        border=True,
    )
    columns[2].metric(
        "Without enough data",
        len(unavailable),
        help="No sales history or no stock level recorded yet.",
        icon=":material/pending:",
        border=True,
    )

    if needs_attention:
        section("shopping_cart", "Consider restocking")
        _render_recommendation_table(needs_attention)
        _render_explanations(needs_attention)
        _download_recommendations(needs_attention)
    else:
        st.success(
            "No product is at or below its reorder point right now.",
            icon=":material/check_circle:",
        )

    if unavailable:
        section("info", "Not available yet")
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
        "Export recommendations (CSV)",
        data=to_csv(rows, columns),
        file_name="restocking-recommendations.csv",
        mime="text/csv",
        key="export_recommendations",
        icon=":material/download:",
    )


def _render_recommendation_table(rows: list) -> None:
    """Main content table for products at or below their reorder point."""
    import pandas as pd

    table = [
        {
            "Name": row["product_name"],
            "SKU": row["product_sku"],
            "Stock": row["current_stock"],
            "Avg daily demand": row["average_daily_demand"],
            "Lead time (days)": row["lead_time_days"],
            "Safety stock": row["safety_stock"],
            "Reorder point": row["reorder_point"],
            "Target stock": row["target_stock"],
            "Order": row["recommended_order_quantity"],
        }
        for row in rows
    ]
    st.dataframe(
        pd.DataFrame(table),
        hide_index=True,
        width="stretch",
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Avg daily demand": st.column_config.NumberColumn(
                "Avg daily demand", format="%.2f",
            ),
        },
    )


def _render_explanations(rows: list) -> None:
    """One expander per product with the formula walk-through."""
    for row in rows:
        with st.expander(
            f"{row['product_name']} ({row['product_sku']}) — "
            f"order {row['recommended_order_quantity']} unit(s)",
            icon=":material/lightbulb:",
        ):
            st.markdown(row["explanation"])
