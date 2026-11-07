"""Historical CSV import service (TASK-023 preview; persistence TASK-024).

Orchestrates the historical import pipeline (DEC-052, DEC-055):

1. Read and validate the uploaded file (TASK-022 domain logic).
2. Build a preview summary before anything is written (DEC-054).
3. Persist accepted rows in a single all-or-nothing transaction
   (TASK-024).

The service is the only layer besides pages/ML that pages may call. It
contains no SQL itself — persistence goes through the historical
repositories.
"""

import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path

from smartstock.domain import csv_import
from smartstock.domain.csv_import import (
    CsvFileError,
    CsvStructureError,
    RowAnalysis,
)

# Maximum number of example problems and sample rows shown in previews
# (CSV Import Specification §13: summarize large files, show examples).
MAX_EXAMPLES = 5
MAX_SAMPLE_ROWS = 5


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
    raw = _read_file_bytes(file)
    frame = csv_import.read_csv_file(io.BytesIO(raw))
    csv_import.validate_file_structure(frame)
    analysis: RowAnalysis = csv_import.analyze_rows(frame)

    sample = analysis.valid_rows.head(MAX_SAMPLE_ROWS) if len(
        analysis.valid_rows
    ) else analysis.valid_rows
    return ImportPreview(
        filename=_file_name(file),
        file_size_bytes=len(raw),
        sha256_fingerprint=hashlib.sha256(raw).hexdigest(),
        store=csv_import.DEFAULT_STORE,
        total_rows=analysis.total_rows,
        valid_row_count=int(len(analysis.valid_rows)),
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
