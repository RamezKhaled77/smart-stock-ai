"""Candidate model training and validation evaluation (TASK-030).

Trains the two approved supervised candidates from forecasting-strategy
§3 — Linear Regression (§3.3) and a conservative Random Forest (§3.4)
— on the DEC-056 training window and evaluates them on the validation
window (2016) with the **same one-step-ahead protocol** the baselines
used (TASK-027), so MAE/RMSE comparisons per DEC-027 are like-for-like.

Leakage protocol (feature-engineering §10, model-training §7):

- Features are per-row deterministic transforms (lags, shifted rolling
  means, calendar values) using only actuals strictly before each
  target date — no fitted transformer exists, so no fitted state can
  carry validation information into training.
- The model fits **only** training-window rows; validation rows are
  never touched during fitting.
- Validation predictions use each day's features built from actuals up
  to the previous day, exactly like the baseline walk-forward.

Module stays independent of Streamlit and the operational database.
"""

import math
from dataclasses import dataclass, field

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from smartstock.ml import features as feature_pipeline
from smartstock.ml import splits as split_pipeline

RANDOM_STATE = 2026


@dataclass
class Candidate:
    """One candidate model with its conservative configuration."""

    name: str
    estimator: object
    parameters: dict = field(default_factory=dict)

    def instantiate(self):
        """Return a fresh unfitted estimator (reproducible runs)."""
        return self.estimator.__class__(**self.parameters)


@dataclass
class CandidateReport:
    """Measured validation outcome of one candidate."""

    name: str
    mae: float
    rmse: float
    predictions: int
    parameters: dict
    worst_item_mae: float
    worst_item: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mae": round(self.mae, 3),
            "rmse": round(self.rmse, 3),
            "predictions": self.predictions,
            "parameters": self.parameters,
            "worst_item": self.worst_item,
            "worst_item_mae": round(self.worst_item_mae, 3),
        }


@dataclass
class CandidateComparison:
    """Full DEC-027 comparison table for a validation run."""

    baselines: dict
    candidates: dict

    def candidates_beat_baselines(self) -> dict:
        """Flag per candidate whether it beat both baseline MAEs."""
        checks = {}
        for name, report in self.candidates.items():
            checks[name] = all(
                report.mae < baseline.mae
                for baseline in self.baselines.values()
            )
        return checks


def default_candidates() -> list[Candidate]:
    """The two approved candidates with conservative parameters.

    Random Forest keeps a modest forest size and shallow-ish default
    depth for CPU practicality; random_state is fixed for
    reproducibility (model-training §9). No hyperparameter search.
    """
    return [
        Candidate(
            name="linear_regression",
            estimator=LinearRegression(),
            parameters={},
        ),
        Candidate(
            name="random_forest",
            estimator=RandomForestRegressor(),
            parameters={
                "n_estimators": 200,
                "min_samples_leaf": 5,
                "n_jobs": -1,
                "random_state": RANDOM_STATE,
            },
        ),
    ]


def evaluate_candidates(
    frame: pd.DataFrame,
    candidates: list[Candidate] | None = None,
    *,
    train_start: str = split_pipeline.TRAIN_START,
    train_end: str = split_pipeline.TRAIN_END,
    validation_start: str = split_pipeline.VALIDATION_START,
    validation_end: str = split_pipeline.VALIDATION_END,
    test_start: str = split_pipeline.TEST_START,
    test_end: str = split_pipeline.TEST_END,
) -> CandidateComparison:
    """Train all candidates on the training window and score validation.

    Steps (model-training §7):

    1. Build feature rows on the shared series (per-row deterministic
       transforms — see module leak protocol).
    2. Fit each candidate on complete training-window rows only.
    3. Predict validation rows one-step-ahead and compute pooled
       MAE/RMSE plus the worst item-days' mean error.

    Window bounds default to the DEC-056 constants (train 2013–2015,
    validation 2016, test 2017; the test window is **not** used for
    fitting or scoring, it only bounds the coverage guard). Synthetic
    tests may pass custom bounds with the same semantics; boundaries
    must strictly increase.

    Returns:
        :class:`CandidateComparison` with baseline reports (recomputed
        on the same validation window so the DEC-027 comparison stays
        like-for-like) and one report per candidate.
    """
    if candidates is None:
        candidates = default_candidates()
    if not candidates:
        raise ValueError("No candidates supplied for evaluation.")

    boundaries = [
        train_start, train_end, validation_start,
        validation_end, test_start, test_end,
    ]
    as_dates = pd.to_datetime(pd.Series(boundaries))
    if not as_dates.is_monotonic_increasing:
        raise ValueError(
            f"Window bounds must strictly increase, got {boundaries}."
        )

    # Features are built over the FULL chronology so that early
    # validation days keep their lag/rolling history from training-year
    # actuals — exactly the information the baseline walk-forward uses.
    # This is leak-free: every feature is a per-row function of actuals
    # strictly before its own target date, and fitting uses training
    # rows only (see the module leakage protocol).
    all_rows = feature_pipeline.build_features(frame)
    train_from = pd.Timestamp(train_start)
    train_to = pd.Timestamp(train_end)
    validation_from = pd.Timestamp(validation_start)
    validation_to = pd.Timestamp(validation_end)
    test_from = pd.Timestamp(test_start)
    test_to = pd.Timestamp(test_end)

    outside = all_rows[
        (all_rows["date"] < train_from) | (all_rows["date"] > test_to)
    ]
    if not outside.empty:
        first = outside.iloc[0]
        raise ValueError(
            f"Row with date {first['date'].date()} falls outside the "
            f"split windows ({train_start} → {test_end}); refusing to "
            "silently drop it from candidate evaluation."
        )

    train_complete = feature_pipeline.drop_rows_without_features(
        all_rows[
            (all_rows["date"] >= train_from)
            & (all_rows["date"] <= train_to)
        ]
    )
    validation_complete = feature_pipeline.drop_rows_without_features(
        all_rows[
            (all_rows["date"] >= validation_from)
            & (all_rows["date"] <= validation_to)
        ]
    )

    train_X = train_complete[feature_pipeline.FEATURE_COLUMNS]
    train_y = train_complete["sales"]
    validation_X = validation_complete[feature_pipeline.FEATURE_COLUMNS]
    validation_y = validation_complete["sales"]
    validation_items = validation_complete["item"].to_numpy()

    reports = {}
    for candidate in candidates:
        model = candidate.instantiate()
        model.fit(train_X, train_y)
        predicted = model.predict(validation_X)
        reports[candidate.name] = _score(
            candidate, predicted, validation_y.to_numpy(), validation_items
        )

    from smartstock.ml import baselines

    baseline_reports = baselines.evaluate_baselines(
        frame, start=validation_start, end=validation_end
    )
    return CandidateComparison(
        baselines=baseline_reports, candidates=reports
    )


def _score(
    candidate: Candidate,
    predicted,
    actual,
    items,
) -> CandidateReport:
    absolute_errors = abs(predicted - actual)
    squared_errors = (predicted - actual) ** 2
    count = len(actual)
    per_item = pd.Series(absolute_errors).groupby(items).mean()
    worst = per_item.idxmax()
    return CandidateReport(
        name=candidate.name,
        mae=float(absolute_errors.mean()),
        rmse=math.sqrt(float(squared_errors.mean())),
        predictions=count,
        parameters=dict(candidate.parameters),
        worst_item_mae=float(per_item.max()),
        worst_item=int(worst),
    )
