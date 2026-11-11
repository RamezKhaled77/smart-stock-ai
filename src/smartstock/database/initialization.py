"""SQLite database initialization (TASK-010).

Creates the operational database and its tables per
``database/schema.sql`` and ``docs/02-architecture/database-schema.md``.
Initialization is idempotent: running it repeatedly is safe because the
schema uses ``CREATE TABLE IF NOT EXISTS`` and never drops data.
"""

import sqlite3
from pathlib import Path

from smartstock.database.schema import (
    EXPECTED_COLUMNS,
    REQUIRED_TABLES,
    SCHEMA_PATH,
)


class DatabaseError(Exception):
    """Raised when the database cannot be initialized or verified."""


def initialize_database(db_path: Path) -> None:
    """Create the database file and apply the schema if needed.

    Repeating this function on an existing database is safe: existing
    tables and data are untouched.

    Args:
        db_path: Path to the SQLite database file (default from
            ``config.DATABASE_PATH``).

    Raises:
        DatabaseError: If the schema cannot be read or applied.
    """
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise DatabaseError(
            f"Could not read the database schema file {SCHEMA_PATH}: {error}"
        ) from error

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        connection = sqlite3.connect(db_path)
        try:
            # Foreign key enforcement is required by the schema document.
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(schema_sql)
            _migrate_products_columns(connection)
            connection.commit()
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not initialize the database at {db_path}: {error}"
        ) from error


def _migrate_products_columns(connection: sqlite3.Connection) -> None:
    """Add columns added to ``products`` after a database was created.

    ``CREATE TABLE IF NOT EXISTS`` never alters an existing table, so
    databases created before DEC-060 lack ``dataset_item_id``. The
    migration is additive (nullable column, no backfill needed) and
    idempotent.
    """
    cursor = connection.execute("PRAGMA table_info(products)")
    existing = {row[1] for row in cursor.fetchall()}
    if "dataset_item_id" not in existing:
        connection.execute(
            "ALTER TABLE products ADD COLUMN "
            "dataset_item_id INTEGER DEFAULT NULL "
            "CHECK (dataset_item_id IS NULL OR dataset_item_id > 0)"
        )


def verify_tables(db_path: Path) -> dict:
    """Verify that every required table exists with expected columns.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Dictionary mapping each required table name to the sorted list
        of its column names.

    Raises:
        DatabaseError: If the database file or a required table is
            missing, or the database cannot be opened.
    """
    db_path = Path(db_path)
    if not db_path.is_file():
        raise DatabaseError(f"Database file not found: {db_path}")

    try:
        connection = sqlite3.connect(db_path)
        try:
            table_columns = {}
            for table_name in REQUIRED_TABLES:
                # Table names come from the internal REQUIRED_TABLES
                # tuple, never from user input, so the f-string is safe
                # (PRAGMA does not support bound parameters for the
                # table name).
                cursor = connection.execute(
                    f"PRAGMA table_info({table_name})"
                )
                columns = [row[1] for row in cursor.fetchall()]
                if not columns:
                    raise DatabaseError(
                        f"Required table '{table_name}' is missing from "
                        f"the database at {db_path}. Run "
                        "initialize_database first."
                    )
                table_columns[table_name] = columns
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not inspect the database at {db_path}: {error}"
        ) from error

    # Presence check (not order): every expected column must exist.
    for table_name, expected in EXPECTED_COLUMNS.items():
        existing = set(table_columns[table_name])
        missing = set(expected) - existing
        if missing:
            raise DatabaseError(
                f"Table '{table_name}' is missing expected columns: "
                f"{sorted(missing)}."
            )

    return table_columns
