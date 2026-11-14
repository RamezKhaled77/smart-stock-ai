"""CSV file and row validation for historical imports (TASK-022).

Pure logic: parses an uploaded CSV file and reports which rows would be
accepted for a historical import without touching the database or the
UI. Implements the file and data validation requirements of the CSV
Import Specification (§6, §7) and the DEC-015 store filter.

Error layers (CSV Import Specification §13):

- :class:`CsvFileError` — file-level problems (empty, unreadable).
- :class:`CsvStructureError` — column-level problems (missing or
  unexpected columns).
- Row-level problems are *not* exceptions: they are collected into the
  :class:`RowAnalysis` report so a mixed-quality file can be previewed
  before any write happens (DEC-054 validates the whole file first).
"""

from dataclasses import dataclass, field

import pandas as pd

from smartstock.i18n import t

# The Kaggle dataset format (CSV Import Specification §3).
REQUIRED_COLUMNS = ("date", "store", "item", "sales")

# Store selected for the single-store workflow (DEC-015).
DEFAULT_STORE = 1


class CsvFileError(Exception):
    """The file itself could not be read as CSV data."""


class CsvStructureError(Exception):
    """The file's columns do not match the historical import format."""


@dataclass
class RowAnalysis:
    """Validation report for one uploaded historical CSV file.

    Attributes:
        total_rows: Data rows in the file (header excluded).
        out_of_store_rows: Rows whose ``store`` is not the selected
            store. They are in scope for another store, not errors
            (DEC-015 filters a single store), so they are skipped and
            reported, never imported.
        rejected_rows: List of ``(data_row_number, reason)`` for rows
            with invalid values.
        duplicate_rows: List of ``(data_row_number, description)`` for
            within-file duplicates — rows repeating a ``(item, date)``
            combination that already appears earlier in the file.
        valid_rows: Accepted rows for the selected store with wall-clock
            values normalized (dates as ``YYYY-MM-DD`` strings, numeric
            columns as integers).
        date_range: ``(min_date, max_date)`` of the accepted rows, or
            ``None`` when no rows are accepted.
    """

    total_rows: int = 0
    out_of_store_rows: int = 0
    rejected_rows: list = field(default_factory=list)
    duplicate_rows: list = field(default_factory=list)
    valid_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    date_range: tuple | None = None

    @property
    def invalid_row_count(self) -> int:
        return len(self.rejected_rows)

    @property
    def duplicate_row_count(self) -> int:
        return len(self.duplicate_rows)

    @property
    def in_scope_rows(self) -> int:
        """Rows that belong to the selected store at all."""
        return self.total_rows - self.out_of_store_rows


def read_csv_file(file) -> pd.DataFrame:
    """Read an uploaded CSV file with strict, validation-friendly types.

    The file is parsed with every column as a string so malformed values
    surface as row-level validation problems instead of silently
    becoming floats or NaN.

    Args:
        file: Path or file-like object (for example ``io.BytesIO`` from
            a Streamlit ``st.file_uploader``).

    Returns:
        The parsed CSV frame.

    Raises:
        CsvFileError: If the file is empty, unreadable, or not valid CSV.
    """
    try:
        frame = pd.read_csv(
            file,
            dtype=str,
            # Keep truly empty cells as empty strings rather than NaN so
            # row validation can describe them as missing values.
            keep_default_na=False,
        )
    except pd.errors.EmptyDataError as error:
        raise CsvFileError(t("svc.imports.file_empty")) from error
    except UnicodeDecodeError as error:
        raise CsvFileError(
            t("svc.imports.file_not_text")
        ) from error
    except pd.errors.ParserError as error:
        raise CsvFileError(
            t("svc.imports.file_malformed", error=error)
        ) from error
    except OSError as error:
        raise CsvFileError(
            t("svc.imports.file_unreadable", error=error)
        ) from error

    if frame.empty:
        raise CsvFileError(t("svc.imports.file_no_rows"))
    if frame.columns.duplicated().any():
        raise CsvStructureError(
            t(
                "svc.imports.duplicate_columns",
                columns=sorted(
                    set(frame.columns[frame.columns.duplicated()])
                ),
            )
        )
    return frame


