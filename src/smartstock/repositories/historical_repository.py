"""Historical repository (TASK-024).

SQL access for the historical import tables (DEC-052):

- ``import_batches`` — one metadata row per import run, including the
  SHA-256 file fingerprint used to reject exact re-uploads (DEC-053).
- ``historical_sales`` — accepted dataset observations keyed by the
  dataset's ``item`` number, protected against overlapping imports by
  the ``UNIQUE (item, sale_date)`` constraint.

Historical rows never touch operational inventory or the ``sales``
table (BR-014, DEC-016). Functions require an open connection, like the
other repositories.
"""

import sqlite3

from smartstock.database.connection import DatabaseError
from smartstock.utils.dates import utc_now_iso


class DuplicateImportError(ValueError):
    """Raised when a file with a recorded fingerprint is re-uploaded.

    Inherits from ``ValueError`` so generic invalid-input handling in
    pages keeps working, while the UI can give this case its own,
    specific message. Carries the original import's details.
    """

    def __init__(
        self,
        original_batch_id: int,
        original_filename: str,
        original_created_at: str,
    ):
        self.original_batch_id = original_batch_id
        self.original_filename = original_filename
        self.original_created_at = original_created_at
        super().__init__(
            "This exact file was already imported on "
            f"{original_created_at} as '{original_filename}', so nothing "
            "was imported again. Upload a different file if you want to "
            "import new records."
        )


def create_import_batch(
    connection: sqlite3.Connection,
    meta: dict,
    rows: list,
    commit: bool = True,
) -> dict:
    """Store one import batch and all its accepted rows (all-or-nothing).

    Steps inside one transaction:

    1. Reject files whose SHA-256 fingerprint is already recorded
       (DEC-053's friendly, fingerprint-level check).
    2. Find which rows already exist in ``historical_sales`` from other
       batches and skip them (counted with the within-file duplicates
       in ``duplicate_rows``).
    3. Insert the batch metadata row, then bulk-insert the remaining
       rows.

    Args:
        connection: Open database connection.
        meta: Batch metadata with ``source_filename``,
            ``file_sha256``, ``store``, ``total_rows``,
            ``out_of_store_rows``, ``rejected_rows``,
            ``duplicate_rows`` (within-file), ``first_date``,
            ``last_date``.
        rows: Accepted rows as ``(item, sale_date, quantity)`` tuples
            (from :func:`smartstock.domain.csv_import.analyze_rows`).
        commit: Commit immediately (default). Pass False to keep the
            transaction open; the caller's session manager commits.

    Returns:
        The stored batch as a dictionary including ``imported_rows``
        and ``duplicate_rows`` with the database-level skips added.

    Raises:
        DuplicateImportError: If the fingerprint is already recorded.
        DatabaseError: If the batch row or rows cannot be stored; no
            partial data is left behind.
    """
    try:
        existing = find_batch_by_fingerprint(
            connection, meta["file_sha256"]
        )
        if existing is not None:
            raise DuplicateImportError(
                existing["id"],
                existing["source_filename"],
                existing["created_at"],
            )

        # Rows already stored by other batches are skipped and counted
        # (DEC-053); the UNIQUE constraint would catch them anyway.
        known_keys = _existing_keys(connection)
        filtered_rows = []
        for row in rows:
            key = (int(row[0]), str(row[1]))
            if key in known_keys:
                continue
            filtered_rows.append(row)
        database_duplicate_rows = len(rows) - len(filtered_rows)

        now = _utc_now()
        batch_values = (
            meta["source_filename"],
            meta["file_sha256"],
            int(meta["store"]),
            int(meta["total_rows"]),
            int(meta["out_of_store_rows"]),
            int(meta["rejected_rows"]),
            int(meta["duplicate_rows"]) + database_duplicate_rows,
            len(filtered_rows),
            meta["first_date"],
            meta["last_date"],
            now,
        )
        cursor = connection.execute(
            "INSERT INTO import_batches (source_filename, file_sha256, "
            "store, total_rows, out_of_store_rows, rejected_rows, "
            "duplicate_rows, imported_rows, first_date, last_date, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            batch_values,
        )
        batch_id = cursor.lastrowid
        if filtered_rows:
            connection.executemany(
                "INSERT INTO historical_sales (item, sale_date, "
                "quantity, import_batch_id) VALUES (?, ?, ?, ?)",
                [(row[0], row[1], row[2], batch_id) for row in filtered_rows],
            )
        if commit:
            connection.commit()
    except DuplicateImportError:
        raise
    except sqlite3.IntegrityError as error:
        raise DatabaseError(
            f"Could not store the import: {error}", cause=error
        ) from error
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not store the import: {error}", cause=error
        ) from error

    return _batch_to_dict(batch_values, batch_id)


def find_batch_by_fingerprint(
    connection: sqlite3.Connection, sha256: str
) -> dict | None:
    """Return the batch stored for this file fingerprint, if any."""
    try:
        cursor = connection.execute(
            "SELECT id, source_filename, file_sha256, store, total_rows, "
            "out_of_store_rows, rejected_rows, duplicate_rows, "
            "imported_rows, first_date, last_date, created_at "
            "FROM import_batches WHERE file_sha256 = ?",
            (sha256,),
        )
        row = cursor.fetchone()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not look up the import fingerprint: {error}",
            cause=error,
        ) from error
    if row is None:
        return None
    return dict(row)


def get_import_batches(connection: sqlite3.Connection) -> list:
    """List import batches, newest first."""
    try:
        cursor = connection.execute(
            "SELECT id, source_filename, file_sha256, store, total_rows, "
            "out_of_store_rows, rejected_rows, duplicate_rows, "
            "imported_rows, first_date, last_date, created_at "
            "FROM import_batches ORDER BY id DESC"
        )
        rows = cursor.fetchall()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not read import batches: {error}", cause=error
        ) from error
    return [dict(row) for row in rows]


def count_historical_rows(connection: sqlite3.Connection) -> int:
    """Total number of stored historical observations."""
    try:
        cursor = connection.execute(
            "SELECT COUNT(*) FROM historical_sales"
        )
        row = cursor.fetchone()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not count historical records: {error}", cause=error
        ) from error
    return int(row[0])


def _existing_keys(connection: sqlite3.Connection) -> set:
    """Set of ``(item, sale_date)`` keys already stored."""
    try:
        cursor = connection.execute(
            "SELECT item, sale_date FROM historical_sales"
        )
        rows = cursor.fetchall()
    except sqlite3.Error as error:
        raise DatabaseError(
            f"Could not read existing historical rows: {error}",
            cause=error,
        ) from error
    return {(int(row["item"]), str(row["sale_date"])) for row in rows}


def _batch_to_dict(values: tuple, batch_id: int) -> dict:
    """Build the returned batch dictionary from the inserted values."""
    columns = (
        "source_filename",
        "file_sha256",
        "store",
        "total_rows",
        "out_of_store_rows",
        "rejected_rows",
        "duplicate_rows",
        "imported_rows",
        "first_date",
        "last_date",
        "created_at",
    )
    batch = dict(zip(columns, values))
    batch["id"] = batch_id
    return batch


def _utc_now() -> str:
    """Current UTC ISO timestamp (delegated to the shared helper)."""
    return utc_now_iso()
