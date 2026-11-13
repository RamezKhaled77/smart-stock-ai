"""Dashboard page (TASK-037, TASK-038, TASK-039).

Summarized view of the business situation per the approved DEC-061
metric set: inventory metrics, recent sales activity, top sellers,
forecast readiness, the sales-trend chart (TASK-038), and the
low-stock overview (TASK-039). All data comes from the dashboard
service — no SQL and no business rules here. Charting approach:
Streamlit's built-in ``st.line_chart`` (no extra dependency).

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language, so the approved pinned English strings are
unchanged in a fresh session.
"""

import pandas as pd
import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.pages.ui import (
    empty_state,
    page_header,
    section,
    show_flash,
)
from smartstock.services import dashboard_service

# Radio choices for the sales-trend window; the format labels need
# separate keys because Arabic handles the two plural forms differently.
_TREND_CHOICES = {7: "dashboard.last_7_days", 30: "dashboard.last_30_days"}
_TREND_SECTIONS = {
    7: "dashboard.trend_section_7",
    30: "dashboard.trend_section_30",
}


def render() -> None:
    """Render the Dashboard page."""
    page_header(
        "dashboard",
        t("dashboard.title"),
        t("dashboard.description"),
    )

    show_flash()

    trend_days = st.radio(
        t("dashboard.trend_window"),
        [7, 30],
        format_func=lambda days: t(_TREND_CHOICES[days]),
        index=0,
        horizontal=True,
        key="dashboard_trend_window",
    )

    try:
        data = dashboard_service.get_dashboard_data(trend_days=trend_days)
    except (ValueError, DatabaseError) as error:
        st.error(t("dashboard.load_error", error=error))
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
        t("dashboard.metric_active_products"),
        data["total_active_products"],
        icon=":material/inventory:",
        border=True,
    )
    top[1].metric(
        t("dashboard.metric_total_stock"),
        data["total_stock"],
        icon=":material/package:",
        border=True,
    )
    top[2].metric(
        t("dashboard.metric_needs_reorder"),
        data["products_needing_reorder"],
        help=t("dashboard.metric_needs_reorder_help"),
        icon=":material/priority_high:",
        border=True,
    )

    recent = data["recent_sales"]
    bottom = st.columns(3)
    bottom[0].metric(
        t("dashboard.metric_units_sold_7"),
        recent["units_sold"],
        icon=":material/shopping_cart:",
        border=True,
    )
    bottom[1].metric(
        t("dashboard.metric_sales_count_7"),
        recent["sale_count"],
        icon=":material/receipt:",
        border=True,
    )
    bottom[2].metric(
        t("dashboard.metric_top_seller"),
        data["top_products"][0]["units_sold"] if data["top_products"] else 0,
        help=t("dashboard.metric_top_seller_help"),
        icon=":material/trophy:",
        border=True,
    )


def _render_trend(data: dict, trend_days: int) -> None:
    """TASK-038: daily sales trend for the selected window."""
    with st.container(border=True):
        section("insights", t(_TREND_SECTIONS[trend_days]))
        if not data["trend"]:
            empty_state(
                t("dashboard.trend_empty_title"),
                t("dashboard.trend_empty_message"),
                icon="insights",
            )
            return
        frame = pd.DataFrame(
            {
                "date": sorted(data["trend"]),
                t("dashboard.column_units_sold"): [
                    data["trend"][day] for day in sorted(data["trend"])
                ],
            }
        )
        frame = frame.set_index(pd.to_datetime(frame["date"]))
        st.line_chart(
            frame[t("dashboard.column_units_sold")], width="stretch"
        )


def _render_top_products(data: dict) -> None:
    """DEC-061: best sellers of the last 30 days."""
    with st.container(border=True):
        section("trophy", t("dashboard.top_section"))
        if not data["top_products"]:
            empty_state(
                t("dashboard.top_empty_title"),
                t("dashboard.top_empty_message"),
                icon="trophy",
            )
            return
        units_label = t("dashboard.column_units_sold")
        table = pd.DataFrame(
            [
                {
                    t("dashboard.column_rank"): index + 1,
                    t("dashboard.column_name"): row["name"],
                    t("dashboard.column_sku"): row["sku"],
                    units_label: row["units_sold"],
                }
                for index, row in enumerate(data["top_products"])
            ]
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                units_label: st.column_config.NumberColumn(
                    units_label, format="%d",
                ),
            },
        )


def _render_low_stock(data: dict) -> None:
    """TASK-039: products meeting the approved low-stock conditions."""
    with st.container(border=True):
        section("warning", t("dashboard.low_section"))
        low_stock = data["low_stock"]
        if not low_stock:
            st.success(
                t("dashboard.low_all_ok"),
                icon=":material/check_circle:",
            )
            return
        st.warning(
            t("dashboard.low_warning", count=len(low_stock)),
            icon=":material/warning:",
        )
        demand_label = t("dashboard.column_avg_demand")
        table = pd.DataFrame(
            [
                {
                    t("dashboard.column_name"): row["product_name"],
                    t("dashboard.column_sku"): row["product_sku"],
                    t("dashboard.column_stock"): row["current_stock"],
                    demand_label: row["average_daily_demand"],
                    t("dashboard.column_reorder_point"): row[
                        "reorder_point"
                    ],
                    t("dashboard.column_suggested_order"): row[
                        "recommended_order_quantity"
                    ],
                }
                for row in low_stock
            ]
        )
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                demand_label: st.column_config.NumberColumn(
                    demand_label, format="%.2f",
                ),
            },
        )
        st.caption(t("dashboard.low_caption"))


def _render_forecast_readiness(data: dict) -> None:
    """DEC-061: forecast-readiness line (DEC-060 links)."""
    ready = data["forecast_ready"]
    with st.container(border=True):
        section("rocket_launch", t("dashboard.readiness_section"))
        if ready["total"] == 0:
            empty_state(
                t("dashboard.readiness_empty_title"),
                t("dashboard.readiness_empty_message"),
                icon="inventory_2",
            )
            return
        if ready["linked"] == 0:
            st.info(
                t("dashboard.readiness_none_linked"),
                icon=":material/link_off:",
            )
            return
        st.caption(
            t(
                "dashboard.readiness_caption",
                linked=ready["linked"],
                total=ready["total"],
            )
        )
