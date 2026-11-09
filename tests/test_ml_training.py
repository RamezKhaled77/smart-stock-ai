"""Tests for candidate model training and evaluation (TASK-030).

Synthetic frames verify the training/evaluation workflow with
hand-computable outcomes; the real DEC-056 dataset pins the measured
candidate results so the evaluation doc stays reproducible.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from smartstock.ml import training


def feature_series_frame(dates, items=(1,), base=20.0) -> pd.DataFrame:
    """Smooth daily demand: base + small ramp → easy to learn."""
    rows = []
    for item in items:
        for offset, date in enumerate(dates):
            rows.append(
                {
                    "store": 1,
                    "item": item,
                    "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                    "sales": base + 0.1 * offset,
                }
            )
    return pd.DataFrame(rows)


class TestDefaultCandidates:
    def test_two_approved_candidates(self) -> None:
        names = [c.name for c in training.default_candidates()]
        assert names == ["linear_regression", "random_forest"]

    def test_random_forest_is_conservative(self) -> None:
        forest = training.default_candidates()[1]
        assert forest.parameters["n_estimators"] == 200
        assert forest.parameters["min_samples_leaf"] == 5
        assert "random_state" in forest.parameters  # reproducibility

    def test_instantiate_returns_fresh_estimator(self) -> None:
        candidate = training.default_candidates()[0]
        first = candidate.instantiate()
        second = candidate.instantiate()
        assert (first is second) is False


class TestSyntheticEvaluation:
    """A near-linear series: LinearRegression must nail it.

    Custom windows: train the first 60 days, validate the last 20.
    """

    n_days = 80

    @pytest.fixture
    def frame(self) -> pd.DataFrame:
        dates = pd.date_range("2023-10-01", periods=self.n_days, freq="D")
        return feature_series_frame(
            [d.strftime("%Y-%m-%d") for d in dates], items=(1, 2)
        )

    def evaluate(self, frame):
        return training.evaluate_candidates(
            frame,
            candidates=training.default_candidates(),
            train_start="2023-10-01",
            train_end="2023-11-29",
            validation_start="2023-11-30",
            validation_end="2023-12-19",
            test_start="2023-12-19",
            test_end="2023-12-19",
        )

    def test_linear_regression_nearly_perfect(self, frame) -> None:
        comparison = self.evaluate(frame)
        # base + 0.1*offset is exact in lag_1 → almost zero error.
        assert comparison.candidates["linear_regression"].mae < 0.2

    def test_baseline_reports_computed_on_same_window(
        self, frame
    ) -> None:
        comparison = self.evaluate(frame)
        counts = {
            b.predictions for b in comparison.baselines.values()
        }
        candidate_counts = {
            c.predictions for c in comparison.candidates.values()
        }
        assert counts == candidate_counts  # like-for-like DEC-027

    def test_worst_item_reported(self, frame) -> None:
        comparison = self.evaluate(frame)
        for report in comparison.candidates.values():
            assert report.worst_item in (1, 2)
            assert report.worst_item_mae >= report.mae

    def test_linear_regression_beats_baselines_on_learnable_series(
        self, frame
    ) -> None:
        comparison = self.evaluate(frame)
        checks = comparison.candidates_beat_baselines()
        # On a near-perfectly learnable ramp, LinearRegression (exact)
        # must beat every baseline; the Random Forest result on tiny
        # synthetic data is only asserted on the real dataset.
        assert checks["linear_regression"] is True

    def test_reversed_window_bounds_rejected(self, frame) -> None:
        with pytest.raises(ValueError, match="strictly increase"):
            training.evaluate_candidates(
                frame,
                train_start="2023-11-01",
                train_end="2023-10-01",
                validation_start="2023-11-30",
                validation_end="2023-12-19",
                test_start="2023-12-19",
                test_end="2023-12-19",
            )


class TestEvaluationGuards:
    def test_no_candidates_rejected(self) -> None:
        frame = feature_series_frame(["2013-01-01"])
        with pytest.raises(ValueError, match="No candidates"):
            training.evaluate_candidates(frame, candidates=[])

    def test_rows_outside_dec056_windows_rejected(self) -> None:
        dates = pd.date_range("2018-01-01", periods=40, freq="D")
        frame = feature_series_frame(
            [d.strftime("%Y-%m-%d") for d in dates]
        )
        with pytest.raises(ValueError, match="outside the split windows"):
            training.evaluate_candidates(frame)

    def test_test_window_evaluation_workflow(self) -> None:
        # Fit on everything before the 28-day test window, score once.
        dates = pd.date_range("2023-01-01", periods=120, freq="D")
        frame = feature_series_frame(
            [d.strftime("%Y-%m-%d") for d in dates]
        )
        comparison = training.evaluate_on_test(
            frame,
            train_start="2023-01-01",
            train_end="2023-02-28",
            validation_start="2023-03-01",
            validation_end="2023-04-02",
            test_start="2023-04-03",
            test_end="2023-04-30",
        )
        for report in comparison.candidates.values():
            assert report.predictions == 28  # 28 test days × 1 item

    def test_test_window_reversed_bounds_rejected(self) -> None:
        dates = pd.date_range("2023-01-01", periods=20, freq="D")
        frame = feature_series_frame(
            [d.strftime("%Y-%m-%d") for d in dates]
        )
        with pytest.raises(ValueError, match="strictly increase"):
            training.evaluate_on_test(
                frame,
                train_start="2023-01-01",
                train_end="2023-01-05",
                validation_start="2023-01-06",
                validation_end="2023-01-15",
                test_start="2023-01-14",
                test_end="2023-01-20",
            )


class TestReproducibility:
    def test_random_forest_repeats_with_fixed_seed(self) -> None:
        dates = pd.date_range("2023-01-01", periods=90, freq="D")
        frame = feature_series_frame(
            [d.strftime("%Y-%m-%d") for d in dates]
        )
        bounds = dict(
            train_start="2023-01-01",
            train_end="2023-03-01",
            validation_start="2023-03-02",
            validation_end="2023-03-31",
            test_start="2023-03-31",
            test_end="2023-03-31",
        )
        first = training.evaluate_candidates(frame, **bounds)
        second = training.evaluate_candidates(frame, **bounds)
        assert first.candidates["random_forest"].mae == (
            pytest.approx(second.candidates["random_forest"].mae)
        )


@pytest.fixture(scope="class")
def store1():
    """The real preprocessed store-1 dataset (when present)."""
    from smartstock.ml import preprocessing

    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return frame


@pytest.fixture(scope="class")
def comparison(store1) -> training.CandidateComparison:
    """Candidate evaluation over the real DEC-056 validation window."""
    return training.evaluate_candidates(store1)


@pytest.fixture(scope="class")
def test_comparison(store1) -> training.CandidateComparison:
    """The one-time DEC-056 test-window evaluation (TASK-031)."""
    return training.evaluate_on_test(store1)


class TestRealTestWindow:
    """One-time test-2017 confirmation numbers (doc: model-evaluation §18)."""

    def test_prediction_counts(self, test_comparison) -> None:
        # 50 items × 365 days of 2017; matches the test baselines.
        for report in test_comparison.candidates.values():
            assert report.predictions == 18_250
        assert all(
            baseline.predictions == 18_250
            for baseline in test_comparison.baselines.values()
        )

    def test_reference_baseline_numbers(self, test_comparison) -> None:
        assert test_comparison.baselines["naive"].to_dict() == {
            "name": "naive", "mae": 10.512, "rmse": 14.13,
            "predictions": 18_250,
        }
        assert test_comparison.baselines["moving_average_7"].to_dict() == {
            "name": "moving_average_7", "mae": 8.378, "rmse": 10.922,
            "predictions": 18_250,
        }

    def test_linear_regression_measured_result(
        self, test_comparison
    ) -> None:
        report = test_comparison.candidates["linear_regression"].to_dict()
        assert report["mae"] == pytest.approx(6.637, abs=0.002)
        assert report["rmse"] == pytest.approx(8.611, abs=0.002)
        assert report["worst_item"] == 28

    def test_random_forest_measured_result(self, test_comparison) -> None:
        report = test_comparison.candidates["random_forest"].to_dict()
        assert report["mae"] == pytest.approx(6.088, abs=0.002)
        assert report["rmse"] == pytest.approx(7.910, abs=0.002)
        assert report["worst_item"] == 28

    def test_selection_confirmed_on_test(self, test_comparison) -> None:
        # The validation-selected winner (Random Forest) also wins MAE
        # and RMSE on the one-time test window and beats both test
        # baselines — the DEC-056 single-touch confirmation.
        checks = test_comparison.candidates_beat_baselines()
        assert checks == {
            "linear_regression": True,
            "random_forest": True,
        }
        assert (
            test_comparison.candidates["random_forest"].mae
            < test_comparison.candidates["linear_regression"].mae
        )


class TestRealValidationResults:
    """Measured TASK-030 numbers pinned to code (doc: model-evaluation)."""

    def test_like_for_like_prediction_counts(self, comparison) -> None:
        for report in comparison.candidates.values():
            assert report.predictions == 18_300  # 50 items × 366 days
        # Identical windows to the baselines: no January 2016 losses.
        assert all(
            report.predictions == baseline.predictions
            for report, baseline in zip(
                comparison.candidates.values(),
                comparison.baselines.values(),
            )
        )

    def test_linear_regression_measured_result(
        self, comparison
    ) -> None:
        report = comparison.candidates["linear_regression"].to_dict()
        assert report["mae"] == pytest.approx(6.482, abs=0.002)
        assert report["rmse"] == pytest.approx(8.387, abs=0.002)
        assert report["worst_item"] == 15
        assert report["worst_item_mae"] == pytest.approx(9.914, abs=0.002)

    def test_random_forest_measured_result(self, comparison) -> None:
        report = comparison.candidates["random_forest"].to_dict()
        assert report["mae"] == pytest.approx(6.033, abs=0.002)
        assert report["rmse"] == pytest.approx(7.785, abs=0.002)
        assert report["worst_item"] == 15
        assert report["worst_item_mae"] == pytest.approx(9.349, abs=0.002)

    def test_both_candidates_beat_both_baselines(
        self, comparison
    ) -> None:
        # DEC-027 gate: candidates must beat naive (10.270) AND MA-7
        # (8.077) pooled MAE on the same 2016 window.
        assert comparison.candidates_beat_baselines() == {
            "linear_regression": True,
            "random_forest": True,
        }
        assert comparison.baselines["moving_average_7"].mae == (
            pytest.approx(8.077, abs=0.002)
        )
        assert comparison.baselines["naive"].mae == pytest.approx(
            10.270, abs=0.002
        )

    def test_random_forest_edges_linear(self, comparison) -> None:
        assert (
            comparison.candidates["random_forest"].mae
            < comparison.candidates["linear_regression"].mae
        )
