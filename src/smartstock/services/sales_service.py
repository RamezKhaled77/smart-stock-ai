"""Application services for sales (TASK-015).

Sales recording is the one operation where two-owned data changes must
succeed or fail together, which realizes the insufficient-stock policy
(DEC-035):

    A sale is accepted only when current stock covers the requested
    quantity. Accepted sales are stored (sales repository) and the
    product stock is reduced by the same amount (inventory repository)
    in one database transaction. A rejected sale leaves the inventory
    unchanged, and the error identifies the requested and available
    quantities.

Reading and aggregating sales delegates to the sales repository. Sales
rows themselves are immutable in v1 (DEC-049); corrections happen
through explicitly recorded stock adjustments.
"""

from pathlib import Path

import config
from smartstock.database.connection import ConnectionContext, session
from smartstock.repositories import (
    inventory_repository,
    product_repository,
    sales_repository,
)
from smartstock.utils.dates import utc_today_iso


class InsufficientStockError(ValueError):
    """Raised when a requested sale exceeds the available stock (DEC-035).

    Inherits from ``ValueError`` so generic invalid-input handling in
    the pages continues to work, while the UI can also give this case a
    specific, friendly message.
    """

    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: requested "
            f"{requested}, but only {available} available. The sale was "
            "not recorded."
        )


def _run(db_path: Path | None) -> ConnectionContext:
    """Open a session for the configured (or given) database."""
    if db_path is None:
        db_path = config.DATABASE_PATH
    return session(db_path)


def record_sale(
    product_id: int,
    quantity: int,
    sale_date: str,
    db_path: Path | None = None,
) -> dict:
    """Record a sale and reduce stock atomically (DEC-035 accepted path).

    The three steps run on one connection inside one transaction:
    validating the available stock, inserting the sale, and decrementing
    the product stock. If any step fails, the session manager rolls
    everything back, so a rejected sale never changes the inventory.

    Args:
        product_id: Product being sold (must exist and be active).
        quantity: Units sold (positive integer).
        sale_date: Sale date as an ISO ``YYYY-MM-DD`` string, not in the
            future (historical backdated entries are allowed, e.g.
            recording yesterday's sales); the quantity is still checked
            against current stock.
        db_path: Database to use; defaults to the configured path.

    Returns:
        The stored sale as a dictionary.

    Raises:
        InsufficientStockError: If the requested quantity exceeds the
            current stock (the sale is not recorded).
        ValueError: If the quantity or date is invalid, or the product
            does not exist.
        DatabaseError: If any step fails at the database level.
    """
    with _run(db_path) as connection:
        # Quick validation before any write so obvious mistakes (zero,
        # non-integer, bad date) never open a transaction.
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError(
                f"Sale quantity must be an integer, got {quantity!r}."
            )
        if quantity <= 0:
            raise ValueError("Sale quantity must be positive.")
        if not isinstance(sale_date, str) or sale_date > utc_today_iso():
            raise ValueError(
                f"Sale date must be a 'YYYY-MM-DD' date not in the future, "
                f"got {sale_date!r}."
            )

        product = product_repository.get_product(connection, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} does not exist.")
        if not product["is_active"]:
            raise ValueError(
                f"Product {product_id} ('{product['name']}') is inactive; "
                "sales cannot be recorded for it."
            )

        available = inventory_repository.get_current_stock(
            connection, product_id
        )
        if quantity > available:
            raise InsufficientStockError(product_id, quantity, available)

        # Both writes skip their own commit; the session manager below
        # commits once when the block completes successfully.
        sale = sales_repository.record_sale(
            connection,
            product_id,
            quantity,
            sale_date,
            commit=False,
        )
        inventory_repository.adjust_stock(
            connection, product_id, -quantity, commit=False
        )
    return sale


def list_sales(
    product_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path | None = None,
) -> list:
    """List sales with optional filters, oldest first.

    Args:
        product_id: Only sales of this product, when given.
        start_date: Inclusive lower bound (``YYYY-MM-DD``), when given.
        end_date: Inclusive upper bound (``YYYY-MM-DD``), when given.
        db_path: Database to use; defaults to the configured path.
    """
    with _run(db_path) as connection:
        return sales_repository.list_sales(
            connection,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )


def get_daily_sales(
    product_id: int,
    start_date: str,
    end_date: str,
    db_path: Path | None = None,
) -> dict:
    """Sum sold quantity per day for one product (inclusive bounds).

    Returns:
        Dictionary mapping each day with sales to the total quantity
        sold; days without sales are absent (preprocessing policy).
    """
    with _run(db_path) as connection:
        return sales_repository.get_daily_sales(
            connection, product_id, start_date, end_date
        )


def get_sales_window_summary(
    start_date: str,
    end_date: str,
    db_path: Path | None = None,
) -> dict:
    """Sale count and total units sold in an inclusive window.

    Returns:
        ``{"sale_count": int, "units_sold": int}`` (both 0 without
        sales in the window).
    """
    with _run(db_path) as connection:
        return sales_repository.get_sales_window_summary(
            connection, start_date, end_date
        )


def get_top_sellers(
    start_date: str,
    end_date: str,
    limit: int = 3,
    db_path: Path | None = None,
) -> list:
    """Best-selling products in an inclusive window, best first.

    Returns:
        List of ``{"product_id", "name", "sku", "units_sold"}``.
    """
    with _run(db_path) as connection:
        return sales_repository.get_top_products(
            connection, start_date, end_date, limit=limit
        )


def get_daily_totals(
    start_date: str,
    end_date: str,
    db_path: Path | None = None,
) -> dict:
    """Total units sold per day across all products (inclusive bounds).

    Merges the per-product daily aggregates into one dictionary —
    the input for the dashboard sales-trend chart (TASK-038).
    """
    with _run(db_path) as connection:
        by_product = sales_repository.get_daily_sales_by_product(
            connection, start_date, end_date
        )
    totals: dict[str, int] = {}
    for daily in by_product.values():
        for day, quantity in daily.items():
            totals[day] = totals.get(day, 0) + quantity
    return totals


def get_product_sales_summary(
    start_date: str,
    end_date: str,
    db_path: Path | None = None,
) -> list:
    """Per-product units and sale counts in an inclusive window.

    Analytics input (F-006): every product that sold in the window,
    best seller first.
    """
    with _run(db_path) as connection:
        return sales_repository.get_product_sales_summary(
            connection, start_date, end_date
        )


def get_daily_sales_by_product(
    start_date: str,
    end_date: str,
    db_path: Path | None = None,
) -> dict:
    """Per-product per-day totals in an inclusive window.

    Returns:
        Dictionary mapping each product id that sold in the window to
        its ``{date: units}`` totals (days without sales absent).
    """
    with _run(db_path) as connection:
        return sales_repository.get_daily_sales_by_product(
            connection, start_date, end_date
        )
