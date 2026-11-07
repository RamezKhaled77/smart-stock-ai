"""Historical CSV import service (TASK-023 preview; TASK-024 persistence).

Orchestrates the historical import pipeline (DEC-052, DEC-055):

1. Read and validate the uploaded file (TASK-022 domain logic).
2. Build a preview summary before anything is written (DEC-054).
3. Persist accepted rows in a single all-or-nothing transaction
   (TASK-024) through the historical repository.

The service is the only layer besides pages/ML that pages may call. It
contains no SQL itself — persistence goes through the historical
repositories, and every page call re-validates the file from its bytes
(uploaded files are never trusted from stale UI state).
"""

import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path

import config

from smartstock.database.connection import session
from smartstock.database.initialization import initialize_database
from smartstock.domain import csv_import
from smartstock.domain.csv_import import (
    CsvFileError,
    CsvStructureError,
    RowAnalysis,
)
from smartstock.repositories import historical_repository
from smartstock.repositories.historical_repository import (
    DuplicateImportError as _RepoDuplicateImportError,
)

# Maximum number of example problems and sample rows shown in previews
# (CSV Import Specification §13: summarize large files, show examples).
MAX_EXAMPLES = 5
MAX_SAMPLE_ROWS = 5

# Pages import this exception type from the service, one stable path.
DuplicateImportError = _RepoDuplicateImportError


class ImportRejectedError(ValueError):
    """The file has no importable rows, so nothing was stored."""


@dataclass
class ImportResult:
    """Outcome of one executed historical import (spec §14 data)."""

    batch_id: int
    filename: str
    store: int
    total_rows: int
    imported_rows: int
    out_of_store_rows: int
    rejected_rows: int
    duplicate_rows: int
    first_date: str | None
    last_date: str | None
    created_at: str

    @property
    def date_range(self) -> tuple | None:
        if self.first_date is None or self.last_date is None:
            return None
        return (self.first_date, self.last_date)


@dataclass
class ImportPreview:
    """Summary of one historical CSV file before importing.

    Row counts follow :class:`smartstock.domain.csv_import.RowAnalysis`;
    ``invalid_in_scope_rows`` counts rejected rows that would have been
    in the selected store's scope had they been valid — they are errors,
    unlike out-of-store rows (DEC-015).
    """

    filename: str
    file_size_bytes: int
    sha256_fingerprint: str
    store: int
    total_rows: int
    valid_row_count: int
    out_of_store_rows: int
    in_scope_rows: int
    rejected_rows: list = field(default_factory=list)
    rejected_truncated: bool = False
    rejected_total: int = 0
    duplicate_rows: list = field(default_factory=list)
    duplicate_truncated: bool = False
    duplicate_total: int = 0
    date_range: tuple | None = None
    sample_rows: list = field(default_factory=list)

    @property
    def invalid_in_scope_rows(self) -> int:
        """Rows rejected for invalid values (full count, not examples)."""
        return self.rejected_total

    @property
    def duplicate_row_count(self) -> int:
        """Within-file duplicates (full count, not examples)."""
        return self.duplicate_total

    @property
    def importable(self) -> bool:
        """Whether there is anything to import at all."""
        return self.valid_row_count > 0


def preview_import(file) -> ImportPreview:
    """Validate a historical CSV file and build the preview summary.

    Nothing is written to the database. The returned fingerprint is the
    SHA-256 hash of the file bytes that persistence (TASK-024) will
    check against ``import_batches`` before importing.

    Args:
        file: Path or file-like object holding the CSV content.

    Returns:
        The :class:`ImportPreview` summary.

    Raises:
        CsvFileError: If the file cannot be read as CSV.
        CsvStructureError: If required columns are missing or unexpected
            columns are present.
    """
    raw, analysis = _parse_import_file(file)
    return _preview_from_analysis(raw, analysis, _file_name(file))


def execute_import(file, db_path: Path | None = None) -> ImportResult:
    """Validate a historical CSV file and store it all-or-nothing.

    The full validation pipeline runs on the file's current bytes right
    before writing, so the data stored is exactly what the validation
    accepted at execution time — a file cannot be imported based on a
    stale preview. The write itself is one transaction: the batch
    metadata row and the accepted rows either all commit or all roll
    back (DEC-054). Inventory and operational sales are untouched
    (BR-014, DEC-016).

    Args:
        file: Path or file-like object holding the CSV content.
        db_path: Database to store in (default ``config.DATABASE_PATH``).

    Returns:
        The :class:`ImportResult` describing what was stored.

    Raises:
        CsvFileError: If the file cannot be read as CSV.
        CsvStructureError: If required columns are missing or unexpected
            columns are present.
        ImportRejectedError: If the file validly contains no importable
            rows for the selected store (DEC-015).
        DuplicateImportError: If a file with the same SHA-256
            fingerprint is already recorded (DEC-053).
        DatabaseError: If storage fails; no partial data is left.
    """
    raw, analysis = _parse_import_file(file)
    preview = _preview_from_analysis(raw, analysis, _file_name(file))
    if not preview.importable:
        raise ImportRejectedError(
            "Nothing to import: the file contains no valid rows for "
            f"store {csv_import.DEFAULT_STORE}."
        )

    if db_path is None:
        db_path = Path(config.DATABASE_PATH)
    # Idempotent: an existing database is untouched except that new
    # schema objects (the import tables) are created if missing.
    initialize_database(db_path)

    return _store_import(preview, analysis, db_path)


