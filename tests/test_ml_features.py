"""Tests for the feature engineering pipeline (TASK-028).

Synthetic frames with hand-computable expectations verify sorting,
per-series grouping, lags, shifted rolling means, and calendar
features; the real DEC-056 dataset pins documented behavior.
"""

import numpy as np
import pandas as pd
import pytest

from smartstock.ml import features


@pytest.fixture
def ramp_frame():
    """One store, one item, 10 consecutive days with sales 1..10.

    Day rows are intentionally inserted out of order to prove the
    pipeline sorts chronologically before lagging.
    """
    day0 = pd.Timestamp("2024-01-01")
    rows = []
    for offset in range(10):
        rows.append(
            {
                "store": 1,
                "item": 1,
                "date": (day0 + pd.Timedelta(days=offset)).strftime(
                    "%Y-%m-%d"
                ),
                "sales": offset + 1,
            }
        )
    frame = pd.DataFrame(rows)
    return frame.sample(frac=1.0, random_state=0)  # scrambled order


@pytest.fixture
def interleaved_frame():
    """Two items, rows interleaved, different series values.

    A cross-item lag bug would create impossible feature values here
    (e.g., item 2's first row lagging item 1's last value).
    """
    day0 = pd.Timestamp("2024-01-01")
    rows = []
    for item, values in ((1, list(range(1, 10))), (2, [100, 200, 300,
                                                       400, 500, 600,
                                                       700, 800, 900])):
        for offset, value in enumerate(values):
            rows.append(
                {
                    "store": 1,
                    "item": item,
                    "date": (day0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": value,
                }
            )
    return pd.DataFrame(rows)


class TestInputValidation:
    def test_empty_frame_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            features.build_features(pd.DataFrame())

    def test_missing_columns_rejected(self, ramp_frame) -> None:
        with pytest.raises(ValueError, match="Missing required columns"):
            features.build_features(ramp_frame.drop(columns=["sales"]))


class TestCalendarFeatures:
    def test_date_features_from_MONDAY_start(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame.sort_values("date"))
        first = built.sort_values("date").iloc[0]
        assert first["day_of_week"] == 0  # 2024-01-01 = Monday
        assert first["month"] == 1
        assert first["day_of_month"] == 1

    def test_sunday_and_month_boundary(self) -> None:
        frame = pd.DataFrame(
            [
                {"store": 1, "item": 1, "date": "2024-01-31", "sales": 1},
                {"store": 1, "item": 1, "date": "2024-02-01", "sales": 2},
            ]
        )
        built = features.build_features(frame).sort_values("date")
        assert built.iloc[0]["day_of_month"] == 31
        assert built.iloc[0]["month"] == 1
        assert built.iloc[0]["day_of_week"] == 2  # Wednesday
        assert built.iloc[1]["day_of_month"] == 1
        assert built.iloc[1]["month"] == 2


class TestLagFeatures:
    def test_sorting_happens_before_lagging(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame)
        ordered = built.sort_values("date")
        # Row order proves nothing by itself; values prove the lags were
        # built on a chronologically sorted series (sales = offset + 1).
        lags = ordered["lag_1"].tolist()
        assert lags[7] == 7  # obs 6's value
        assert lags[9] == 9  # obs 8's value

    def test_lag_values(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame).sort_values("date")
        expect_lag1 = np.array([np.nan] + list(range(1, 10)))
        expect_lag7 = np.array([np.nan] * 7 + [1.0, 2.0, 3.0])
        np.testing.assert_allclose(built["lag_1"], expect_lag1, equal_nan=True)
        np.testing.assert_allclose(built["lag_7"], expect_lag7, equal_nan=True)

    def test_lags_stay_within_each_series(self, interleaved_frame) -> None:
        built = features.build_features(interleaved_frame)
        item2 = built[built["item"] == 2].sort_values("date")
        # Item 2's lag_1 must come from item 2's own series (100, 200...).
        expect = np.array([np.nan] + [100.0, 200.0, 300.0, 400.0, 500.0,
                                      600.0, 700.0, 800.0])
        np.testing.assert_allclose(
            item2["lag_1"].to_numpy(), expect, equal_nan=True
        )
        # A cross-item bug would produce neighbors' values like 9 here.
        assert item2["lag_1"].iloc[1] == 100

    def test_same_date_does_not_create_cross_item_lags(
        self, interleaved_frame
    ) -> None:
        # Both items share identical dates; grouping must be per series.
        built = features.build_features(interleaved_frame)
        item1 = built[built["item"] == 1].sort_values("date")
        assert item1["lag_1"].iloc[1] == 1  # item 1's own day 1 value


class TestRollingFeatures:
    def test_rolling_means_exclude_current_target(self) -> None:
        # A single outlier day proves the target is not in its own
        # window: with sales 7..12 on days 8..10 (window covers days
        # 1..7 / 2..8 / 3..9), the outlier 12 must NOT affect day 10.
        day0 = pd.Timestamp("2024-01-01")
        rows = []
        for offset in range(10):
            value = 100 if offset == 9 else offset + 1  # obs 10 = 100
            rows.append(
                {
                    "store": 1,
                    "item": 1,
                    "date": (day0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": value,
                }
            )
        built = features.build_features(pd.DataFrame(rows))
        day10 = built[built["date"] == "2024-01-10"].iloc[0]
        # Window covers obs 2..8 (values 3..9): outlier 100 NOT inside.
        assert day10["rolling_mean_7"] == pytest.approx(6.0)
        # lag_1 also safe: yesterday was 9, not the outlier.
        assert day10["lag_1"] == 9

    def test_rolling_mean_7_window_contents(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame).sort_values("date")
        values = built["rolling_mean_7"].tolist()
        assert all(np.isnan(v) for v in values[:7])
        # Day 8 (obs 7): mean of obs 0..6 → (1+..+7)/7 = 4.0.
        assert values[7] == pytest.approx(4.0)
        # Day 9: mean of obs 1..7 → (2+..+8)/7 = 5.0.
        assert values[8] == pytest.approx(5.0)

    def test_rolling_mean_30_needs_31_observations(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame)
        assert built["rolling_mean_30"].isna().all()  # only 10 days

    def test_rolling_mean_30_value_with_full_history(self) -> None:
        day0 = pd.Timestamp("2024-01-01")
        rows = []
        for offset in range(32):
            rows.append(
                {
                    "store": 1,
                    "item": 1,
                    "date": (day0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": offset + 1,
                }
            )
        built = features.build_features(pd.DataFrame(rows)).sort_values(
            "date"
        )
        rm30 = built["rolling_mean_30"].tolist()
        assert all(np.isnan(v) for v in rm30[:30])
        # Obs 30 (0-based): window covers obs 0..29 → (1+..+30)/30 = 15.5.
        assert rm30[30] == pytest.approx(15.5)
        # Obs 31: window covers obs 1..30 → 16.5.
        assert rm30[31] == pytest.approx(16.5)

    def test_rolling_features_stay_within_each_series(
        self, interleaved_frame
    ) -> None:
        built = features.build_features(interleaved_frame)
        item2 = built[built["item"] == 2].sort_values("date")
        # Item 2's rolling_mean_7 first non-NaN at obs 7: mean of item-2
        # obs 0..6 = (100+...+700)/7 = 400. A cross-item bug would mix
        # in item 1's small values.
        values = item2["rolling_mean_7"].tolist()
        assert all(np.isnan(v) for v in values[:7])
        assert values[7] == pytest.approx(400.0)
        assert values[8] == pytest.approx(500.0)


class TestOutputContract:
    def test_feature_columns_constant_order(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame)
        assert list(built.columns[-7:]) == features.FEATURE_COLUMNS

    def test_original_columns_preserved(self, ramp_frame) -> None:
        built = features.build_features(ramp_frame)
        for column in ("store", "item", "date", "sales"):
            assert column in built.columns

    def test_no_arbitrary_fills_in_lags(self, ramp_frame) -> None:
        # Early rows keep NaN; nothing is coerced to 0 or the mean.
        built = features.build_features(ramp_frame)
        assert built["rolling_mean_30"].isna().sum() == 10


class TestDropAndSplit:
    def test_drop_rows_without_features_keeps_full_rows_only(
        self,
    ) -> None:
        day0 = pd.Timestamp("2024-01-01")
        rows = []
        for offset in range(33):
            rows.append(
                {
                    "store": 1,
                    "item": 1,
                    "date": (day0 + pd.Timedelta(days=offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": offset + 1,
                }
            )
        built = features.build_features(pd.DataFrame(rows))
        complete = features.drop_rows_without_features(built)
        # rolling_mean_30 needs 30 past observations; the first complete
        # row is obs index 30 → 33 obs keep 3 rows (values 31, 32, 33).
        assert len(complete) == 3
        assert complete["sales"].tolist() == [31, 32, 33]
        assert complete[features.FEATURE_COLUMNS].notna().all().all()

    def test_drop_rejects_missing_columns_and_empty(self, ramp_frame) -> None:
        with pytest.raises(ValueError, match="Missing required columns"):
            features.drop_rows_without_features(
                ramp_frame.drop(columns=["sales"])
            )
        with pytest.raises(ValueError, match="empty"):
            features.drop_rows_without_features(pd.DataFrame())

    def test_feature_matrix_shapes(self) -> None:
        n = 42  # 42 obs → first complete at obs 30 → 12 complete rows
        day0 = pd.Timestamp("2024-01-01")
        frame = pd.DataFrame(
            {
                "store": 1,
                "item": 1,
                "date": (
                    pd.Timestamp("2024-01-01")
                    + pd.to_timedelta(pd.RangeIndex(n), unit="D")
                ).strftime("%Y-%m-%d"),
                "sales": list(range(1, n + 1)),
            }
        )
        X, y = features.feature_matrix(features.build_features(frame))
        assert list(X.columns) == features.FEATURE_COLUMNS
        assert "sales" not in X.columns
        assert len(X) == len(y) == n - 30
        assert X.notna().all().all()


@pytest.fixture(scope="class")
def store1():
    """The real preprocessed store-1 dataset (when present)."""
    from smartstock.ml import preprocessing
    from pathlib import Path

    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return frame


class TestRealDataset:
    def test_real_pipeline_shapes(self, store1) -> None:
        built = features.build_features(store1)
        assert len(built) == 91_300
        assert list(built.columns[-7:]) == features.FEATURE_COLUMNS

    def test_real_dec056_training_rows(self, store1) -> None:
        # 50 items × 1,826 obs; the first 30 obs of every item have NaN
        # rolling_mean_30 → complete rows = 50 × (1826 - 30) = 89,800.
        complete = features.drop_rows_without_features(
            features.build_features(store1)
        )
        assert len(complete) == 50 * (1826 - 30)

    def test_real_no_current_day_leakage(self, store1) -> None:
        # On 2016-12-31 the lag-1 feature must hold 2016-12-30's sales.
        built = features.build_features(store1)
        day = built[built["date"] == "2016-12-31"]
        previous = built[built["date"] == "2016-12-30"].set_index("item")[
            "sales"
        ]
        check = day.set_index("item")["lag_1"]
        assert (check == previous).all()

    def test_real_known_feature_value(self, store1) -> None:
        # Item 1: 2013-02-01 is obs index 31 (0-based 2013-01-01 = 0).
        # At obs 31: lag_1 = obs 30, lag_7 = obs 24, rolling_mean_7 =
        # mean of obs 24..30 (2013-01-25 .. 2013-01-31).
        built = features.build_features(store1)
        row = built[
            (built["item"] == 1) & (built["date"] == "2013-02-01")
        ].iloc[0]
        per_item = store1[store1["item"] == 1].sort_values("date")
        assert row["lag_1"] == float(per_item["sales"].iloc[30])
        assert row["lag_7"] == float(per_item["sales"].iloc[24])
        assert row["rolling_mean_7"] == pytest.approx(
            float(per_item["sales"].iloc[24:31].mean()), abs=1e-9
        )
