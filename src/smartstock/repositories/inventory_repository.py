"""Inventory repository (TASK-012).

Direct stock access per DEC-047: current stock is a maintained column,
and this module owns every stock change so the approved policies apply
in one place:

- Stock never becomes negative (DEC-034): the database CHECK rejects
  it and these functions reject it with a clear validation message
  before SQL runs.
- There is no movement history in v1 (DEC-047); corrections go through
  ``set_stock_level`` and overwrite the stored value.
"""

import sqlite3

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.utils.dates import utc_now_iso


def get_current_stock(
    connection: sqlite3.Connection, product_id: int
) -> int:
    """Return the stored current stock for a product.

    Raises:
        ValueError: If the product does not exist.
        DatabaseError: If the lookup fails at the database level.
    """
    try:
        cursor = connection.execute(
            "SELECT current_stock FROM products WHERE id = ?",
            (product_id,),
        )
        row = cursor.fetchone()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not read stock for product {product_id}: {error}",
            cause=error,
        ) from error
    if row is None:
        raise ValueError(
            t("svc.common.product_missing", product_id=product_id)
        )
    return int(row["current_stock"])


def adjust_stock(
    connection: sqlite3.Connection,
    product_id: int,
    change: int,
    commit: bool = True,
) -> int:
    """Apply a signed manual stock adjustment and return the new stock.

    Add stock with a positive ``change`` and remove stock with a
    negative value. Zero-change adjustments are rejected because they
    are always a caller mistake.

    Args:
        connection: Open database connection.
        product_id: Product whose stock changes.
        change: Signed integer quantity (positive adds, negative
            removes).
        commit: Commit immediately (default). Pass False when composing
            several writes in one transaction; the caller's session
            manager commits instead.

    Raises:
        ValueError: If the change is invalid, the product is unknown,
            or the adjustment would make stock negative (DEC-034).
        DatabaseError: If the update fails at the database level.
    """
    if isinstance(change, bool) or not isinstance(change, int):
        raise ValueError(
            t("svc.inventory.change_integer", value=change)
        )
    if change == 0:
        raise ValueError(t("svc.inventory.change_not_zero"))

    current = get_current_stock(connection, product_id)
    new_stock = current + change
    if new_stock < 0:
        raise ValueError(
            t(
                "svc.inventory.negative_rejected",
                change=change,
                product_id=product_id,
                new_stock=new_stock,
                current=current,
            )
        )

    try:
        cursor = connection.execute(
            "UPDATE products SET current_stock = ?, updated_at = ? "
            "WHERE id = ?",
            (new_stock, utc_now_iso(), product_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(
                t("svc.common.product_missing", product_id=product_id)
            )
        if commit:
            connection.commit()
    except ValueError:
        raise
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not adjust stock for product {product_id}: {error}",
            cause=error,
        ) from error
    return new_stock


def set_stock_level(
    connection: sqlite3.Connection, product_id: int, stock: int
) -> int:
    """Set the stored stock to an explicit value (correction/reconciliation).

    Unlike ``adjust_stock``, this overwrites the stored value. It is an
    explicitly requested operation: use it for initial stock setup or
    correcting wrong data, not for recording sales or ordinary changes.

    Raises:
        ValueError: If the value is not a nonnegative integer or the
            product does not exist.
        DatabaseError: If the update fails at the database level.
    """
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
        raise ValueError(
            t("svc.inventory.level_nonnegative", value=stock)
        )
    try:
        cursor = connection.execute(
            "UPDATE products SET current_stock = ?, updated_at = ? "
            "WHERE id = ?",
            (stock, utc_now_iso(), product_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(
                t("svc.common.product_missing", product_id=product_id)
            )
        connection.commit()
    except ValueError:
        raise
    except sqlite3.IntegrityError as error:
        raise DatabaseError(
            f"Could not set stock for product {product_id}: {error}",
            cause=error,
        ) from error
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not set stock for product {product_id}: {error}",
            cause=error,
        ) from error
    return stock
