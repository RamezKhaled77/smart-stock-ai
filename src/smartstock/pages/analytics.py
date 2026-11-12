"""Sales Analytics page (TASK-041).

Date-range and product-filtered sales analytics per F-006 v1:
quantity metrics, daily trend, weekday pattern, month totals, and a
per-product ranking. All calculations come from the analytics service
— the page only collects input and renders (charts: built-in
Streamlit line/bar charts, no extra dependency). Read-only.
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
from smartstock.services import analytics_service, product_service
from smartstock.utils.dates import utc_today_iso
from smartstock.utils.export import to_csv

ALL_PRODUCTS = "All products"


def render() -> None:
    """Render the Sales Analytics page."""
    page_header(
        "insights",
        "Sales Analytics",
        "Quantity-based sales insights (F-006): units sold and "
        "patterns. Revenue analytics need price data the application "
        "does not store.",
    )

    show_flash()

    products: list = []
    try:
        products = product_service.list_products()
    except DatabaseError as error:
        st.error(f"Could not load products: {error}")
        return
    if not products:
        empty_state(
            "No active products yet",
            "Add products on the Products & Inventory page, then "
            "record sales to see analytics.",
            icon="insights",
        )
        return

    today = utc_today_iso()
    left, right = st.columns(2)
    start = left.date_input(
        "Start date",
        value=dt_date_days_ago(29),
        min_value=None,
        max_value=today,
        key="analytics_start",
    )
    end = right.date_input(
        "End date", value=today, max_value=today, key="analytics_end"
    )

    product = st.selectbox(
        "Product filter",
        [ALL_PRODUCTS] + products,
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
        st.error(f"Invalid range: {error}")
        return
    except DatabaseError as error:
        st.error(f"Could not load analytics: {error}")
        return

    totals = data["totals"]
    columns = st.columns(4)
    columns[0].metric(
        "Units sold",
        totals["units_sold"],
        icon=":material/shopping_cart:",
        border=True,
    )
    columns[1].metric(
        "Sales recorded",
        totals["sale_count"],
        icon=":material/receipt:",
        border=True,
    )
    columns[2].metric(
        "Avg units/day",
        totals["avg_units_per_day"],
        help=f"Over all {totals['days_in_range']} days in the range "
        "(days without sales count as zero).",
        icon=":material/calendar_month:",
        border=True,
    )
    columns[3].metric(
        "Days with sales",
        totals["days_with_sales"],
        help=f"Out of {totals['days_in_range']} days in the range.",
        icon=":material/event_available:",
        border=True,
    )

    _render_daily_trend(data)
    _render_weekday_pattern(data)
    _render_per_product(data)
    _render_performance(start, end, product_id)
    _render_monthly(data)


def _render_daily_trend(data: dict) -> None:
    section("trending_up", "Daily units sold")
    if not data["daily"]:
        empty_state(
            "No sales in this range",
            "Record sales in this date range, or widen the range, to "
            "see the daily trend.",
            icon="trending_up",
        )
        return
    days = sorted(data["daily"])
    frame = pd.DataFrame(
        {
            "date": days,
            "Units sold": [data["daily"][day] for day in days],
        }
    ).set_index(pd.to_datetime(frame_index(days)))
    st.line_chart(frame["Units sold"], width="stretch")


def frame_index(days: list):
    """Datetime index helper for the trend frame."""
    import datetime as dt

    return [dt.date.fromisoformat(day) for day in days]


def _render_weekday_pattern(data: dict) -> None:
    section("calendar_month", "Weekday pattern")
    st.caption(
        "Average units sold per weekday over the whole range — days "
        "without sales count as zero."
    )
    pattern = data["weekday_pattern"]
    frame = pd.DataFrame(
        {
            "Weekday": [
                "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
            ],
            "Avg units": pattern,
        }
    )
    st.bar_chart(frame.set_index("Weekday")["Avg units"], width="stretch")


def _render_per_product(data: dict) -> None:
    section("leaderboard", "Sales by product")
    if not data["per_product"]:
        empty_state(
            "No sales in this range",
            "Record sales in this date range, or widen the range, to "
            "see the per-product ranking.",
            icon="leaderboard",
        )
        return
    table = pd.DataFrame(
        [
            {
                "Rank": index + 1,
                "Name": row["name"],
                "SKU": row["sku"],
                "Units sold": row["units_sold"],
                "Sales": row["sale_count"],
                "Share": f"{row['share_of_units'] * 100:.1f}%",
            }
            for index, row in enumerate(data["per_product"])
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")
    _download_button(
        "Export sales by product (CSV)",
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
    section("query_stats", "Product performance")
    try:
        rows = analytics_service.get_product_performance(
            start, end, product_id=product_id
        )
    except (ValueError, DatabaseError) as error:
        st.error(f"Could not load product performance: {error}")
        return
    if not rows:
        empty_state(
            "No sales in this range",
            "Record sales in this date range, or widen the range, to "
            "see per-product performance.",
            icon="query_stats",
        )
        return
    table = pd.DataFrame(
        [
            {
                "Name": row["name"],
                "SKU": row["sku"],
                "Units sold": row["units_sold"],
                "Avg units/day": row["avg_units_per_day"],
                "First sale": row["first_sale"],
                "Last sale": row["last_sale"],
                "Trend": row["trend"],
            }
            for row in rows
        ]
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Avg units/day": st.column_config.NumberColumn(
                "Avg units/day", format="%.3f",
            ),
        },
    )
    st.caption(
        "Trend compares the two calendar halves of the range (zeros "
        "count): Rising/Falling when the second half's daily average "
        "differs by ≥ 15%. Stock-warning frequency is not tracked in "
        "v1 — warnings are advisory snapshots, not logged events."
    )
    _download_button(
        "Export product performance (CSV)",
        rows,
        ["name", "sku", "units_sold", "avg_units_per_day",
         "first_sale", "last_sale", "trend"],
        "product-performance.csv",
        key="export_performance",
    )


def _render_monthly(data: dict) -> None:
    section("calendar_month", "Monthly totals")
    if not data["monthly"]:
        return
    months = sorted(data["monthly"])
    table = pd.DataFrame(
        {
            "Month": months,
            "Units sold": [data["monthly"][month] for month in months],
        }
    )
    st.dataframe(table, hide_index=True, width="stretch")
    monthly_rows = [
        {"month": month, "units_sold": data["monthly"][month]}
        for month in months
    ]
    _download_button(
        "Export monthly totals (CSV)",
        monthly_rows,
        ["month", "units_sold"],
        "monthly-totals.csv",
        key="export_monthly",
    )
