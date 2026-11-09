"""Exploratory analysis for the historical sales series (TASK-026).

Computes the patterns documented in
``docs/04-machine-learning/data-exploration.md`` from a preprocessed
store-1 DataFrame (see :mod:`smartstock.ml.preprocessing`). Every
function is pure: it takes a DataFrame and returns plain Python values
(JSON-serializable) so a test can assert the documented report numbers
come from the same code path used to produce them.

The module stays independent of Streamlit and the operational database.
"""

import pandas as pd

REQUIRED_COLUMNS = ["date", "sales"]

# Weekday labels in pandas day_of_week order (Monday = 0).
WEEKDAY_NAMES = {
    0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun",
}

PERCENTILES = (5, 25, 50, 75, 95, 99)


def require_columns(df: pd.DataFrame, columns: list) -> None:
    """Raise ``ValueError`` when the frame lacks required columns."""
    if df.empty:
        raise ValueError("Cannot explore an empty dataset.")
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}.")


def with_calendar_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with parsed dates plus weekday/month/year columns.

    The input must carry a ``date`` column of ``YYYY-MM-DD`` strings or
    datetimes (the preprocessing pipeline output qualifies).
    """
    require_columns(df, ["date"])
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["weekday"] = frame["date"].dt.day_of_week
    frame["month"] = frame["date"].dt.month
    frame["year"] = frame["date"].dt.year
    return frame


def compute_overview(df: pd.DataFrame) -> dict:
    """Basic time-coverage facts (TASK-005-verified facts restated)."""
    require_columns(df, ["date", "sales", "item"])
    dates = pd.to_datetime(df["date"])
    return {
        "total_records": int(len(df)),
        "date_min": dates.min().strftime("%Y-%m-%d"),
        "date_max": dates.max().strftime("%Y-%m-%d"),
        "days_covered": int(dates.nunique()),
        "item_count": int(df["item"].nunique()),
        "zero_sales_records": int((df["sales"] == 0).sum()),
    }


def compute_sales_distribution(df: pd.DataFrame) -> dict:
    """Distribution shape of daily sales quantities."""
    require_columns(df, ["sales"])
    sales = df["sales"]
    return {
        "mean": float(sales.mean()),
        "std": float(sales.std()),
        "min": int(sales.min()),
        "max": int(sales.max()),
        "percentiles": {
            str(p): float(sales.quantile(p / 100)) for p in PERCENTILES
        },
    }


def compute_weekday_pattern(df: pd.DataFrame) -> dict:
    """Mean sales per weekday (Monday = 0), labeled for readability."""
    frame = with_calendar_columns(df)
    means = frame.groupby("weekday")["sales"].mean()
    return {
        WEEKDAY_NAMES[weekday]: round(float(value), 2)
        for weekday, value in means.items()
    }


def compute_monthly_pattern(df: pd.DataFrame) -> dict:
    """Mean sales per calendar month (1–12)."""
    frame = with_calendar_columns(df)
    means = frame.groupby("month")["sales"].mean()
    return {int(month): round(float(value), 2) for month, value in means.items()}


def compute_yearly_totals(df: pd.DataFrame) -> dict:
    """Total, mean, and record count per year."""
    frame = with_calendar_columns(df)
    grouped = frame.groupby("year")["sales"].agg(["sum", "mean", "count"])
    return {
        int(year): {
            "total": int(row["sum"]),
            "mean": round(float(row["mean"]), 2),
            "records": int(row["count"]),
        }
        for year, row in grouped.iterrows()
    }


def compute_lag_correlations(df: pd.DataFrame) -> dict:
    """Pearson correlation between sales and past-day sales per item.

    Lags are shifted **within each item's series**, so an item does not
    borrow yesterday's sales from its data-row neighbor (no leakage).
    """
    require_columns(df, ["item", "sales", "date"])
    ordered = with_calendar_columns(df).sort_values(["item", "date"])
    result = {}
    for lag in (1, 7, 30):
        shifted = ordered.groupby("item")["sales"].shift(lag)
        result[f"lag_{lag}"] = round(
            float(ordered["sales"].corr(shifted)), 3
        )
    return result


def compute_item_summary(df: pd.DataFrame) -> dict:
    """Per-item coverage and strongest/weakest items by mean demand."""
    require_columns(df, ["item", "sales", "date"])
    frame = with_calendar_columns(df)
    coverage = frame.groupby("item")["date"].nunique()
    means = frame.groupby("item")["sales"].mean()
    return {
        "days_per_item_min": int(coverage.min()),
        "days_per_item_max": int(coverage.max()),
        "weakest_items": {
            int(item): round(float(value), 1)
            for item, value in means.nsmallest(3).items()
        },
        "strongest_items": {
            int(item): round(float(value), 1)
            for item, value in means.nlargest(3).items()
        },
    }


def summarize_series(df: pd.DataFrame) -> dict:
    """Combine all exploration views into one report dictionary."""
    return {
        "overview": compute_overview(df),
        "distribution": compute_sales_distribution(df),
        "weekday_pattern": compute_weekday_pattern(df),
        "monthly_pattern": compute_monthly_pattern(df),
        "yearly_totals": compute_yearly_totals(df),
        "lag_correlations": compute_lag_correlations(df),
        "item_summary": compute_item_summary(df),
    }
