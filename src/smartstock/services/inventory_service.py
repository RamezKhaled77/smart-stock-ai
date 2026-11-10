"""Application services for inventory (TASK-014).

Coordinates the approved stock operations through the inventory
repository, which is the single owner of stock changes (DEC-047):

- Reading current stock.
- Manual stock adjustments (signed change; guarded by DEC-034 so stock
  never becomes negative).
- Explicit stock level setting, for initial setup and corrections only.
- Stock overview for listing pages: average demand (DEC-038), reorder
  point (DEC-032), and stock status (BR-008) per active product.

Per the approved rules, recorded sales also change stock — that
transaction lives in the sales service (TASK-015), which combines this
repository's validation logic with the sales repository under the
insufficient-stock policy (DEC-035).
"""

from pathlib import Path

import config
from smartstock.database.connection import ConnectionContext, session
from smartstock.domain.inventory import (
    DEMAND_WINDOW_DAYS,
    calculate_average_daily_demand,
    calculate_reorder_point,
    classify_stock,
)
from smartstock.repositories import (
    inventory_repository,
    product_repository,
    sales_repository,
)
from smartstock.utils.dates import utc_today_iso


def _run(db_path: Path | None) -> ConnectionContext:
    """Open a session for the configured (or given) database."""
    if db_path is None:
        db_path = config.DATABASE_PATH
    return session(db_path)


def get_current_stock(
    product_id: int, db_path: Path | None = None
) -> int:
    """Return the stored current stock for a product.

    Raises:
        ValueError: If the product does not exist.
        DatabaseError: If the lookup fails at the database level.
    """
    with _run(db_path) as connection:
        return inventory_repository.get_current_stock(
            connection, product_id
        )


def adjust_stock(
    product_id: int,
    change: int,
    db_path: Path | None = None,
) -> int:
    """Apply a signed manual stock adjustment and return the new stock.

    Positive ``change`` adds stock (receipts, corrections upward);
    negative removes stock (damage, loss, manual reductions). A zero
    change and non-integer values are rejected as caller mistakes, and
    an adjustment that would take stock below zero is rejected per the
    negative-stock policy (DEC-034).

    Returns:
        The new stock level after the adjustment.

    Raises:
        ValueError: If the change is invalid, the product is unknown,
            or the result would be negative.
        DatabaseError: If the update fails at the database level.
    """
    with _run(db_path) as connection:
        return inventory_repository.adjust_stock(
            connection, product_id, change
        )


def set_stock_level(
    product_id: int,
    stock: int,
    db_path: Path | None = None,
) -> int:
    """Set the stored stock to an explicit value and return it.

    This is an explicitly requested correction operation: it overwrites
    the stored value without proving how the difference arose. Use it
    for initial stock setup and fixing wrong data — not for sales
    (which must go through the sales service) or ordinary changes
    (which should use :func:`adjust_stock`).

    Raises:
        ValueError: If the value is not a nonnegative integer or the
            product does not exist.
        DatabaseError: If the update fails at the database level.
    """
    with _run(db_path) as connection:
        return inventory_repository.set_stock_level(
            connection, product_id, stock
        )


def get_stock_overview(db_path: Path | None = None) -> list:
    """Stock overview for one active product per row, ready for listing.

    For every active product (BR-026), combines stored product data
    with computed stock indicators:

    - ``average_daily_demand``: mean demand over the product's most
      recent available history — per DEC-059 the window ends at the
      product's last recorded sale date and covers up to
      ``DEMAND_WINDOW_DAYS`` (30) calendar days; days without sales
      count as zero.
    - ``reorder_point``: per DEC-032 from the demand, the product's
      lead time, and safety stock.
    - ``stock_status``: In Stock / Low Stock / Out of Stock (BR-008).

    Args:
        db_path: Database to use; defaults to the configured path.

    Returns:
        List of product dictionaries with the three extra keys, ordered
        by SKU. Empty list when there are no active products.
    """
    with _run(db_path) as connection:
        products = product_repository.list_products(connection)
        first_sale_date = sales_repository.get_first_sale_date(connection)
        if first_sale_date is None:
            sales_by_product = {}
        else:
            # Full observed history: the DEC-059 window ends at each
            # product's last sale, so nothing may be cut off by a
            # today-anchored pre-filter. Future sales cannot exist
            # (backdated is allowed, future is rejected).
            sales_by_product = sales_repository.get_daily_sales_by_product(
                connection, first_sale_date, utc_today_iso()
            )

    overview = []
    for product in products:
        daily_totals = sales_by_product.get(product["id"], {})
        demand = calculate_average_daily_demand(
            daily_totals, DEMAND_WINDOW_DAYS
        )
        reorder_point = calculate_reorder_point(
            demand,
            product["lead_time_days"],
            product["safety_stock"],
        )
        overview.append(
            {
                **product,
                "average_daily_demand": round(demand, 4),
                "reorder_point": reorder_point,
                "stock_status": classify_stock(
                    product["current_stock"], reorder_point
                ),
            }
        )
    return overview
