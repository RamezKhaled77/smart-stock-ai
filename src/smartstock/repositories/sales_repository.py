"""Sales repository (TASK-012).

All SQL access for the sales table. Functions require an open
connection and focus on storage and retrieval only:

- Stock validation and the insufficient-stock policy (DEC-035) live in
  the services layer, which combines this repository with the
  inventory repository in one transaction.
- Sales rows are immutable in v1 (DEC-049); no update or delete
  operations are provided.
"""

import datetime as dt

import sqlite3

from smartstock.database.connection import DatabaseError
from smartstock.utils.dates import utc_now_iso


def record_sale(
    connection: sqlite3.Connection,
    product_id: int,
    quantity: int,
    sale_date: str,
    commit: bool = True,
) -> dict:
    """Insert a sales record and return it as a dictionary.

    Args:
        connection: Open database connection.
        product_id: Existing product (foreign key enforced).
        quantity: Units sold (positive integer).
        sale_date: Sale date as an ISO ``YYYY-MM-DD`` string.
        commit: Commit immediately (default). Pass False when composing
            several writes in one transaction; the caller's session
            manager commits instead.

    Returns:
        The stored sale as ``{"id", "product_id", "quantity",
        "sale_date", "created_at"}``.

    Raises:
        ValueError: If quantity or the date is invalid.
        DatabaseError: If the product is unknown (integrity error) or
            the insert fails at the database level.
    """
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError(f"Sale quantity must be an integer, got {quantity!r}.")
    if quantity <= 0:
        raise ValueError("Sale quantity must be positive.")
    if not isinstance(sale_date, str) or not _is_iso_date(sale_date):
        raise ValueError(
            f"Sale date must be a 'YYYY-MM-DD' string, got {sale_date!r}."
        )

    now = _utc_now()
    try:
        cursor = connection.execute(
            "INSERT INTO sales (product_id, quantity, sale_date, "
            "created_at) VALUES (?, ?, ?, ?)",
            (product_id, quantity, sale_date, now),
        )
        if commit:
            connection.commit()
    except sqlite3.IntegrityError as error:
        raise DatabaseError(
            f"Could not record sale: product {product_id} does not exist.",
            cause=error,
        ) from error
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not record sale: {error}", cause=error
        ) from error

    sale_id = cursor.lastrowid
    return {
        "id": sale_id,
        "product_id": product_id,
        "quantity": quantity,
        "sale_date": sale_date,
        "created_at": now,
    }


def list_sales(
    connection: sqlite3.Connection,
    product_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list:
    """List sales with optional filters, oldest first.

    Args:
        connection: Open database connection.
        product_id: Only sales of this product, when given.
        start_date: Inclusive lower bound (``YYYY-MM-DD``), when given.
        end_date: Inclusive upper bound (``YYYY-MM-DD``), when given.

    Returns:
        List of sale dictionaries.

    Raises:
        ValueError: If a filter date is not valid ``YYYY-MM-DD``.
        DatabaseError: If the query fails.
    """
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None and not _is_iso_date(value):
            raise ValueError(
                f"{label} must be a 'YYYY-MM-DD' string, got {value!r}."
            )

    conditions = []
    parameters = []
    if product_id is not None:
        conditions.append("product_id = ?")
        parameters.append(product_id)
    if start_date is not None:
        conditions.append("sale_date >= ?")
        parameters.append(start_date)
    if end_date is not None:
        conditions.append("sale_date <= ?")
        parameters.append(end_date)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    try:
        cursor = connection.execute(
            "SELECT id, product_id, quantity, sale_date, created_at "
            "FROM sales" + where + " ORDER BY sale_date, id",
            parameters,
        )
        rows = cursor.fetchall()
    except sqlite3.Error as error:
        raise DatabaseError(f"Could not read sales: {error}", cause=error)

    return [dict(row) for row in rows]


def get_first_sale_date(connection: sqlite3.Connection) -> str | None:
    """Earliest recorded sale date across all products, if any.

    Used by the stock overview to fetch each product's full observed
    history (DEC-059 anchors the demand window at the last sale date,
    but "no product may lose history just because it sold before this
    window" requires knowing how far back sales exist).

    Args:
        connection: Open database connection.

    Returns:
        The earliest ``sale_date`` as ``YYYY-MM-DD``, or ``None`` when
        no sales are recorded.

    Raises:
        DatabaseError: If the query fails.
    """
    try:
        row = connection.execute(
            "SELECT MIN(sale_date) AS first_date FROM sales"
        ).fetchone()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not read the first sale date: {error}", cause=error
        )
    return row["first_date"] if row is not None else None


