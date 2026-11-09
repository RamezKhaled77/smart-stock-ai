"""Tests for baseline forecasting and chronological evaluation (TASK-027).

Synthetic frames with hand-computable errors verify the walk-forward
logic and its leakage guard; the real DEC-056 validation window pins
the documented report numbers.
"""

from pathlib import Path

import pandas as pd
import pytest

from smartstock.ml import baselines


@pytest.fixture
def synthetic():
    """One item, a 10-day history then a 6-day validation window."""
    rows = []
    day_0 = pd.Timestamp("2024-01-01")
    for offset in range(16):
        date = (day_0 + pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
        rows.append(
            {
                "store": 1,
                "item": 1,
                "date": date,
                "sales": offset + 1,  # 1..16 (a clean ramp)
            }
        )
    return pd.DataFrame(rows)


class TestForecastFunctions:
    def test_naive_repeats_latest_value(self) -> None:
        assert baselines.naive_forecast([5]) == 5
        assert baselines.naive_forecast([5, 8, 3]) == 3

    def test_naive_rejects_empty_history(self) -> None:
        with pytest.raises(ValueError, match="history"):
            baselines.naive_forecast([])

    def test_moving_average_trailing_window(self) -> None:
        # Only the trailing window days count, never earlier ones.
        assert baselines.moving_average_forecast([1, 2, 3, 9], window=2) == 6.0
        assert baselines.moving_average_forecast([7], window=30) == 7.0

    def test_moving_average_rejects_bad_window(self) -> None:
        with pytest.raises(ValueError, match="Window"):
            baselines.moving_average_forecast([1, 2], window=0)

    def test_moving_average_rejects_empty_history(self) -> None:
        with pytest.raises(ValueError, match="history"):
            baselines.moving_average_forecast([], window=7)


class TestWalkForwardEvaluation:
    def test_ramp_gives_unit_errors_for_naive(self, synthetic) -> None:
        # Predicting day t as day t-1's actual in a ramp: every error
        # is exactly 1 unit (7 validation days 2024-01-11 .. 01-16,
        # offsets 10..15 → 6 days).
        report = baselines.evaluate_one_step_ahead(
            synthetic, "2024-01-11", "2024-01-16",
            baselines.naive_forecast, "naive",
        )
        assert report.predictions == 6
        assert report.mae == pytest.approx(1.0)
        assert report.rmse == pytest.approx(1.0)

    def test_moving_average_1_equals_naive(self, synthetic) -> None:
        report = baselines.evaluate_one_step_ahead(
            synthetic, "2024-01-11", "2024-01-16",
            lambda history: baselines.moving_average_forecast(
                history, window=1
            ),
            "ma1",
        )
        assert report.mae == pytest.approx(1.0)

    def test_constant_series_gives_zero_error(self) -> None:
        rows = []
        day_0 = pd.Timestamp("2024-01-01")
        for offset in range(20):
            rows.append(
                {
                    "store": 1,
                    "item": 1,
                    "date": (day_0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": 42,
                }
            )
        frame = pd.DataFrame(rows)
        report = baselines.evaluate_one_step_ahead(
            frame, "2024-01-11", "2024-01-20",
            lambda history: baselines.moving_average_forecast(
                history, window=7
            ),
            "flat-7",
        )
        assert report.mae == 0.0
        assert report.predictions == 10

    def test_no_future_leakage_in_history(self, synthetic) -> None:
        # The forecast function must never see the current day or later.
        seen = []

        def spy(history):
            seen.append(tuple(history))
            return history[-1]

        baselines.evaluate_one_step_ahead(
            synthetic, "2024-01-11", "2024-01-16", spy, "spy"
        )
        # Six calls; histories grow by one actual each step and cap at
        # day 10's value (17? no — offset 10 → sales value 11 is max).
        assert len(seen) == 6
        for index, history in enumerate(seen):
            assert 11 + index > max(history)  # current day not in history
        assert seen[0][-1] == 10  # last training value is offset 9 → 10

    def test_validation_window_bounds_respected(self, synthetic) -> None:
        report = baselines.evaluate_one_step_ahead(
            synthetic, "2024-01-14", "2024-01-14",
            baselines.naive_forecast, "one-day",
        )
        assert report.predictions == 1

    def test_reversed_window_rejected(self, synthetic) -> None:
        with pytest.raises(ValueError, match="reversed"):
            baselines.evaluate_one_step_ahead(
                synthetic, "2024-01-16", "2024-01-11",
                baselines.naive_forecast, "x",
            )

    def test_incomplete_window_coverage_rejected(self) -> None:
        rows = []
        day_0 = pd.Timestamp("2024-01-01")
        for offset in range(12):
            if offset == 5:  # a gap inside the validation window
                continue
            rows.append(
                {
                    "store": 1,
                    "item": 1,
                    "date": (day_0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": 5,
                }
            )
        frame = pd.DataFrame(rows)
        with pytest.raises(ValueError, match="missing"):
            baselines.evaluate_one_step_ahead(
                frame, "2024-01-04", "2024-01-10",
                baselines.naive_forecast, "gappy",
            )

    def test_item_without_training_history_rejected(self) -> None:
        rows = []
        day_0 = pd.Timestamp("2024-01-01")
        # Rows exist ONLY inside the validation window: nothing before
        # the window start to forecast from.
        for offset in range(10, 15):  # Jan 11..15 = the full window
            rows.append(
                {
                    "store": 1,
                    "item": 2,
                    "date": (day_0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": 5,
                }
            )
        frame = pd.DataFrame(rows)
        with pytest.raises(ValueError, match="no history"):
            baselines.evaluate_one_step_ahead(
                frame, "2024-01-11", "2024-01-15",
                baselines.naive_forecast, "x",
            )

    def test_multi_item_errors_pooled_per_item(self) -> None:
        rows = []
        day_0 = pd.Timestamp("2024-01-01")
        for item in (1, 2):
            for offset in range(12):
                rows.append(
                    {
                        "store": 1,
                        "item": item,
                        "date": (
                            day_0 + pd.Timedelta(days=offset)
                        ).strftime("%Y-%m-%d"),
                        "sales": (item * 10) + offset,
                    }
                )
        frame = pd.DataFrame(rows)
        report = baselines.evaluate_one_step_ahead(
            frame, "2024-01-10", "2024-01-12",
            baselines.naive_forecast, "two-items",
        )
        # Every item-ramp predicts with a 1-unit one-step error.
        assert report.predictions == 6  # 2 items × 3 days
        assert report.mae == pytest.approx(1.0)


class TestEvaluateBaselines:
    def test_all_three_baselines_reported(self, synthetic) -> None:
        reports = baselines.evaluate_baselines(
            synthetic, start="2024-01-11", end="2024-01-16"
        )
        assert set(reports) == {"naive", "moving_average_7",
                                "moving_average_30"}
        for report in reports.values():
            assert report.predictions == 6
        # Ramp series: MA-7 lags far behind a trend, worse than naive.
        assert reports["moving_average_7"].mae > reports["naive"].mae

    def test_reports_serialize_to_dicts(self, synthetic) -> None:
        reports = baselines.evaluate_baselines(
            synthetic, start="2024-01-11", end="2024-01-16"
        )
        naive = reports["naive"].to_dict()
        assert naive["name"] == "naive"
        assert naive["predictions"] == 6
        assert naive["mae"] == pytest.approx(1.0)


@pytest.fixture(scope="class")
def store1():
    """The real preprocessed store-1 dataset (when present)."""
    from smartstock.ml import preprocessing

    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return frame


class TestRealValidationWindow:
    """Dec-056 window numbers pinned to code (doc: baseline-evaluation)."""

    def test_documented_baseline_numbers(self, store1) -> None:
        reports = baselines.evaluate_baselines(store1)  # DEC-056 2016
        assert reports["naive"].to_dict() == {
            "name": "naive", "mae": 10.27, "rmse": 13.761,
            "predictions": 18300,
        }
        assert reports["moving_average_7"].to_dict() == {
            "name": "moving_average_7", "mae": 8.077, "rmse": 10.556,
            "predictions": 18300,
        }
        assert reports["moving_average_30"].to_dict() == {
            "name": "moving_average_30", "mae": 8.298, "rmse": 10.915,
            "predictions": 18300,
        }
        # The 7-day window beats 30 days (weekly seasonality, §7 of the
        # exploration doc) → the historical average = trailing 7 days.
        assert reports["moving_average_7"].mae < reports["moving_average_30"].mae
        # Both averages beat naive on this dataset.
        assert reports["moving_average_7"].mae < reports["naive"].mae
