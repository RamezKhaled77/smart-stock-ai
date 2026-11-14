"""Application service for the Dashboard metrics (TASK-037).

Composes the approved DEC-061 metric set from the other services — no
SQL and no business rules here, only composition of already-verified
calculations:

- Total active products and total stock (product/inventory data).
- Products needing reorder (BR-022 via the restocking calculations).
- Recent sales activity: units and sale count in the last 7 days.
- Top sellers: best-selling products over the last 30 days.
- Forecast readiness: active products linked to a dataset item
  (DEC-060) out of the total.
- Sales trend series and the low-stock overview (TASK-038/TASK-039)
  are returned alongside so the dashboard page renders one data
  snapshot.

All windows end at the current UTC date, matching DEC-059's
calendar-day view. Read-only: nothing here mutates data.
"""

import datetime as dt
from pathlib import Path

from smartstock.domain.inventory import STATUS_IN_STOCK
from smartstock.services import (
    product_service,
    restock_service,
    sales_service,
)
from smartstock.utils.dates import utc_today_iso


def get_dashboard_data(
    db_path: Path | None = None,
    trend_days: int = 30,
) -> dict:
    """One dashboard data snapshot.

    Args:
        db_path: Database to use; defaults to the configured path.
        trend_days: Calendar length of the sales-trend window
            (positive integer; the page offers 7/30, default 30).

    Returns:
        Dictionary with:

        - ``total_active_products``: int.
        - ``total_stock``: sum of current stock over active products.
        - ``products_needing_reorder``: int (BR-022, advisory data;
          products without enough history are not counted).
        - ``recent_sales``: ``{"units_sold", "sale_count"}`` for the
          last 7 days ending today (UTC).
        - ``top_products``: best sellers of the last 30 days
          (max 3, best first; DEC-061 fixes this window).
        - ``forecast_ready``: ``{"linked", "total"}`` per DEC-060.
        - ``trend``: ``{date: units}`` daily totals for the trend
          window (days without sales absent).
        - ``low_stock``: recommendation rows (restock service) whose
          stock status is not In Stock (BR-008), attention first.

    Raises:
        DatabaseError: If any underlying read fails.
    """
    if isinstance(trend_days, bool) or not isinstance(
        trend_days, int
    ) or trend_days <= 0:
        raise ValueError(
            f"trend_days must be a positive integer, got {trend_days!r}."
        )

    today = utc_today_iso()
    today_date = dt.date.fromisoformat(today)
    week_start = (today_date - dt.timedelta(days=6)).isoformat()
    month_start = (today_date - dt.timedelta(days=29)).isoformat()
    trend_start = (today_date - dt.timedelta(days=trend_days - 1)).isoformat()

    products = product_service.list_products(db_path=db_path)
    recommendations = restock_service.get_restock_recommendations(
        db_path=db_path
    )

    recent_sales = sales_service.get_sales_window_summary(
        week_start, today, db_path=db_path
    )
    top_products = sales_service.get_top_sellers(
        month_start, today, limit=3, db_path=db_path
    )
    trend = sales_service.get_daily_totals(
        trend_start, today, db_path=db_path
    )

    low_stock = [
        row for row in recommendations if row["stock_status"] is not None
        and row["stock_status"] != STATUS_IN_STOCK
    ]

    return {
        "total_active_products": len(products),
        "total_stock": sum(
            int(product["current_stock"]) for product in products
        ),
        "products_needing_reorder": sum(
            1 for row in recommendations if row["needs_reorder"]
        ),
        "recent_sales": recent_sales,
        "top_products": top_products,
        "forecast_ready": {
            "linked": sum(
                1 for product in products
                if product.get("dataset_item_id") is not None
            ),
            "total": len(products),
        },
        "trend": trend,
        "low_stock": low_stock,
    }
