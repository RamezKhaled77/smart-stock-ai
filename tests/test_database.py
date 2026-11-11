"""Tests for database initialization (TASK-010) and connection (TASK-011).

Uses a temporary database file per test; never touches the real
``data/smartstock.db``.
"""

import sqlite3
from pathlib import Path

import pytest

from smartstock.database.initialization import (
    DatabaseError,
    initialize_database,
    verify_tables,
)
from smartstock.database.schema import EXPECTED_COLUMNS


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with foreign key enforcement enabled.

    The PRAGMA is per-connection in SQLite, so tests that simulate
    application connections must enable it themselves.
    """
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Initialize a fresh database in the test's temporary directory."""
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


class TestInitializeDatabase:
    """Initialization behavior: creation, idempotency, verification."""

    def test_creates_database_and_tables(self, db_path: Path) -> None:
        columns = verify_tables(db_path)

        assert sorted(columns) == sorted(EXPECTED_COLUMNS)
        for table_name, expected in EXPECTED_COLUMNS.items():
            assert set(columns[table_name]) >= set(expected)

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "test.db"
        initialize_database(nested)
        assert nested.is_file()

    def test_reinitialization_is_idempotent(self, db_path: Path) -> None:
        # Data written before a repeated initialization must survive.
        connection = _connect(db_path)
        connection.execute(
            "INSERT INTO products (name, sku, created_at, updated_at) "
            "VALUES ('Item A', 'SKU-001', '2026-11-04T00:00:00Z', "
            "'2026-11-04T00:00:00Z')"
        )
        connection.commit()
        connection.close()

        initialize_database(db_path)  # repeat on purpose
        verify_tables(db_path)

        connection = _connect(db_path)
        count = connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        connection.close()
        assert count == 1

    def test_legacy_database_gets_dec060_column(self, tmp_path) -> None:
        """Additive migration: a pre-DEC-060 products table upgrades.

        Simulates a database created before the mapping decision by
        building the products table without the column, then letting
        ``initialize_database`` apply its guarded ALTER TABLE.
        """
        db_path = tmp_path / "legacy.db"
        connection = _connect(db_path)
        connection.execute(
            "CREATE TABLE products ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "name TEXT NOT NULL, sku TEXT NOT NULL UNIQUE,"
            "category TEXT NOT NULL DEFAULT '',"
            "current_stock INTEGER NOT NULL DEFAULT 0,"
            "lead_time_days INTEGER NOT NULL DEFAULT 3,"
            "safety_stock INTEGER NOT NULL DEFAULT 0,"
            "is_active INTEGER NOT NULL DEFAULT 1,"
            "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO products (name, sku, created_at, updated_at) "
            "VALUES ('Legacy', 'SKU-LEG', '2026-01-01T00:00:00Z', "
            "'2026-01-01T00:00:00Z')"
        )
        connection.commit()
        connection.close()

        initialize_database(db_path)
        columns = verify_tables(db_path)["products"]
        assert "dataset_item_id" in columns
        # Existing row survives; its link is NULL until set.
        connection = _connect(db_path)
        row = connection.execute(
            "SELECT name, dataset_item_id FROM products"
        ).fetchone()
        connection.close()
        assert row[0] == "Legacy"
        assert row[1] is None

    def test_missing_database_raises_on_verify(self, tmp_path: Path) -> None:
        with pytest.raises(DatabaseError, match="not found"):
            verify_tables(tmp_path / "never_created.db")

    def test_empty_database_is_missing_tables(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.db"
        connection = sqlite3.connect(path)
        connection.close()

        with pytest.raises(DatabaseError, match="missing"):
            verify_tables(path)


class TestSchemaConstraints:
    """Integrity rules from the approved schema document."""

    def _product(self, **overrides) -> str:
        """Build an INSERT statement with per-test overrides."""
        defaults = {
            "name": "'Item A'",
            "sku": "'SKU-001'",
            "current_stock": 10,
            "created_at": "'2026-11-04T00:00:00Z'",
            "updated_at": "'2026-11-04T00:00:00Z'",
        }
        defaults.update(overrides)
        columns = ", ".join(defaults)
        values = ", ".join(str(v) for v in defaults.values())
        return f"INSERT INTO products ({columns}) VALUES ({values})"

    def test_negative_stock_is_rejected(self, db_path: Path) -> None:
        connection = _connect(db_path)
        with pytest.raises(sqlite3.IntegrityError, match="(?i)check"):
            connection.execute(self._product(current_stock=-1))

    def test_unknown_is_active_value_is_rejected(self, db_path: Path) -> None:
        connection = _connect(db_path)
        with pytest.raises(sqlite3.IntegrityError, match="(?i)check"):
            connection.execute(self._product(is_active=2))

    def test_negative_lead_time_is_rejected(self, db_path: Path) -> None:
        connection = _connect(db_path)
        with pytest.raises(sqlite3.IntegrityError, match="(?i)check"):
            connection.execute(self._product(lead_time_days=-3))

    def test_duplicate_sku_is_rejected(self, db_path: Path) -> None:
        connection = _connect(db_path)
        connection.execute(self._product())
        with pytest.raises(sqlite3.IntegrityError, match="(?i)unique"):
            connection.execute(self._product(sku="'SKU-DUP'"))
            connection.execute(
                "INSERT INTO products (name, sku, created_at, updated_at) "
                "VALUES ('Item B', 'SKU-001', '2026-11-04T00:00:00Z', "
                "'2026-11-04T00:00:00Z')"
            )

    def test_zero_or_negative_sale_quantity_is_rejected(
        self, db_path: Path
    ) -> None:
        connection = _connect(db_path)
        connection.execute(self._product())
        with pytest.raises(sqlite3.IntegrityError, match="(?i)check"):
            connection.execute(
                "INSERT INTO sales (product_id, quantity, sale_date, "
                "created_at) VALUES (1, 0, '2026-11-04', "
                "'2026-11-04T00:00:00Z')"
            )

    def test_sale_for_unknown_product_is_rejected(self, db_path: Path) -> None:
        connection = _connect(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sales (product_id, quantity, sale_date, "
                "created_at) VALUES (999, 1, '2026-11-04', "
                "'2026-11-04T00:00:00Z')"
            )
