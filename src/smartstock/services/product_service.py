"""Application services for products (TASK-013).

Services are the layer between the Streamlit pages and the data layer:
they coordinate repositories, apply validation that spans more than one
repository, and return plain data the pages can display directly.

Product operations here are independent of Streamlit on purpose, so they
can be tested without a UI and reused by future interfaces.

All functions open a managed database session (commit/rollback/close is
handled by ``smartstock.database.connection``). Errors from the data
layer (``ValueError`` for invalid input, ``DatabaseError`` for database
failures) propagate unchanged so pages can show the same clear messages
the repositories produce.
"""

from pathlib import Path

import config
from smartstock.database.connection import ConnectionContext, session
from smartstock.repositories import product_repository


def _resolve_db_path(db_path: Path | None) -> Path:
    """Return the given path, or the configured application database."""
    if db_path is None:
        return config.DATABASE_PATH
    return Path(db_path)


def _run(db_path: Path | None) -> ConnectionContext:
    """Open a session for the configured (or given) database."""
    return session(_resolve_db_path(db_path))


def create_product(
    name: str,
    sku: str,
    category: str = "",
    initial_stock: int = 0,
    lead_time_days: int = 3,
    safety_stock: int = 0,
    dataset_item_id: int | None = None,
    db_path: Path | None = None,
) -> dict:
    """Create a product with its initial stock in one operation.

    The initial stock is written together with the product row, so a
    new product can never exist without its stock being defined.

    Defaults follow the approved decisions: lead time 3 days (DEC-037),
    safety stock 0 (DEC-036), and the product starts active (DEC-048).

    Args:
        name: Nonempty product name.
        sku: Nonempty unique business identifier.
        category: Optional category label.
        initial_stock: Nonnegative starting quantity (default 0).
        lead_time_days: Nonnegative replenishment days (default 3).
        safety_stock: Nonnegative buffer quantity (default 0).
        dataset_item_id: Optional linked dataset item for forecasting
            (DEC-060; default no link).
        db_path: Database to use; defaults to the configured path.

    Returns:
        The created product as a dictionary.

    Raises:
        ValueError: If a field is invalid or the SKU already exists.
        DatabaseError: If the insert fails at the database level.
    """
    with _run(db_path) as connection:
        return product_repository.create_product(
            connection,
            name=name,
            sku=sku,
            category=category,
            current_stock=initial_stock,
            lead_time_days=lead_time_days,
            safety_stock=safety_stock,
            dataset_item_id=dataset_item_id,
        )


def get_product(product_id: int, db_path: Path | None = None) -> dict | None:
    """Return one product by id, or None when it does not exist."""
    with _run(db_path) as connection:
        return product_repository.get_product(connection, product_id)


def get_product_by_sku(
    sku: str, db_path: Path | None = None
) -> dict | None:
    """Return one product by SKU, or None when it does not exist."""
    with _run(db_path) as connection:
        return product_repository.get_product_by_sku(connection, sku)


def list_products(
    active_only: bool = True, db_path: Path | None = None
) -> list:
    """List products ordered by SKU.

    Args:
        active_only: Exclude deactivated products (default, per the
            soft-delete policy DEC-048 and listing rule BR-026).
        db_path: Database to use; defaults to the configured path.
    """
    with _run(db_path) as connection:
        return product_repository.list_products(
            connection, active_only=active_only
        )


def update_product(
    product_id: int,
    db_path: Path | None = None,
    **fields,
) -> dict | None:
    """Update editable product fields (name, sku, category, lead_time_days,
    safety_stock).

    Stock is intentionally not updatable here; see the inventory
    service for the approved stock-change operations.

    Args:
        product_id: Product to update.
        db_path: Database to use; defaults to the configured path.
        **fields: Keyword arguments forwarded to the repository
            (only provided fields change).

    Returns:
        The updated product, or None when the product does not exist.

    Raises:
        ValueError: If a field value is invalid or the SKU conflicts.
        DatabaseError: If the update fails at the database level.
    """
    if "current_stock" in fields:
        raise ValueError(
            "Stock cannot be changed through update_product; use the "
            "inventory service for stock changes."
        )
    with _run(db_path) as connection:
        return product_repository.update_product(
            connection, product_id, **fields
        )


def set_product_active(
    product_id: int, is_active: bool, db_path: Path | None = None
) -> dict | None:
    """Activate or deactivate a product (soft delete policy DEC-048).

    Deactivating is the approved "remove product" behavior: the row and
    its sales history are preserved, and listings skip the product
    (BR-026). Reactivation restores it.
    """
    with _run(db_path) as connection:
        return product_repository.set_product_active(
            connection, product_id, is_active
        )
