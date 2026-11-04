"""Historical dataset loading, validation, and preprocessing.

This module implements the preprocessing workflow defined in
``docs/03-data/data-preprocessing.md`` for the historical sales dataset
(``data/raw/train.csv``):

1. Load the CSV safely and check for file errors.
2. Validate required columns and value types.
3. Parse dates and validate sales values.
4. Detect duplicate records and date gaps per store-item series.
5. Filter to the selected store and chronologically sort (DEC-015).

The module must stay independent of Streamlit and the operational
database; it works on plain pandas DataFrames.
"""

from pathlib import Path
import pandas as pd

# Required columns per docs/03-data/data-preprocessing.md section 5.
REQUIRED_COLUMNS = ["date", "store", "item", "sales"]


class DatasetError(Exception):
    """Raised when the historical dataset cannot be loaded or is invalid."""


def load_historical_dataset(csv_path: Path) -> pd.DataFrame:
    """Load the historical sales CSV into a DataFrame.

    Checks that the file exists and is readable and that all required
    columns are present. Raises ``DatasetError`` with a clear message
    when any of these checks fail. The loaded data is returned as-is;
    value validation happens in ``validate_and_parse_dataset``.

    Args:
        csv_path: Path to the CSV file (usually ``data/raw/train.csv``).

    Returns:
        DataFrame with the raw CSV contents.

    Raises:
        DatasetError: If the file does not exist, cannot be read,
            is empty, or lacks any required column.
    """
    if not csv_path.is_file():
        raise DatasetError(
            f"Historical dataset file not found: {csv_path}"
        )

    try:
        df = pd.read_csv(csv_path)
    except Exception as error:
        raise DatasetError(
            f"Could not read dataset file {csv_path}: {error}"
        ) from error

    if df.empty:
        raise DatasetError(
            f"Dataset file {csv_path} contains no records."
        )

    missing = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]
    if missing:
        raise DatasetError(
            f"Dataset file {csv_path} is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    return df


def validate_and_parse_dataset(
    df: pd.DataFrame, source_name: str = "dataset"
) -> pd.DataFrame:
    """Validate required columns, types, dates, and sales values.

    Implements the validation rules from
    ``docs/03-data/data-preprocessing.md`` sections 6-10. Invalid data
    is rejected with a clear error rather than silently converted or
    dropped. The policy of rejecting missing values, nonnumeric
    values, negative sales, and duplicate keys is based on the TASK-005
    inspection evidence (the source dataset contains none of these
    cases) and is documented in the preprocessing documentation.

    Args:
        df: DataFrame returned by ``load_historical_dataset``.
        source_name: Label used in error messages.

    Returns:
        A new DataFrame where ``date`` is datetime64, ``store`` and
        ``item`` are integers, and ``sales`` is numeric. Row order is
        unchanged; sorting happens in the preprocessing step.

    Raises:
        DatasetError: If any required value is missing, identifiers or
            sales are not valid numbers, dates cannot be parsed, sales
            contains negative values, or duplicate (date, store, item)
            keys exist.
    """
    for column in REQUIRED_COLUMNS:
        missing_count = int(df[column].isna().sum())
        if missing_count:
            raise DatasetError(
                f"{source_name} contains {missing_count} missing "
                f"'{column}' value(s). Missing required values are not "
                "allowed."
            )

    validated = df.copy()

    # Identifiers must be whole numbers.
    for column in ("store", "item"):
        try:
            converted = pd.to_numeric(validated[column], errors="raise")
        except ValueError as error:
            raise DatasetError(
                f"{source_name} has nonnumeric '{column}' value(s): {error}"
            ) from error
        if (converted % 1 != 0).any():
            raise DatasetError(
                f"{source_name} has noninteger '{column}' value(s)."
            )
        validated[column] = converted.astype("int64")

    # Sales must be numeric; negatives and duplicates are rejected.
    try:
        sales = pd.to_numeric(validated["sales"], errors="raise")
    except ValueError as error:
        raise DatasetError(
            f"{source_name} has nonnumeric 'sales' value(s): {error}"
        ) from error
    negative_count = int((sales < 0).sum())
    if negative_count:
        raise DatasetError(
            f"{source_name} contains {negative_count} negative 'sales' "
            "value(s). Negative sales must be investigated before use."
        )
    validated["sales"] = sales

    # Dates must parse as real dates.
    try:
        parsed_dates = pd.to_datetime(validated["date"], errors="raise")
    except ValueError as error:
        raise DatasetError(
            f"{source_name} has invalid 'date' value(s): {error}"
        ) from error
    validated["date"] = parsed_dates

    duplicate_mask = validated.duplicated(
        subset=["date", "store", "item"], keep=False
    )
    duplicate_count = int(duplicate_mask.sum())
    if duplicate_count:
        raise DatasetError(
            f"{source_name} contains {duplicate_count} duplicate "
            "(date, store, item) record(s). Duplicates must be "
            "investigated before use instead of being dropped silently."
        )

    return validated


def filter_store(df: pd.DataFrame, store_id: int) -> pd.DataFrame:
    """Filter the history to exactly one store (DEC-015).

    Task-005 evidence shows every store contains the same 50 items, so
    filtering by store yields a complete per-product history.

    Args:
        df: Validated dataset (from ``validate_and_parse_dataset``).
        store_id: Store identifier to keep (1-10 in the source data).

    Returns:
        Filtered DataFrame with a fresh index.

    Raises:
        DatasetError: If the store identifier is unknown or the filter
            would produce an empty dataset.
    """
    filtered = df[df["store"] == store_id]
    if filtered.empty:
        available = sorted(df["store"].unique().tolist())
        raise DatasetError(
            f"Store {store_id} not found in dataset. "
            f"Available stores: {available}"
        )
    return filtered.reset_index(drop=True)


def sort_chronologically(df: pd.DataFrame) -> pd.DataFrame:
    """Sort records by store, item, then date (ascending).

    Chronological order is required for lag features, rolling
    averages, and time-based splitting.

    Args:
        df: Validated (and optionally store-filtered) dataset.

    Returns:
        A new DataFrame sorted by store, item, date with reset index.
    """
    return df.sort_values(
        ["store", "item", "date"], kind="stable"
    ).reset_index(drop=True)


def detect_date_gaps(df: pd.DataFrame) -> dict:
    """Check that every store-item series runs on consecutive days.

    Args:
        df: Validated dataset covering one or more stores.

    Returns:
        Summary with ``combinations_checked``, ``combinations_with_gaps``,
        and ``total_missing_dates`` across all series.
    """
    gaps_total = 0
    combos_with_gaps = 0
    for _, group in df.groupby(["store", "item"]):
        dates = group["date"].sort_values()
        expected = pd.date_range(
            dates.min(), dates.max(), freq="D"
        )
        missing = len(expected.difference(dates))
        if missing:
            combos_with_gaps += 1
            gaps_total += missing

    return {
        "combinations_checked": int(df.groupby(["store", "item"]).ngroups),
        "combinations_with_gaps": combos_with_gaps,
        "total_missing_dates": int(gaps_total),
    }


def preprocess_dataset(
    csv_path: Path, store_id: int = 1
) -> tuple[pd.DataFrame, dict]:
    """Run the full preprocessing workflow for the selected store.

    Workflow per ``docs/03-data/data-preprocessing.md``:
    load -> validate -> filter to the selected store (DEC-015) ->
    sort chronologically -> detect date gaps -> summarize.

    Args:
        csv_path: Path to the historical CSV file.
        store_id: Store to keep (default 1 per DEC-015).

    Returns:
        Tuple of (prepared DataFrame for the selected store, report
        dictionary with the details listed in the preprocessing
        documentation section 17).

    Raises:
        DatasetError: On any loading or validation failure.
    """
    raw_df = load_historical_dataset(csv_path)
    validated_df = validate_and_parse_dataset(
        raw_df, source_name=csv_path.name
    )
    store_df = sort_chronologically(filter_store(validated_df, store_id))
    gaps = detect_date_gaps(store_df)

    zero_sales_count = int((store_df["sales"] == 0).sum())
    report = {
        "source_file": str(csv_path),
        "source_record_count": int(len(raw_df)),
        "store_id": store_id,
        "prepared_record_count": int(len(store_df)),
        "date_range": (store_df["date"].min(), store_df["date"].max()),
        "product_count": int(store_df["item"].nunique()),
        "zero_sales_record_count": zero_sales_count,
        **gaps,
    }
    return store_df, report
