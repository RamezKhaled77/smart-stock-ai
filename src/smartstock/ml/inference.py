"""Forecast inference for supported products (TASK-033).

Implements the prediction-logic doc workflow on top of the saved model
artifact (TASK-032):

1. Validate the horizon (DEC-026: 7, 14, or 30 days) and the product's
   history (one observation per day, non-negative quantities).
2. Choose the path per DEC-058:
   - **≥ 31 observed days** → the Random Forest (DEC-057) with
     recursive features (DEC-025): the prediction for each day is
     appended to a temporary working history before the next day's
     features are recomputed.
   - **1 → 30 days** → the trailing-7-day moving average (TASK-027
     baseline) applied recursively — predictions join the trailing
     window.
   - **0 days** → refused with an explicit error (§13).
3. Return raw predictions (no rounding here — the business layer
   rounds, per prediction-logic §11) clipped to non-negative values
   (§10, documented policy).

The prediction history is per-call and never touches operational sales
records (§8). The module stays independent of Streamlit.
"""

import math
from datetime import datetime, timezone

import pandas as pd

from smartstock.ml.baselines import moving_average_forecast
from smartstock.ml.features import FEATURE_COLUMNS

SUPPORTED_HORIZONS = (7, 14, 30)
DEFAULT_HORIZON_DAYS = 7

# DEC-058 (measured at TASK-028): rolling_mean_30 + one-step shift need
# 31 observations before the first fully-featured training row.
MINIMUM_MODEL_HISTORY = 31
FALLBACK_WINDOW_DAYS = 7

REQUIRED_INPUT_COLUMNS = ["date", "sales"]


class ForecastError(Exception):
    """Raised when a forecast cannot be generated as requested."""


def forecast_product(
    model,
    metadata: dict,
    history: pd.DataFrame,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    product_id=None,
) -> pd.DataFrame:
    """Forecast ``horizon_days`` of demand for one product series.

    Args:
        model: Fitted scikit-learn estimator (from the model artifact).
        metadata: Artifact metadata (model_version is reported onward).
        history: The product's daily sales observations with ``date``
            and ``sales`` columns. Any number of rows ≥ 1; rows are
            sorted internally; duplicates are rejected.
        horizon_days: One of the DEC-026 horizons (7/14/30).
        product_id: Optional identifier copied into the output rows.

    Returns:
        DataFrame with columns ``product_id``, ``forecast_date``,
        ``predicted_demand`` (raw float, clipped to ≥ 0),
        ``model_used`` (``random_forest`` or ``moving_average_7``),
        ``model_version``, and ``generated_at`` (UTC) — one row per
        forecast day, in chronological order.

    Raises:
        ForecastError: On an unsupported horizon, empty history,
            duplicate dates, invalid sales values, or a non-finite
            model output.
    """
    if horizon_days not in SUPPORTED_HORIZONS:
        raise ForecastError(
            f"Unsupported horizon {horizon_days!r}. Choose one of "
            f"{list(SUPPORTED_HORIZONS)} (DEC-026)."
        )
    if history.empty:
        raise ForecastError(
            "No suitable history exists for this product "
            "(prediction-logic §13): forecasting needs at least one "
            "observed day."
        )
    missing = [
        column
        for column in REQUIRED_INPUT_COLUMNS
        if column not in history.columns
    ]
    if missing:
        raise ForecastError(f"History is missing columns: {missing}.")

    work = history.copy()
    work["date"] = pd.to_datetime(work["date"])
    work["sales"] = pd.to_numeric(work["sales"], errors="raise")
    if work["sales"].isna().any():
        raise ForecastError("History sales contain invalid values.")
    if (work["sales"] < 0).any():
        raise ForecastError("History sales must be non-negative.")
    work = work.sort_values("date")
    if work["date"].duplicated().any():
        raise ForecastError(
            "History must hold one observation per day; duplicate "
            "dates found. Aggregate multi-record days before "
            "forecasting."
        )

    series = work["sales"].astype(float).tolist()
    last_date = work["date"].iloc[-1]
    model_used = (
        "random_forest"
        if len(series) >= MINIMUM_MODEL_HISTORY
        else "moving_average_7"
    )

    predictions = []
    working_history = list(series)
    for offset in range(horizon_days):
        forecast_date = last_date + pd.Timedelta(days=offset + 1)
        raw = _predict_one_day(
            model, metadata, model_used, forecast_date, working_history
        )
        clipped = max(0.0, float(raw))
        predictions.append(clipped)
        working_history.append(clipped)

    generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return pd.DataFrame(
        {
            "product_id": [product_id] * horizon_days,
            "forecast_date": [
                last_date + pd.Timedelta(days=offset + 1)
                for offset in range(horizon_days)
            ],
            "predicted_demand": predictions,
            "model_used": [model_used] * horizon_days,
            "model_version": [metadata["model_version"]] * horizon_days,
            "generated_at": [generated_at] * horizon_days,
        }
    )


def _predict_one_day(
    model,
    metadata: dict,
    model_used: str,
    forecast_date: pd.Timestamp,
    working_history: list[float],
) -> float:
    """One recursive step (prediction-logic §8 step 2–5)."""
    if model_used == "moving_average_7":
        return float(
            moving_average_forecast(
                working_history, window=FALLBACK_WINDOW_DAYS
            )
        )

    if len(working_history) < MINIMUM_MODEL_HISTORY:
        raise ForecastError(
            "Internal contract error: model path requires ≥ "
            f"{MINIMUM_MODEL_HISTORY} observations."
        )
    row = {
        "day_of_week": float(forecast_date.day_of_week),
        "month": float(forecast_date.month),
        "day_of_month": float(forecast_date.day),
        "lag_1": float(working_history[-1]),
        "lag_7": float(working_history[-7]),
        "rolling_mean_7": float(
            sum(working_history[-7:]) / FALLBACK_WINDOW_DAYS
        ),
        "rolling_mean_30": float(
            sum(working_history[-30:]) / 30
        ),
    }
    features = pd.DataFrame(
        [[row[column] for column in FEATURE_COLUMNS]],
        columns=FEATURE_COLUMNS,
    )
    prediction = float(model.predict(features)[0])
    if not math.isfinite(prediction):
        raise ForecastError(
            "Model produced a non-finite prediction; rejecting the "
            "result (prediction-logic §10)."
        )
    return prediction
