"""Application services for inventory (TASK-014).

Coordinates the approved stock operations through the inventory
repository, which is the single owner of stock changes (DEC-047):

- Reading current stock.
- Manual stock adjustments (signed change; guarded by DEC-034 so stock
  never becomes negative).
- Explicit stock level setting, for initial setup and corrections only.

Per the approved rules, recorded sales also change stock — that
transaction lives in the sales service (TASK-015), which combines this
repository's validation logic with the sales repository under the
insufficient-stock policy (DEC-035).
"""

from pathlib import Path

import config
from smartstock.database.connection import ConnectionContext, session
from smartstock.repositories import inventory_repository


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
