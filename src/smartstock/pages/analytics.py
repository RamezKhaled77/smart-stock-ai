"""Sales Analytics page (TASK-041).

Date-range and product-filtered sales analytics per F-006 v1:
quantity metrics, daily trend, weekday pattern, month totals, and a
per-product ranking. All calculations come from the analytics service
— the page only collects input and renders (charts: built-in
Streamlit line/bar charts, no extra dependency). Read-only.

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. The "All products" filter sentinel stays a
language-independent constant — only its displayed label is
translated — so filter comparisons work in both languages.
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
from smartstock.services import analytics_service, product_service
from smartstock.utils.dates import utc_today_iso
from smartstock.utils.export import to_csv

ALL_PRODUCTS = "All products"  # sentinel; displayed via common.all_products

_WEEKDAY_KEYS = [
    "analytics.weekday_mon",
    "analytics.weekday_tue",
    "analytics.weekday_wed",
    "analytics.weekday_thu",
    "analytics.weekday_fri",
    "analytics.weekday_sat",
    "analytics.weekday_sun",
]


def render() -> None:
    """Render the Sales Analytics page."""
    page_header(
        "insights",
        t("analytics.title"),
        t("analytics.description"),
    )

    show_flash()

    products: list = []
    try:
        products = product_service.list_products()
    except DatabaseError as error:
        st.error(t("analytics.load_products_error", error=error))
        return
    if not products:
        empty_state(
            t("analytics.empty_title"),
            t("analytics.empty_message"),
            icon="insights",
        )
        return

    today = utc_today_iso()
    left, right = st.columns(2)
    start = left.date_input(
        t("analytics.filter_start"),
        value=dt_date_days_ago(29),
        min_value=None,
        max_value=today,
        key="analytics_start",
    )
    end = right.date_input(
        t("analytics.filter_end"),
        value=today,
        max_value=today,
        key="analytics_end",
    )

    def product_label(value) -> str:
        if value == ALL_PRODUCTS:
            return t("common.all_products")
        return f"{value['name']} ({value['sku']})"

    product = st.selectbox(
        t("analytics.filter_product"),
        [ALL_PRODUCTS] + products,
        format_func=product_label,
        key="analytics_product",
    )

    if isinstance(start, str) or isinstance(end, str):
        return  # date widget still settling
    _render_analytics(
        start.isoformat(), end.isoformat(),
        product_id=None if product == ALL_PRODUCTS else product["id"],
    )


def dt_date_days_ago(days: int):
    """Helper for the default range start (today − 29 days)."""
    import datetime as dt

    return dt.date.fromisoformat(utc_today_iso()) - dt.timedelta(days)


def _render_analytics(
    start: str, end: str, product_id: int | None
) -> None:
    """Fetch the analytics snapshot and render all sections."""
    try:
        data = analytics_service.get_sales_analytics(
            start, end, product_id=product_id
        )
    except ValueError as error:
        st.error(t("analytics.error_invalid_range", error=error))
        return
    except DatabaseError as error:
        st.error(t("analytics.load_error", error=error))
        return

    totals = data["totals"]
    columns = st.columns(4)
    columns[0].metric(
        t("analytics.metric_units_sold"),
        totals["units_sold"],
        icon=":material/shopping_cart:",
        border=True,
    )
    columns[1].metric(
        t("analytics.metric_sales_recorded"),
        totals["sale_count"],
        icon=":material/receipt:",
        border=True,
    )
    columns[2].metric(
        t("analytics.metric_avg_per_day"),
        totals["avg_units_per_day"],
        help=t("analytics.metric_avg_help", days=totals["days_in_range"]),
        icon=":material/calendar_month:",
        border=True,
    )
    columns[3].metric(
        t("analytics.metric_days_with_sales"),
        totals["days_with_sales"],
        help=t("analytics.metric_days_help", days=totals["days_in_range"]),
        icon=":material/event_available:",
        border=True,
    )

    _render_daily_trend(data)
    _render_weekday_pattern(data)
    _render_per_product(data)
    _render_performance(start, end, product_id)
    _render_monthly(data)


def _render_daily_trend(data: dict) -> None:
    section("trending_up", t("analytics.section_daily"))
    if not data["daily"]:
        empty_state(
            t("analytics.no_sales_title"),
            t("analytics.no_sales_daily_message"),
            icon="trending_up",
        )
        return
    units_label = t("analytics.column_units_sold")
    days = sorted(data["daily"])
    frame = pd.DataFrame(
        {
            "date": days,
            units_label: [data["daily"][day] for day in days],
        }
    ).set_index(pd.to_datetime(frame_index(days)))
    st.line_chart(frame[units_label], width="stretch")


def frame_index(days: list):
    """Datetime index helper for the trend frame."""
    import datetime as dt

    return [dt.date.fromisoformat(day) for day in days]


def _render_weekday_pattern(data: dict) -> None:
    section("calendar_month", t("analytics.section_weekday"))
    st.caption(t("analytics.weekday_caption"))
    pattern = data["weekday_pattern"]
    weekday_label = t("analytics.column_weekday")
    avg_label = t("analytics.column_avg_units")
    frame = pd.DataFrame(
        {
            weekday_label: [t(key) for key in _WEEKDAY_KEYS],
            avg_label: pattern,
        }
    )
    st.bar_chart(frame.set_index(weekday_label)[avg_label], width="stretch")


def _render_per_product(data: dict) -> None:
    section("leaderboard", t("analytics.section_per_product"))
    if not data["per_product"]:
        empty_state(
            t("analytics.no_sales_title"),
            t("analytics.no_sales_product_message"),
            icon="leaderboard",
        )
        return
    name_label = t("analytics.column_name")
    units_label = t("analytics.column_units_sold")
    table = pd.DataFrame(
        [
            {
                t("analytics.column_rank"): index + 1,
                name_label: row["name"],
                t("analytics.column_sku"): row["sku"],
                units_label: row["units_sold"],
                t("analytics.column_sales"): row["sale_count"],
                t("analytics.column_share"): (
                    f"{row['share_of_units'] * 100:.1f}%"
                ),
            }
            for index, row in enumerate(data["per_product"])
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")
    _download_button(
        t("analytics.export_per_product"),
        data["per_product"],
        ["name", "sku", "units_sold", "sale_count", "share_of_units"],
        "sales-by-product.csv",
        key="export_per_product",
    )


def _download_button(
    label: str, rows: list, columns: list, file_name: str, key: str
) -> None:
    """CSV download button for a service row list (TASK-049, DEC-063)."""
    csv_text = to_csv(rows, columns)
    st.download_button(
        label,
        data=csv_text,
        file_name=file_name,
        mime="text/csv",
        key=key,
        icon=":material/download:",
    )


def _render_performance(
    start: str, end: str, product_id: int | None
) -> None:
    """TASK-043: per-product performance insights (F-011)."""
    section("query_stats", t("analytics.section_performance"))
    try:
        rows = analytics_service.get_product_performance(
            start, end, product_id=product_id
        )
    except (ValueError, DatabaseError) as error:
        st.error(t("analytics.load_perf_error", error=error))
        return
    if not rows:
        empty_state(
            t("analytics.no_sales_title"),
            t("analytics.no_sales_perf_message"),
            icon="query_stats",
        )
        return
    name_label = t("analytics.column_name")
    units_label = t("analytics.column_units_sold")
    avg_label = t("analytics.column_avg_per_day")
    table = pd.DataFrame(
        [
            {
                name_label: row["name"],
                t("analytics.column_sku"): row["sku"],
                units_label: row["units_sold"],
                avg_label: row["avg_units_per_day"],
                t("analytics.column_first_sale"): row["first_sale"],
                t("analytics.column_last_sale"): row["last_sale"],
                t("analytics.column_trend"): row["trend"],
            }
            for row in rows
        ]
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            avg_label: st.column_config.NumberColumn(
                avg_label, format="%.3f",
            ),
        },
    )
    st.caption(t("analytics.trend_caption"))
    _download_button(
        t("analytics.export_performance"),
        rows,
        ["name", "sku", "units_sold", "avg_units_per_day",
         "first_sale", "last_sale", "trend"],
        "product-performance.csv",
        key="export_performance",
    )


def _render_monthly(data: dict) -> None:
    section("calendar_month", t("analytics.section_monthly"))
    if not data["monthly"]:
        return
    units_label = t("analytics.column_units_sold")
    months = sorted(data["monthly"])
    table = pd.DataFrame(
        {
            t("analytics.column_month"): months,
            units_label: [data["monthly"][month] for month in months],
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")
    monthly_rows = [
        {"month": month, "units_sold": data["monthly"][month]}
        for month in months
    ]
    _download_button(
        t("analytics.export_monthly"),
        monthly_rows,
        ["month", "units_sold"],
        "monthly-totals.csv",
        key="export_monthly",
    )
