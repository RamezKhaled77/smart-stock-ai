"""Baseline forecasting candidates and chronological evaluation (TASK-027).

Implements the two approved baseline families from forecasting-strategy
§3 — the Naive Forecast (§3.1) and the Historical Average (§3.2, as
rolling 7- and 30-day means) — and one evaluation helper used by both:

``evaluate_one_step_ahead`` walks forward through a validation window
in date order. For every (item, day) it forecasts from the history of
**already-observed actuals before that day** (train history plus
earlier validation actuals), then adds the actual to the history. No
future information ever enters a prediction — the leakage-prevention
requirement of forecasting-strategy §10.

The later supervised models (TASK-030+) are required to beat both
baselines on the same validation window (DEC-027).
"""

import math
from dataclasses import dataclass

import pandas as pd


@dataclass
class BaselineReport:
    """Measured outcome of one baseline over a validation window."""

    name: str
    mae: float
    rmse: float
    predictions: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mae": round(self.mae, 3),
            "rmse": round(self.rmse, 3),
            "predictions": self.predictions,
        }


def naive_forecast(history: list) -> float:
    """Naive forecast (§3.1): repeat the latest observed value."""
    if not history:
        raise ValueError(
            "Naive forecast needs at least one observation of history."
        )
    return float(history[-1])


def moving_average_forecast(history: list, window: int = 30) -> float:
    """Historical average (§3.2): mean of the trailing ``window`` days.

    With fewer observations than the window, the available recent days
    are used (a guard against crashing on short histories; the
    minimum-history policy for inference is decided separately).
    """
    if window < 1:
        raise ValueError(f"Window must be ≥ 1, got {window}.")
    if not history:
        raise ValueError(
            "Moving average forecast needs at least one observation of "
            "history."
        )
    recent = history[-window:]
    return float(sum(recent) / len(recent))


def evaluate_one_step_ahead(
    frame: pd.DataFrame,
    start: str,
    end: str,
    forecast,
    name: str,
) -> BaselineReport:
    """Walk-forward evaluation of a forecast function over one window.

    Args:
        frame: Preprocessed store-1 frame (``item``, ``date``, ``sales``
            columns; one row per item and day).
        start/end: Inclusive validation window bounds (``YYYY-MM-DD``);
            per DEC-056 this is 2016-01-01 → 2016-12-31.
        forecast: Callable mapping a history list (ascending actuals up
            to day t-1) to the prediction for day t.
        name: Baseline name for the report.

    Returns:
        The :class:`BaselineReport` with pooled MAE and RMSE over all
        predicted item-days.

    Raises:
        ValueError: If the frame is empty, the window is empty or
            reversed, some item has no training history before ``start``,
            or the window's day coverage is incomplete (a missing day
            would silently bias the pooled error).
    """
    _validate_frame(frame)
    if start > end:
        raise ValueError(
            f"Validation window reversed: {start} > {end}."
        )

    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"])
    window_rows = work[
        (work["date"] >= pd.Timestamp(start))
        & (work["date"] <= pd.Timestamp(end))
    ].sort_values(["item", "date"])

    expected_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    for _, group in window_rows.groupby("item"):
        if len(group) != expected_days:
            raise ValueError(
                f"Item {group['item'].iloc[0]} is missing "
                f"{expected_days - len(group)} day(s) inside the "
                f"validation window — refusing to report a biased "
                "error."
            )

    absolute_errors = []
    squared_errors = []
    for item, group in window_rows.groupby("item"):
        full_series = work[work["item"] == item].sort_values("date")
        history = full_series.loc[
            full_series["date"] < pd.Timestamp(start), "sales"
        ].astype(float).tolist()
        if not history:
            raise ValueError(
                f"Item {item} has no history before {start}; DEC-056 "
                "provides 3 training years, so empty training history "
                "is not supported here."
            )
        for _, row in group.iterrows():
            prediction = forecast(history)
            actual = float(row["sales"])
            absolute_errors.append(abs(prediction - actual))
            squared_errors.append((prediction - actual) ** 2)
            # The actual becomes history only for the *next* day.
            history.append(actual)

    if not absolute_errors:  # defensive; the day-coverage check above
        # makes an empty window unreachable in practice
        raise ValueError("No predictions were generated.")

    predictions = len(absolute_errors)
    return BaselineReport(
        name=name,
        mae=sum(absolute_errors) / predictions,
        rmse=math.sqrt(sum(squared_errors) / predictions),
        predictions=predictions,
    )


def evaluate_baselines(
    frame: pd.DataFrame, start: str = "2016-01-01", end: str = "2016-12-31"
) -> dict:
    """Run both approved baselines over the validation window.

    Returns:
        Dictionary of :class:`BaselineReport` keyed ``naive``,
        ``moving_average_7``, and ``moving_average_30`` (the r7/r30
        window pair covers forecasting-strategy §3.2's window question;
        the final historical-average window is selected from these
        measured numbers).
    """
    return {
        "naive": evaluate_one_step_ahead(
            frame, start, end, naive_forecast, "naive"
        ),
        "moving_average_7": evaluate_one_step_ahead(
            frame,
            start,
            end,
            lambda history: moving_average_forecast(history, window=7),
            "moving_average_7",
        ),
        "moving_average_30": evaluate_one_step_ahead(
            frame,
            start,
            end,
            lambda history: moving_average_forecast(history, window=30),
            "moving_average_30",
        ),
    }


def _validate_frame(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("Cannot evaluate on an empty dataset.")
    missing = [
        column for column in ("item", "date", "sales")
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}.")
