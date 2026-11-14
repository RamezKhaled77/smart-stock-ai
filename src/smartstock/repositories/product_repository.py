"""Product repository (TASK-012).

All SQL access for the products table. Functions require an open
connection from ``smartstock.database.connection`` and return plain
dictionaries so callers never depend on sqlite3 Row objects.

Removal follows the approved soft-delete policy (DEC-048): rows are
never deleted; ``set_product_active`` toggles the ``is_active`` flag.
"""

import sqlite3

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.utils.dates import utc_now_iso


def _to_dict(row: sqlite3.Row) -> dict:
    """Convert a products row to a plain dictionary."""
    return dict(row)


def _validate_dataset_item_id(value: int | None) -> None:
    """Validate the DEC-060 dataset-item link (positive int or None)."""
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            t(
                "svc.products.dataset_item_invalid",
                value=value,
            )
        )


def create_product(
    connection: sqlite3.Connection,
    name: str,
    sku: str,
    category: str = "",
    current_stock: int = 0,
    lead_time_days: int = 3,
    safety_stock: int = 0,
    dataset_item_id: int | None = None,
) -> dict:
    """Insert a new product and return it as a dictionary.

    Defaults follow the approved decisions: stock starts at zero
    (DEC-047), lead time 3 days (DEC-037), safety stock 0 (DEC-036),
    and the product is active (DEC-048).

    Args:
        connection: Open database connection.
        name: Nonempty product name.
        sku: Nonempty unique business identifier.
        category: Optional category label.
        current_stock: Initial stock (nonnegative, default 0).
        lead_time_days: Nonnegative integer (default 3).
        safety_stock: Nonnegative integer (default 0).
        dataset_item_id: Optional linked dataset item (DEC-060) used
            by the forecasting component (default no link).

    Returns:
        The created product as a dictionary.

    Raises:
        ValueError: If a field is invalid or the SKU already exists.
        DatabaseError: If the insert fails for another database reason.
    """
    _validate_dataset_item_id(dataset_item_id)
    if not isinstance(name, str) or not name.strip():
        raise ValueError(t("svc.products.name_required"))
    if not isinstance(sku, str) or not sku.strip():
        raise ValueError(t("svc.products.sku_required"))
    for label, value in (
        ("current_stock", current_stock),
        ("lead_time_days", lead_time_days),
        ("safety_stock", safety_stock),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(
                t(
                    "svc.products.field_nonnegative",
                    label=label,
                    value=value,
                )
            )

    now = utc_now_iso()
    try:
        cursor = connection.execute(
            "INSERT INTO products "
            "(name, sku, category, current_stock, lead_time_days, "
            " safety_stock, dataset_item_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name.strip(),
                sku.strip(),
                category,
                current_stock,
                lead_time_days,
                safety_stock,
                dataset_item_id,
                now,
                now,
            ),
        )
        connection.commit()
        product_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        message = str(error)
        if "UNIQUE" in message.upper() and "sku" in message.lower():
            raise ValueError(
                t("svc.products.sku_exists", sku=sku)
            ) from error
        raise DatabaseError(
            f"Could not create product: {message}", cause=error
        ) from error
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not create product: {error}", cause=error
        ) from error

    created = get_product(connection, product_id)
    if created is None:  # defensive: insert reported success
        raise DatabaseError(
            f"Product {product_id} inserted but could not be read back."
        )
    return created


def get_product(
    connection: sqlite3.Connection, product_id: int
) -> dict | None:
    """Return one product by id, or None when it does not exist."""
    cursor = connection.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _to_dict(row)


def get_product_by_sku(connection: sqlite3.Connection, sku: str) -> dict | None:
    """Return one product by SKU, or None when it does not exist."""
    cursor = connection.execute(
        "SELECT * FROM products WHERE sku = ?", (sku,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _to_dict(row)


def list_products(
    connection: sqlite3.Connection, active_only: bool = True
) -> list:
    """List products ordered by SKU.

    Args:
        connection: Open database connection.
        active_only: Exclude deactivated products (default, per the
            soft-delete policy DEC-048).

    Returns:
        List of product dictionaries.
    """
    if active_only:
        cursor = connection.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY sku"
        )
    else:
        cursor = connection.execute("SELECT * FROM products ORDER BY sku")
    return [_to_dict(row) for row in cursor.fetchall()]


UNSET = object()  # sentinel: dataset_item_id provided vs. unchanged


def update_product(
    connection: sqlite3.Connection,
    product_id: int,
    name: str | None = None,
    sku: str | None = None,
    category: str | None = None,
    lead_time_days: int | None = None,
    safety_stock: int | None = None,
    dataset_item_id: int | None = UNSET,  # type: ignore[assignment]
) -> dict | None:
    """Update editable product fields and return the updated product.

    Only the provided (non-None) fields change. ``updated_at`` is
    refreshed automatically. ``current_stock`` is intentionally not a
    parameter here; use the inventory repository for stock changes so
    the approved adjustment rules apply in one place.

    ``dataset_item_id`` (DEC-060) uses a sentinel: pass an integer to
    link, ``None`` to unlink, and leave unset to keep the current link.

    Raises:
        ValueError: If FK-unique violations (SKU) or invalid values.
        DatabaseError: For other database failures.
    """
    assignments: list = []
    parameters: list = []

    if dataset_item_id is not UNSET:
        _validate_dataset_item_id(dataset_item_id)
        assignments.append("dataset_item_id = ?")
        parameters.append(dataset_item_id)

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(t("svc.products.name_required"))
        assignments.append("name = ?")
        parameters.append(name.strip())
    if sku is not None:
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError(t("svc.products.sku_required"))
        assignments.append("sku = ?")
        parameters.append(sku.strip())
    if category is not None:
        assignments.append("category = ?")
        parameters.append(category)
    for label, value in (
        ("lead_time_days", lead_time_days),
        ("safety_stock", safety_stock),
    ):
        if value is not None and (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(
                t(
                    "svc.products.field_nonnegative_plain",
                    label=label,
                    value=value,
                )
            )
    if lead_time_days is not None:
        assignments.append("lead_time_days = ?")
        parameters.append(lead_time_days)
    if safety_stock is not None:
        assignments.append("safety_stock = ?")
        parameters.append(safety_stock)

    if not assignments:
        return get_product(connection, product_id)

    assignments.append("updated_at = ?")
    parameters.append(utc_now_iso())
    parameters.append(product_id)

    try:
        connection.execute(
            f"UPDATE products SET {', '.join(assignments)} WHERE id = ?",
            parameters,
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        message = str(error)
        if "UNIQUE" in message.upper() and "sku" in message.lower():
            raise ValueError(
                t("svc.products.sku_exists", sku=sku)
            ) from error
        raise DatabaseError(
            f"Could not update product {product_id}: {message}",
            cause=error,
        ) from error
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not update product {product_id}: {error}", cause=error
        ) from error

    return get_product(connection, product_id)


def set_product_active(
    connection: sqlite3.Connection, product_id: int, is_active: bool
) -> dict | None:
    """Activate or deactivate a product (soft delete, DEC-048).

    Rows are never deleted; this toggles ``is_active`` and refreshes
    ``updated_at``.
    """
    if not isinstance(is_active, bool):
        raise ValueError("is_active must be a boolean.")
    try:
        connection.execute(
            "UPDATE products SET is_active = ?, updated_at = ? "
            "WHERE id = ?",
            (1 if is_active else 0, utc_now_iso(), product_id),
        )
        connection.commit()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not change active state for product {product_id}: "
            f"{error}",
            cause=error,
        ) from error
    return get_product(connection, product_id)
