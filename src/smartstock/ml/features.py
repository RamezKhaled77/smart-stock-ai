"""Feature engineering for demand forecasting (TASK-028).

Implements the feature pipeline defined in
``docs/04-machine-learning/feature-engineering.md`` over a preprocessed
historical frame (``store``, ``item``, ``date``, ``sales``):

1. Calendar features: ``day_of_week`` (0 = Monday), ``month``,
   ``day_of_month``.
2. Lag features: ``lag_1`` and ``lag_7`` — past sales shifted **within
   each (store, item) series** so items never borrow a neighbor's row.
3. Rolling features: ``rolling_mean_7`` and ``rolling_mean_30``
   computed on ``sales.shift(1)``, so the current target value is never
   part of its own features (§6).

All features use information available strictly before the target date
(§10 — no data leakage). Early observations that lack enough history
keep missing values rather than being filled arbitrarily (§8); training
consumers drop them explicitly via :func:`drop_rows_without_features`.

The module stays independent of Streamlit and the operational database.
"""

import pandas as pd

# Required input columns (§2).
REQUIRED_COLUMNS = ["store", "item", "date", "sales"]

# Model feature columns in their fixed order (§9).
FEATURE_COLUMNS = [
    "day_of_week",
    "month",
    "day_of_month",
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "rolling_mean_30",
]

# One-step shift guarantees rolling features exclude the current target.
ROLLING_SHIFT = 1


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``frame`` with the engineered feature columns.

    The input must carry the preprocessed columns (store, item, date,
    sales). Series are grouped per (store, item) and sorted
    chronologically before lagging, per §5 and §7.

    Rows near the start of each series keep ``NaN`` in lag/rolling
    columns (§8) — no arbitrary fills.

    Raises:
        ValueError: If the frame is empty or misses a required column.
    """
    if frame.empty:
        raise ValueError("Cannot build features from an empty dataset.")
    missing = [
        column for column in REQUIRED_COLUMNS if column not in frame.columns
    ]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.sort_values(["store", "item", "date"]).reset_index(
        drop=True
    )

    # Calendar features (§4).
    result["day_of_week"] = result["date"].dt.day_of_week
    result["month"] = result["date"].dt.month
    result["day_of_month"] = result["date"].dt.day

    # Lag and rolling features within each (store, item) series (§5, §6).
    grouped = result.groupby(["store", "item"], sort=False)["sales"]
    result["lag_1"] = grouped.shift(1)
    result["lag_7"] = grouped.shift(7)
    previous_sales = grouped.shift(ROLLING_SHIFT)
    result["rolling_mean_7"] = (
        previous_sales.groupby(
            [result["store"], result["item"]], sort=False
        )
        .rolling(7, min_periods=7)
        .mean()
        .reset_index(level=[0, 1], drop=True)
    )
    result["rolling_mean_30"] = (
        previous_sales.groupby(
            [result["store"], result["item"]], sort=False
        )
        .rolling(30, min_periods=30)
        .mean()
        .reset_index(level=[0, 1], drop=True)
    )
    return result


def drop_rows_without_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing any engineered feature value (§8 strategy).

    Training consumers call this explicitly instead of the pipeline
    filling values arbitrarily. The first rows of each series are lost
    by design: ``rolling_mean_30`` requires 30 past observations plus
    the one-step shift, so a series needs 31 observed days before its
    first fully-featured row (regardless of calendar gaps, features
    count observations, not dates).
    """
    if frame.empty:
        raise ValueError("Cannot select features from an empty dataset.")
    missing_columns = [
        column
        for column in FEATURE_COLUMNS + ["sales"]
        if column not in frame.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    complete = frame.dropna(subset=FEATURE_COLUMNS)
    return complete.reset_index(drop=True)


def feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split a fully-featured frame into (X, y) for model training.

    The target ``sales`` is never part of the feature matrix (§9), and
    column order is fixed by :data:`FEATURE_COLUMNS` for reproducible
    model input.
    """
    complete = drop_rows_without_features(frame)
    return complete[FEATURE_COLUMNS].copy(), complete["sales"].copy()
