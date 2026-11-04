"""Reusable SQLite connection management (TASK-011).

Every database call in the application should go through the helpers in
this module so that connection settings are applied consistently:

- Foreign key enforcement (``PRAGMA foreign_keys = ON``).
- Row access by column name (``sqlite3.Row``).
- Commits on success, rollback on error, close in all cases.

Repositories receive a connection returned by :func:`connect` (or a
``ConnectionContext`` instance) and never open SQLite connections
themselves.
"""

import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Type

from smartstock.database.initialization import initialize_database


class DatabaseError(Exception):
    """Raised when a database connection cannot be established or use fails."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a configured SQLite connection.

    The database file is created with the standard schema when it does
    not exist yet, mirroring the initialization task requirements.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Connection with foreign keys enabled and row factory set to
        ``sqlite3.Row``. Callers are responsible for closing it; see
        :func:`session` for automatic cleanup.

    Raises:
        DatabaseError: If the file cannot be opened or configured.
    """
    db_path = Path(db_path)
    if not db_path.is_file():
        try:
            initialize_database(db_path)
        except Exception as error:
            raise DatabaseError(
                f"Could not prepare the database at {db_path}: {error}",
                cause=error,
            ) from error

    try:
        connection = sqlite3.connect(db_path)
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not open the database at {db_path}: {error}",
            cause=error,
        ) from error

    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


class ConnectionContext:
    """Context manager that commits, rolls back, and closes safely.

    Usage::

        with session(db_path) as conn:
            conn.execute(...)

    The context commits when the block exits normally and rolls back
    when an exception propagates. The connection is always closed.
    """

    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self._connection = connect(self._db_path)
        return self._connection

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if self._connection is None:
            return False
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._connection.close()
            self._connection = None
        # Do not suppress the original exception.
        return False


def session(db_path: Path) -> ConnectionContext:
    """Create a managed database session (context manager)."""
    return ConnectionContext(db_path)
