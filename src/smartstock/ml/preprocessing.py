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
    value validation happens in ``validate_dataset``.

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