def validate_file_structure(frame: pd.DataFrame) -> None:
    """Check that the frame has exactly the required columns.

    Raises:
        CsvStructureError: If required columns are missing or unexpected
            extra columns are present. Extra columns are rejected in v1
            so the file's meaning is never guessed.
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise CsvStructureError(
            t(
                "svc.imports.missing_columns",
                missing=missing,
                required=list(REQUIRED_COLUMNS),
            )
        )
    extra = [column for column in frame.columns if column not in REQUIRED_COLUMNS]
    if extra:
        raise CsvStructureError(
            t(
                "svc.imports.unexpected_columns",
                extra=extra,
                required=list(REQUIRED_COLUMNS),
            )
        )


def analyze_rows(
    frame: pd.DataFrame, store: int = DEFAULT_STORE
) -> RowAnalysis:
    """Validate every data row and classify the results.

    Rows for other stores are counted as out of scope (DEC-015), rows
    with invalid values are reported with reasons, and within-file
    duplicate ``(item, date)`` combinations are skipped so a repeated
    file section does not crash the database level.

    Args:
        frame: Parsed CSV frame with exactly the required columns.
        store: Store whose rows are in scope (default per DEC-015).

    Returns:
        The :class:`RowAnalysis` report.
    """
    analysis = RowAnalysis(total_rows=len(frame))
    if analysis.total_rows == 0:
        return analysis

    # Column-level masks first; combined per row afterwards.
    date_bad = bad_date_mask(frame)
    store_bad = bad_integer_mask(frame, "store", minimum=1)
    item_bad = bad_integer_mask(frame, "item", minimum=1)
    sales_bad = bad_integer_mask(frame, "sales", minimum=0)
    invalid = date_bad | store_bad | item_bad | sales_bad

    analysis.rejected_rows = collect_row_problems(
        frame,
        {
            "date": (date_bad, t("svc.imports.bad_date")),
            "store": (store_bad, t("svc.imports.bad_store")),
            "item": (item_bad, t("svc.imports.bad_item")),
            "sales": (sales_bad, t("svc.imports.bad_sales")),
        },
    )

    in_scope = ~invalid & (numeric_column(frame, "store") == store)
    analysis.out_of_store_rows = int((~invalid & ~in_scope).sum())

    candidates = frame[in_scope].copy()

    # Within-file duplicates: a repeated (item, date) pair keeps its
    # first occurrence; later repeats are skipped and reported.
    duplicate_mask = candidates.duplicated(
        subset=["item", "date"], keep="first"
    )
    analysis.duplicate_rows = [
        (
            _data_row_number(frame, index),
            t(
                "svc.imports.duplicate_row",
                item=candidates["item"][index],
                date=candidates["date"][index],
            ),
        )
        for index in candidates[duplicate_mask].index
    ]

    valid = candidates[~duplicate_mask].drop(columns=[]).copy()
    _normalize_valid_rows(valid)
    analysis.valid_rows = valid

    if len(valid) > 0:
        analysis.date_range = (
            valid["date"].min(), valid["date"].max(),
        )
    return analysis


def _normalize_valid_rows(valid: pd.DataFrame) -> None:
    """Convert validated columns to their storage types (in place)."""
    for column in ("store", "item", "sales"):
        valid[column] = pd.to_numeric(valid[column]).astype(int)


def _data_row_number(frame: pd.DataFrame, index) -> int:
    """Translate a DataFrame index to a human-friendly data row number."""
    return frame.index.get_loc(index) + 1


def collect_row_problems(frame: pd.DataFrame, problem_specs: dict) -> list:
    """Build ``(row_number, reason)`` pairs for all invalid rows."""
    rows = []
    invalid_any = None
    for _, (mask, _) in problem_specs.items():
        invalid_any = mask if invalid_any is None else (invalid_any | mask)
    for index in frame[invalid_any].index:
        problems = []
        for column, (mask, reason) in problem_specs.items():
            if mask[index]:
                value = frame[column][index]
                problems.append(
                    t(
                        "svc.imports.row_problem",
                        column=column,
                        value=value,
                        reason=reason,
                    )
                    if value != ""
                    else t("svc.imports.row_missing", column=column)
                )
        rows.append((_data_row_number(frame, index), "; ".join(problems)))
    return rows


def numeric_column(frame: pd.DataFrame, column: str) -> pd.Series:
    """Return the column as floats (NaN where unparseable)."""
    return pd.to_numeric(frame[column], errors="coerce")


def bad_date_mask(frame: pd.DataFrame) -> pd.Series:
    """True where a date value is not a valid ``YYYY-MM-DD`` date."""
    parsed = pd.to_datetime(
        frame["date"], format="%Y-%m-%d", errors="coerce"
    )
    return parsed.isna()


def bad_integer_mask(
    frame: pd.DataFrame, column: str, minimum: int
) -> pd.Series:
    """True where a value is not an integer ≥ ``minimum``.

    Covers missing values, non-numeric text, fractional numbers, and
    too-small values — all common CSV row problems (spec §7).
    """
    numeric = numeric_column(frame, column)
    return numeric.isna() | (numeric != numeric.round()) | (numeric < minimum)
