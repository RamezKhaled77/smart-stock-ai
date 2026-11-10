"""Tests for forecast inference (TASK-033).

Tiny seeded models verify every policy path cheaply; the real artifact
(skip-guarded) pins behavior against the actual workflow.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from smartstock.ml import inference
from smartstock.ml import model_artifacts as artifacts
from smartstock.ml.features import FEATURE_COLUMNS, build_features


@pytest.fixture(scope="class")
def tiny_artifact():
    """A 40-tree RF trained on a periodic synthetic series (seeded)."""
    rows = []
    for offset in range(120):
        rows.append(
            {
                "store": 1,
                "item": 1,
                "date": (pd.Timestamp("2023-01-01") + pd.Timedelta(days=offset)).strftime("%Y-%m-%d"),
                "sales": 10 + (offset % 7),  # weekly pattern
            }
        )
    frame = pd.DataFrame(rows)
    built = build_features(frame)
    complete = built.dropna(subset=FEATURE_COLUMNS)
    model = RandomForestRegressor(
        n_estimators=40, min_samples_leaf=2, random_state=2026,
        n_jobs=1,
    )
    model.fit(complete[FEATURE_COLUMNS], complete["sales"])
    metadata = artifacts.build_metadata(
        model_name="random_forest",
        model_parameters={"n_estimators": 40},
        dataset_reference="synthetic",
        training_row_count=len(complete),
        evaluation_metrics={"validation_window": {"mae": 1.0}},
    )
    return model, metadata


def daily_frame(values, start="2024-01-01") -> pd.DataFrame:
    start_ts = pd.Timestamp(start)
    return pd.DataFrame(
        {
            "store": 1,
            "item": 1,
            "date": [
                (start_ts + pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
                for offset in range(len(values))
            ],
            "sales": values,
        }
    )


class TestInputValidation:
    def test_unsupported_horizon_rejected(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        with pytest.raises(inference.ForecastError, match="DEC-026"):
            inference.forecast_product(
                model, metadata, daily_frame([1, 2]), horizon_days=5
            )

    def test_empty_history_refused_per_dec058(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        with pytest.raises(inference.ForecastError, match="No suitable"):
            inference.forecast_product(
                model, metadata, daily_frame([]), horizon_days=7
            )

    def test_missing_columns_rejected(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        with pytest.raises(inference.ForecastError, match="missing columns"):
            inference.forecast_product(
                model, metadata, pd.DataFrame([{"date": "2024-01-01"}])
            )

    def test_duplicate_dates_rejected(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        frame = daily_frame([5, 5, 5, 5, 5, 5, 5])
        frame.loc[len(frame)] = [1, 1, "2024-01-03", 5]  # duplicate day
        with pytest.raises(inference.ForecastError, match="duplicate"):
            inference.forecast_product(model, metadata, frame)

    def test_negative_sales_rejected(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        with pytest.raises(inference.ForecastError, match="non-negative"):
            inference.forecast_product(
                model, metadata, daily_frame([5, -1, 3, 5, 5, 5, 5])
            )

    def test_unsorted_input_is_sorted(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        frame = daily_frame(list(range(1, 41)))
        scrambled = frame.sample(frac=1.0, random_state=3)
        result = inference.forecast_product(
            model, metadata, scrambled, horizon_days=7, product_id=1
        )
        # Sorted internally: forecasts continue after the last day.
        assert result["forecast_date"].iloc[0] == pd.Timestamp("2024-02-10")


class TestOutputContract:
    def test_columns_and_count(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame(list(range(1, 41)))
        )
        assert len(result) == 7
        for column in (
            "product_id", "forecast_date", "predicted_demand",
            "model_used", "model_version", "generated_at",
        ):
            assert column in result.columns

    def test_dates_follow_last_observation(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame(list(range(1, 41)))
        )
        dates = result["forecast_date"].tolist()
        assert dates[0] == pd.Timestamp("2024-02-10")
        expected = pd.date_range("2024-02-10", periods=7, freq="D")
        assert list(dates) == list(expected)

    def test_model_version_from_metadata(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame(list(range(1, 41)))
        )
        assert result["model_version"].iloc[0] == metadata["model_version"]

    def test_predictions_are_finite_and_nonnegative(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame(list(range(1, 41)))
        )
        values = result["predicted_demand"].to_numpy()
        assert np.isfinite(values).all()
        assert (values >= 0).all()


class TestDec058Paths:
    def test_model_path_used_for_full_history(self, tiny_artifact) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame(list(range(1, 41)))
        )
        assert set(result["model_used"]) == {"random_forest"}

    def test_fallback_path_used_below_31_days(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        result = inference.forecast_product(
            model, metadata, daily_frame([10] * 10)
        )
        assert set(result["model_used"]) == {"moving_average_7"}
        # Constant history → MA-7 predictions are exactly 10 each day.
        assert result["predicted_demand"].tolist() == [10.0] * 7

    def test_fallback_reduces_to_trailing_mean(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        history = [5, 6, 7, 8, 9, 10, 11]  # 7 obs, MA-7 window full
        result = inference.forecast_product(
            model, metadata, daily_frame(history)
        )
        # Day 1: mean(5..11) = 8; the prediction joins the window:
        # Day 2: mean(6..10 + 8) = wait — window slides: [6,7,8,9,10,11,8]
        #   → mean = 59/7 ≈ 8.428571 (recomputed by hand below).
        day1 = result["predicted_demand"].iloc[0]
        day2 = result["predicted_demand"].iloc[1]
        assert day1 == pytest.approx(8.0)
        expected_day2 = np.mean([6, 7, 8, 9, 10, 11, 8.0])
        assert day2 == pytest.approx(float(expected_day2))

    def test_model_path_matches_manual_feature_math(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        # Trained on a constant series, every leaf holds the same
        # value → predictions equal that constant regardless of dates.
        frame = daily_frame([10.0] * 45, start="2022-01-01")
        built = build_features(frame)
        complete = built.dropna(subset=FEATURE_COLUMNS)
        constant_model = RandomForestRegressor(
            n_estimators=10, random_state=7, n_jobs=1
        )
        constant_model.fit(complete[FEATURE_COLUMNS], complete["sales"])
        result = inference.forecast_product(
            constant_model, metadata, frame[["date", "sales"]]
        )
        np.testing.assert_allclose(
            result["predicted_demand"], [10.0] * 7
        )

    def test_negative_clipping_policy(self, tiny_artifact) -> None:
        _, metadata = tiny_artifact

        class NegativeModel:
            def predict(self, features):
                return [-3.0] * len(features)

        result = inference.forecast_product(
            NegativeModel(), metadata, daily_frame([5.0] * 40)
        )
        # §10 policy: negatives clipped to zero, documented.
        assert result["predicted_demand"].tolist() == [0.0] * 7

    def test_nonfinite_output_rejected(self, tiny_artifact) -> None:
        _, metadata = tiny_artifact

        class InfiniteModel:
            def predict(self, features):
                return [float("nan")] * len(features)

        with pytest.raises(inference.ForecastError, match="non-finite"):
            inference.forecast_product(
                InfiniteModel(), metadata, daily_frame([5.0] * 40)
            )

    def test_recursive_predictions_feed_next_features(
        self, tiny_artifact
    ) -> None:
        model, metadata = tiny_artifact
        # Manual replication of the §8 loop for a flat-then-jump series
        # verifies the model path consumes its own predictions.
        history = [10.0] * 40 + [50.0]  # day 41 jumped to 50
        result = inference.forecast_product(
            model, metadata, daily_frame(history)
        )
        manual_history = list(map(float, history))
        for index in range(7):
            date = pd.Timestamp("2024-02-10") + pd.Timedelta(
                days=index + 1
            )
            row = {
                "day_of_week": float(date.day_of_week),
                "month": float(date.month),
                "day_of_month": float(date.day),
                "lag_1": manual_history[-1],
                "lag_7": float(manual_history[-7]),
                "rolling_mean_7": float(
                    np.mean(manual_history[-7:])
                ),
                "rolling_mean_30": float(
                    np.mean(manual_history[-30:])
                ),
            }
            features = pd.DataFrame(
                [[row[column] for column in FEATURE_COLUMNS]],
                columns=FEATURE_COLUMNS,
            )
            prediction = float(model.predict(features)[0])
            assert result["predicted_demand"].iloc[index] == (
                pytest.approx(max(0.0, prediction))
            )
            manual_history.append(prediction)


@pytest.fixture(scope="class")
def real_forecast_setup():
    """Real artifact + real store-1 frame for skip-guarded pins."""
    from pathlib import Path

    from smartstock.ml import preprocessing

    artifacts_dir = Path("models") / "artifacts"
    if not (artifacts_dir / "demand_model.joblib").is_file():
        pytest.skip("Model artifact not generated in this checkout")
    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    model, metadata = artifacts.load_model_artifact(artifacts_dir)
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return model, metadata, frame


class TestRealArtifact:
    """Skip-guarded pins against the produced artifact + dataset."""

    def test_item1_seven_day_forecast_shape(
        self, real_forecast_setup
    ) -> None:
        model, metadata, frame = real_forecast_setup
        item1 = frame[frame["item"] == 1][["date", "sales"]]
        result = inference.forecast_product(
            model, metadata, item1, horizon_days=7, product_id=1
        )
        assert len(result) == 7
        assert set(result["model_used"]) == {"random_forest"}
        # Continues after the historical dataset's last day.
        assert result["forecast_date"].iloc[0] == pd.Timestamp(
            "2018-01-01"
        )
        assert result["forecast_date"].iloc[-1] == pd.Timestamp(
            "2018-01-07"
        )

    def test_item1_forecast_is_deterministic(
        self, real_forecast_setup
    ) -> None:
        model, metadata, frame = real_forecast_setup
        item1 = frame[frame["item"] == 1][["date", "sales"]]
        first = inference.forecast_product(
            model, metadata, item1, horizon_days=7
        )
        second = inference.forecast_product(
            model, metadata, item1, horizon_days=7
        )
        np.testing.assert_allclose(
            first["predicted_demand"],
            second["predicted_demand"],
            rtol=1e-12,
        )

    def test_short_history_item_uses_fallback(
        self, real_forecast_setup
    ) -> None:
        model, metadata, frame = real_forecast_setup
        short = frame[frame["item"] == 1][["date", "sales"]].tail(20)
        result = inference.forecast_product(model, metadata, short)
        assert set(result["model_used"]) == {"moving_average_7"}
        assert len(result) == 7