def get_daily_sales(
    connection: sqlite3.Connection,
    product_id: int,
    start_date: str,
    end_date: str,
) -> dict:
    """Sum sold quantity per day for one product (inclusive bounds).

    Args:
        connection: Open database connection.
        product_id: Product to aggregate.
        start_date: Inclusive lower bound (``YYYY-MM-DD``).
        end_date: Inclusive upper bound (``YYYY-MM-DD``).

    Returns:
        Dictionary mapping each observed ``YYYY-MM-DD`` string to the
        total quantity sold that day. Days without sales are absent
        (callers decide how to represent them, per the preprocessing
        documentation).

    Raises:
        ValueError: If the dates are invalid.
        DatabaseError: If the query fails.
    """
    for value in (start_date, end_date):
        if not _is_iso_date(value):
            raise ValueError(
                f"Dates must be 'YYYY-MM-DD' strings, got {value!r}."
            )
    try:
        cursor = connection.execute(
            "SELECT sale_date, SUM(quantity) AS total "
            "FROM sales WHERE product_id = ? AND sale_date >= ? "
            "AND sale_date <= ? GROUP BY sale_date ORDER BY sale_date",
            (product_id, start_date, end_date),
        )
        rows = cursor.fetchall()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not aggregate sales for product {product_id}: {error}",
            cause=error,
        ) from error
    return {row["sale_date"]: int(row["total"]) for row in rows}


def get_daily_sales_by_product(
    connection: sqlite3.Connection,
    start_date: str,
    end_date: str,
) -> dict:
    """Sum sold quantity per day for every product (inclusive bounds).

    Same aggregation as :func:`get_daily_sales` for all products in one
    query, so pages listing many products avoid one query per product.

    Args:
        connection: Open database connection.
        start_date: Inclusive lower bound (``YYYY-MM-DD``).
        end_date: Inclusive upper bound (``YYYY-MM-DD``).

    Returns:
        Dictionary mapping each ``product_id`` to its per-day totals
        dictionary (same shape as ``get_daily_sales``). Products with
        no sales in the window are absent.

    Raises:
        ValueError: If the dates are invalid.
        DatabaseError: If the query fails.
    """
    for value in (start_date, end_date):
        if not _is_iso_date(value):
            raise ValueError(
                f"Dates must be 'YYYY-MM-DD' strings, got {value!r}."
            )
    try:
        cursor = connection.execute(
            "SELECT product_id, sale_date, SUM(quantity) AS total "
            "FROM sales WHERE sale_date >= ? AND sale_date <= ? "
            "GROUP BY product_id, sale_date ORDER BY product_id, sale_date",
            (start_date, end_date),
        )
        rows = cursor.fetchall()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not aggregate sales by product: {error}", cause=error
        ) from error
    totals_by_product: dict[int, dict] = {}
    for row in rows:
        product_totals = totals_by_product.setdefault(row["product_id"], {})
        product_totals[row["sale_date"]] = int(row["total"])
    return totals_by_product


def _is_iso_date(value: str) -> bool:
    """Check that a string parses as an ISO calendar date."""
    try:
        dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _utc_now() -> str:
    """Current UTC ISO timestamp (delegated to the shared helper)."""
    return utc_now_iso()
