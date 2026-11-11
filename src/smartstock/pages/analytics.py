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
from smartstock.pages.ui import show_flash
from smartstock.services import analytics_service, product_service
from smartstock.utils.dates import utc_today_iso

ALL_PRODUCTS = "All products"


def render() -> None:
    """Render the Sales Analytics page."""
    st.title("📊 Sales Analytics")
    st.caption(
        "Quantity-based sales insights (F-006): units sold and "
        "patterns. Revenue analytics need price data the application "
        "does not store."
    )

    show_flash()

    products = product_service.list_products()
    if not products:
        st.info(
            "No active products yet. Add products on the Products & "
            "Inventory page, then record sales to see analytics."
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
    columns[0].metric("Units sold", totals["units_sold"])
    columns[1].metric("Sales recorded", totals["sale_count"])
    columns[2].metric(
        "Avg units/day",
        totals["avg_units_per_day"],
        help=f"Over all {totals['days_in_range']} days in the range "
        "(days without sales count as zero).",
    )
    columns[3].metric(
        "Days with sales",
        totals["days_with_sales"],
        help=f"Out of {totals['days_in_range']} days in the range.",
    )

    _render_daily_trend(data)
    _render_weekday_pattern(data)
    _render_per_product(data)
    _render_performance(start, end, product_id)
    _render_monthly(data)


def _render_daily_trend(data: dict) -> None:
    st.subheader("📈 Daily units sold")
    if not data["daily"]:
        st.info("No sales recorded in this range.")
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
    st.subheader("🗓️ Weekday pattern")
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
    st.subheader("🥇 Sales by product")
    if not data["per_product"]:
        st.info("No sales recorded in this range.")
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


def _render_performance(
    start: str, end: str, product_id: int | None
) -> None:
    """TASK-043: per-product performance insights (F-011)."""
    st.subheader("🔎 Product performance")
    try:
        rows = analytics_service.get_product_performance(
            start, end, product_id=product_id
        )
    except (ValueError, DatabaseError) as error:
        st.error(f"Could not load product performance: {error}")
        return
    if not rows:
        st.info("No sales recorded in this range.")
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


def _render_monthly(data: dict) -> None:
    st.subheader("📅 Monthly totals")
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