def get_import_summary(db_path: Path | None = None) -> dict:
    """Summarize all recorded import batches (TASK-025 display data).

    Args:
        db_path: Database to read (default ``config.DATABASE_PATH``).

    Returns:
        Dictionary with ``batches`` (newest-first batch dicts from the
        repository) and ``total_records`` (stored historical rows).

    Raises:
        DatabaseError: If the database cannot be read.
    """
    if db_path is None:
        db_path = Path(config.DATABASE_PATH)
    # Idempotent so a database created before DEC-052 gains the import
    # tables before this summary reads them.
    initialize_database(db_path)
    with session(db_path) as connection:
        return {
            "batches": historical_repository.get_import_batches(connection),
            "total_records": historical_repository.count_historical_rows(
                connection
            ),
        }


def _parse_import_file(file) -> tuple:
    """Read, structurally validate, and row-analyze one CSV file."""
    raw = _read_file_bytes(file)
    frame = csv_import.read_csv_file(io.BytesIO(raw))
    csv_import.validate_file_structure(frame)
    return raw, csv_import.analyze_rows(frame)


def _preview_from_analysis(
    raw: bytes, analysis: RowAnalysis, filename: str
) -> ImportPreview:
    """Translate validated file content into the preview summary."""
    valid = analysis.valid_rows
    sample = valid.head(MAX_SAMPLE_ROWS) if len(valid) else valid
    return ImportPreview(
        filename=filename,
        file_size_bytes=len(raw),
        sha256_fingerprint=hashlib.sha256(raw).hexdigest(),
        store=csv_import.DEFAULT_STORE,
        total_rows=analysis.total_rows,
        valid_row_count=int(len(valid)),
        out_of_store_rows=analysis.out_of_store_rows,
        in_scope_rows=analysis.in_scope_rows,
        rejected_rows=analysis.rejected_rows[:MAX_EXAMPLES],
        rejected_truncated=len(analysis.rejected_rows) > MAX_EXAMPLES,
        rejected_total=len(analysis.rejected_rows),
        duplicate_rows=analysis.duplicate_rows[:MAX_EXAMPLES],
        duplicate_truncated=len(analysis.duplicate_rows) > MAX_EXAMPLES,
        duplicate_total=len(analysis.duplicate_rows),
        date_range=analysis.date_range,
        sample_rows=sample.to_dict(orient="records"),
    )


def _store_import(
    preview: ImportPreview, analysis: RowAnalysis, db_path: Path
) -> ImportResult:
    """Write the validated import in one transaction (DEC-054)."""
    rows = [
        (
            int(row["item"]),
            str(row["date"]),
            int(row["sales"]),
        )
        for row in analysis.valid_rows.to_dict(orient="records")
    ]
    meta = {
        "source_filename": preview.filename,
        "file_sha256": preview.sha256_fingerprint,
        "store": preview.store,
        "total_rows": analysis.total_rows,
        "out_of_store_rows": analysis.out_of_store_rows,
        "rejected_rows": len(analysis.rejected_rows),
        "duplicate_rows": len(analysis.duplicate_rows),
        "first_date": analysis.date_range[0]
        if analysis.date_range
        else None,
        "last_date": analysis.date_range[1]
        if analysis.date_range
        else None,
    }
    with session(db_path) as connection:
        batch = historical_repository.create_import_batch(
            connection, meta, rows
        )
    return _result_from_batch(preview, batch)


def _result_from_batch(preview: ImportPreview, batch: dict) -> ImportResult:
    """Translate the stored batch into the page-facing result."""
    return ImportResult(
        batch_id=batch["id"],
        filename=preview.filename,
        store=batch["store"],
        total_rows=batch["total_rows"],
        imported_rows=batch["imported_rows"],
        out_of_store_rows=batch["out_of_store_rows"],
        rejected_rows=batch["rejected_rows"],
        duplicate_rows=batch["duplicate_rows"],
        first_date=batch["first_date"],
        last_date=batch["last_date"],
        created_at=batch["created_at"],
    )


def _read_file_bytes(file) -> bytes:
    """Return the file content as bytes for hashing and parsing."""
    if isinstance(file, (str, Path)):
        try:
            return Path(file).read_bytes()
        except OSError as error:
            raise CsvFileError(
                f"The file could not be read: {error}"
            ) from error
    try:
        data = file.read()
    except OSError as error:
        raise CsvFileError(f"The file could not be read: {error}") from error
    # Leave the stream readable again for any later re-parse.
    seek = getattr(file, "seek", None)
    if seek is not None:
        seek(0)
    return data


def _file_name(file) -> str:
    """Best-effort display name of an uploaded file."""
    if isinstance(file, (str, Path)):
        return Path(file).name
    name = getattr(file, "name", None)
    if isinstance(name, str) and name:
        return name
    return "uploaded file"
