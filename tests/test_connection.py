"""Tests for database connection management (TASK-011).

Uses an already-initialized temporary database; never touches the real
``data/smartstock.db``.
"""

import sqlite3
from pathlib import Path

import pytest

from smartstock.database import connection as connection_module
from smartstock.database.initialization import initialize_database
from smartstock.database.schema import EXPECTED_COLUMNS
from smartstock.database.connection import ConnectionContext, connect, session


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


PRODUCT = (
    "INSERT INTO products (name, sku, created_at, updated_at) "
    "VALUES ('Item A', 'SKU-001', '2026-11-04T00:00:01Z', "
    "'2026-11-04T00:00:01Z')"
)


class TestConnect:
    """Connection settings applied consistently."""

    def test_returns_open_connection_with_row_factory(
        self, db_path: Path
    ) -> None:
        connection = connect(db_path)
        try:
            assert isinstance(connection, sqlite3.Connection)
            assert connection.row_factory is sqlite3.Row
            foreign_keys = connection.execute(
                "PRAGMA foreign_keys"
            ).fetchone()[0]
            assert foreign_keys == 1
        finally:
            connection.close()

    def test_creates_database_when_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "fresh.db"
        connection = connect(path)
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            table_names = {row["name"] for row in tables}
        finally:
            connection.close()
        assert set(EXPECTED_COLUMNS) <= table_names

    def test_open_error_wrapped_in_database_error(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        path = tmp_path / "broken.db"
        path.write_text("this is not a sqlite database")

        original_connect = connection_module.sqlite3.connect

        def fake_connect(*args, **kwargs):
            raise sqlite3.OperationalError("file is not a database")

        monkeypatch.setattr(
            connection_module.sqlite3, "connect", fake_connect
        )
        with pytest.raises(
            connection_module.DatabaseError, match="Could not open"
        ):
            connect(path)
        monkeypatch.setattr(
            connection_module.sqlite3, "connect", original_connect
        )


class TestSession:
    """Commit, rollback, and close behavior."""

    def test_commits_on_success(self, db_path: Path) -> None:
        with session(db_path) as conn:
            conn.execute(PRODUCT)

        connection = connect(db_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]
        finally:
            connection.close()
        assert count == 1

    def test_rolls_back_on_error(self, db_path: Path) -> None:
        with pytest.raises(ValueError):
            with session(db_path) as conn:
                conn.execute(PRODUCT)
                raise ValueError("simulated failure")

        connection = connect(db_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]
        finally:
            connection.close()
        assert count == 0

    def test_closes_connection_even_without_error(self, db_path: Path) -> None:
        with session(db_path) as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.total_changes >= 0
        # A closed connection raises when used again.
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_returns_connection_context_class(
        self, db_path: Path
    ) -> None:
        context = session(db_path)
        assert isinstance(context, ConnectionContext)
