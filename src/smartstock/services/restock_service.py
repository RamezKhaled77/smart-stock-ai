"""Application service for advisory restocking recommendations
(TASK-035).

Composes one :class:`~smartstock.domain.restocking.RestockRecommendation`
per active product from stored data only — a read-only operation:

- Inventory is never mutated here (restocking advice is advisory,
  DEC-031; stock changes go through the inventory service operations).
- Forecasts are not consumed yet: per DEC-030/DEC-038 the restocking
  formulas use historical average daily demand so they can be
  explained and tested standalone. When the Forecast page lands, the
  model forecast (DEC-057/DEC-058) is presented alongside, not inside,
  these formulas.
"""

from pathlib import Path

from smartstock.domain.restocking import build_restock_recommendation
from smartstock.repositories import (
    product_repository,
    sales_repository,
)
from smartstock.services.inventory_service import _run
from smartstock.utils.dates import utc_today_iso


def _round_for_display(recommendations: list) -> list:
    """Return dict rows with the demand rounded for display.

    The domain keeps raw floats (per prediction-logic §11 rounding
    belongs to the presentation layer); 4 decimals are display-friendly
    without hiding small intermittent-seller demand.
    """
    rows = []
    for recommendation in recommendations:
        row = vars(recommendation).copy()
        if row["average_daily_demand"] is not None:
            row["average_daily_demand"] = round(
                row["average_daily_demand"], 4
            )
        rows.append(row)
    return rows


def get_restock_recommendations(db_path: Path | None = None) -> list:
    """Advisory restocking recommendations, one active product per row.

    Args:
        db_path: Database to use; defaults to the configured path.

    Returns:
        List of recommendation dictionaries ordered by SKU. Products
        with missing inputs (no sales history, no stock level) carry
        ``available: False`` with an ``unavailable_reason`` instead of
        silently showing zeros.

    Raises:
        DatabaseError: If reading products or sales fails.
    """
    with _run(db_path) as connection:
        products = product_repository.list_products(connection)
        first_sale_date = sales_repository.get_first_sale_date(connection)
        if first_sale_date is None:
            sales_by_product = {}
        else:
            # Full observed history; the DEC-059 window logic trims to
            # each product's own span later. Future-dated sales cannot
            # exist (future dates are rejected at recording), so all
            # recorded sales fall within today's UTC bounds.
            sales_by_product = sales_repository.get_daily_sales_by_product(
                connection, first_sale_date, utc_today_iso()
            )

    recommendations = []
    for product in products:
        daily_totals = sales_by_product.get(product["id"], {})
        recommendations.append(
            build_restock_recommendation(product, daily_totals)
        )
    return _round_for_display(recommendations)
