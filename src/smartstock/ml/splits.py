"""Chronological train/validation/test splitting (TASK-029).

Implements the DEC-056 split as code so every later task (baseline
re-evaluation, candidate training TASK-030, final selection TASK-031)
shares one definition:

| Split      | Window                          |
|------------|---------------------------------|
| Training   | 2013-01-01 → 2015-12-31         |
| Validation | 2016-01-01 → 2016-12-31         |
| Test       | 2017-01-01 → 2017-12-31         |

Splitting is strictly chronological: training precedes validation,
validation precedes test, and every window is inclusive. Rows outside
all three windows are refused (not silently dropped) — discarding data
quietly would mask preprocessing gaps.

The module stays independent of Streamlit and the operational database.
"""

import pandas as pd

# DEC-056 calendar windows (inclusive bounds, YYYY-MM-DD).
TRAIN_START = "2013-01-01"
TRAIN_END = "2015-12-31"
VALIDATION_START = "2016-01-01"
VALIDATION_END = "2016-12-31"
TEST_START = "2017-01-01"
TEST_END = "2017-12-31"

REQUIRED_COLUMNS = ["store", "item", "date", "sales"]


class SplitError(Exception):
    """Raised when a frame cannot be split chronologically."""


def chronological_split(
    frame: pd.DataFrame,
    train_end: str = TRAIN_END,
    validation_start: str = VALIDATION_START,
    validation_end: str = VALIDATION_END,
    test_start: str = TEST_START,
    test_end: str = TEST_END,
    train_start: str = TRAIN_START,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a frame into (train, validation, test) by inclusive dates.

    Args:
        frame: Preprocessed frame with ``date`` (``YYYY-MM-DD`` strings
            or datetimes) plus the required columns.
        train_end: Inclusive last training day (default: DEC-056).
        validation_start/validation_end: Inclusive validation window.
        test_start/test_end: Inclusive test window.
        train_start: Inclusive first training day.

    Returns:
        Three new DataFrames sorted chronologically with fresh indexes.

    Raises:
        SplitError: If the frame is empty, misses required columns,
            the boundaries are not strictly increasing, any row falls
            outside the three windows, or any window ends up empty.
    """
    if frame.empty:
        raise SplitError("Cannot split an empty dataset.")
    missing = [
        column for column in REQUIRED_COLUMNS if column not in frame.columns
    ]
    if missing:
        raise SplitError(f"Dataset is missing columns: {missing}.")

    boundaries = [
        train_start, train_end, validation_start,
        validation_end, test_start, test_end,
    ]
    as_dates = pd.to_datetime(pd.Series(boundaries))
    if not as_dates.is_monotonic_increasing:
        raise SplitError(
            f"Split boundaries must strictly increase, got {boundaries}."
        )

    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"])
    work = work.sort_values("date").reset_index(drop=True)

    def mask(start: str, end: str) -> pd.Series:
        timestamps = work["date"]
        return (timestamps >= pd.Timestamp(start)) & (
            timestamps <= pd.Timestamp(end)
        )

    train_mask = mask(train_start, train_end)
    validation_mask = mask(validation_start, validation_end)
    test_mask = mask(test_start, test_end)

    train = _select_window(
        work, train_mask, "train", allow_empty=False
    )
    validation = _select_window(
        work, validation_mask, "validation", allow_empty=False
    )
    test = _select_window(work, test_mask, "test", allow_empty=False)

    covered = train_mask | validation_mask | test_mask
    if not covered.all():
        first_uncovered = work.loc[~covered].iloc[0]
        raise SplitError(
            f"Row with date {first_uncovered['date'].date()} falls "
            "outside every split window; refusing to silently drop it."
        )

    chronology_holds = train["date"].max() < validation["date"].min() and (
        validation["date"].max() < test["date"].min()
    )
    if not chronology_holds:
        raise SplitError(
            "Split windows overlap after filtering; boundaries must be "
            "strictly increasing in time."
        )

    return train, validation, test


def _select_window(
    frame: pd.DataFrame, row_mask: pd.Series, name: str, allow_empty: bool
) -> pd.DataFrame:
    """Select rows by a boolean mask built on ``frame``'s index."""
    selected = frame[row_mask]
    if selected.empty and not allow_empty:
        raise SplitError(f"The {name} window selected no rows.")
    return selected.reset_index(drop=True)
