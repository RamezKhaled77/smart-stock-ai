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
