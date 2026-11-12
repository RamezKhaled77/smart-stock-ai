"""Dashboard page (TASK-037, TASK-038, TASK-039).

Summarized view of the business situation per the approved DEC-061
metric set: inventory metrics, recent sales activity, top sellers,
forecast readiness, the sales-trend chart (TASK-038), and the
low-stock overview (TASK-039). All data comes from the dashboard
service — no SQL and no business rules here. Charting approach:
Streamlit's built-in ``st.line_chart`` (no extra dependency).
"""

import pandas as pd
import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.pages.ui import (
    empty_state,
    page_header,
    section,
    show_flash,
)
from smartstock.services import dashboard_service


def render() -> None:
    """Render the Dashboard page."""
    page_header(
        "dashboard",
        "Dashboard",
        "Snapshot of the current inventory and sales situation. All "
        "windows end at today (UTC); restocking advice stays advisory "
        "(DEC-031).",
    )

    show_flash()

    trend_days = st.radio(
        "Sales trend window",
        [7, 30],
        format_func=lambda days: f"Last {days} days",
        index=0,
        horizontal=True,
        key="dashboard_trend_window",
    )

    try:
        data = dashboard_service.get_dashboard_data(trend_days=trend_days)
    except (ValueError, DatabaseError) as error:
        st.error(f"Could not load the dashboard: {error}")
        return

    _render_metrics(data)
    _render_trend(data, trend_days)
    _render_top_products(data)
    _render_low_stock(data)
    _render_forecast_readiness(data)


def _render_metrics(data: dict) -> None:
    """DEC-061 metric rows."""
    top = st.columns(3)
    top[0].metric(
        "Active products",
        data["total_active_products"],
        icon=":material/inventory:",
        border=True,
    )
    top[1].metric(
        "Total stock",
        data["total_stock"],
        icon=":material/package:",
        border=True,
    )
    top[2].metric(
        "Products needing reorder",
        data["products_needing_reorder"],
        help="Current stock at or below the reorder point (BR-022). "
        "Products without sales history are not counted yet.",
        icon=":material/priority_high:",
        border=True,
    )

    recent = data["recent_sales"]
    bottom = st.columns(3)
    bottom[0].metric(
        "Units sold (last 7 days)",
        recent["units_sold"],
        icon=":material/shopping_cart:",
        border=True,
    )
    bottom[1].metric(
        "Sales recorded (last 7 days)",
        recent["sale_count"],
        icon=":material/receipt:",
        border=True,
    )
    bottom[2].metric(
        "Top seller (30 days)",
        data["top_products"][0]["units_sold"] if data["top_products"] else 0,
        help="Units sold by the best-selling product of the last 30 "
        "days.",
        icon=":material/trophy:",
        border=True,
    )


def _render_trend(data: dict, trend_days: int) -> None:
    """TASK-038: daily sales trend for the selected window."""
    with st.container(border=True):
        section("insights", f"Sales trend — last {trend_days} days")
        if not data["trend"]:
            empty_state(
                "No sales in this window",
                "Record sales on the Sales Management page to see "
                "trends here.",
                icon="insights",
            )
            return
        frame = pd.DataFrame(
            {
                "date": sorted(data["trend"]),
                "Units sold": [
                    data["trend"][day] for day in sorted(data["trend"])
                ],
            }
        )
        frame = frame.set_index(pd.to_datetime(frame["date"]))
        st.line_chart(frame["Units sold"], width="stretch")


def _render_top_products(data: dict) -> None:
    """DEC-061: best sellers of the last 30 days."""
    with st.container(border=True):
        section("trophy", "Top sellers — last 30 days")
        if not data["top_products"]:
            empty_state(
                "No sales in the last 30 days",
                "Once sales are recorded, the best-selling products "
                "appear here.",
                icon="trophy",
            )
            return
        table = pd.DataFrame(
            [
                {
                    "Rank": index + 1,
                    "Name": row["name"],
                    "SKU": row["sku"],
                    "Units sold": row["units_sold"],
                }
                for index, row in enumerate(data["top_products"])
            ]
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "Units sold": st.column_config.NumberColumn(
                    "Units sold", format="%d",
                ),
            },
        )


def _render_low_stock(data: dict) -> None:
    """TASK-039: products meeting the approved low-stock conditions."""
    with st.container(border=True):
        section("warning", "Low-stock overview")
        low_stock = data["low_stock"]
        if not low_stock:
            st.success(
                "All products are In Stock.",
                icon=":material/check_circle:",
            )
            return
        st.warning(
            f"{len(low_stock)} product(s) are Out of Stock or Low Stock "
            "(current stock at or below the reorder point, BR-008).",
            icon=":material/warning:",
        )
        table = pd.DataFrame(
            [
                {
                    "Name": row["product_name"],
                    "SKU": row["product_sku"],
                    "Stock": row["current_stock"],
                    "Avg daily demand": row["average_daily_demand"],
                    "Reorder point": row["reorder_point"],
                    "Suggested order": row["recommended_order_quantity"],
                }
                for row in low_stock
            ]
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "Avg daily demand": st.column_config.NumberColumn(
                    "Avg daily demand", format="%.2f",
                ),
            },
        )
        st.caption(
            "Order suggestions are advisory (DEC-031). Review details "
            "on the Restocking Recommendations page."
        )


def _render_forecast_readiness(data: dict) -> None:
    """DEC-061: forecast-readiness line (DEC-060 links)."""
    ready = data["forecast_ready"]
    with st.container(border=True):
        section("rocket_launch", "Forecast readiness")
        if ready["total"] == 0:
            empty_state(
                "No active products yet",
                "Add products to start forecasting.",
                icon="inventory_2",
            )
            return
        if ready["linked"] == 0:
            st.info(
                "No product is linked to a dataset item yet, so "
                "nothing is forecastable. Link items on the Products "
                "& Inventory page (DEC-060), then open Demand Forecast.",
                icon=":material/link_off:",
            )
            return
        st.caption(
            f"{ready['linked']} of {ready['total']} active products "
            "are linked to a dataset item and can be forecast on the "
            "Demand Forecast page."
        )
