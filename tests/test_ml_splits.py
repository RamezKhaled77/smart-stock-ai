"""Tests for chronological splitting (TASK-029).

Synthetic frames check window selection and guard behavior with
hand-computable row counts; the real DEC-056 dataset pins the actual
calendar-year row counts.
"""

from pathlib import Path

import pandas as pd
import pytest

from smartstock.ml import splits


def daily_frame(dates, items=(1,), store=1) -> pd.DataFrame:
    """Build a frame with one row per date and item."""
    rows = []
    for item in items:
        for date in dates:
            rows.append(
                {
                    "store": store,
                    "item": item,
                    "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                    "sales": len(rows) % 30 + 1,
                }
            )
    return pd.DataFrame(rows)


class TestDefaultWindows:
    def test_dec056_constants(self) -> None:
        assert splits.TRAIN_START == "2013-01-01"
        assert splits.TRAIN_END == "2015-12-31"
        assert splits.VALIDATION_START == "2016-01-01"
        assert splits.VALIDATION_END == "2016-12-31"
        assert splits.TEST_START == "2017-01-01"
        assert splits.TEST_END == "2017-12-31"


class TestSyntheticSplit:
    """Five consecutive days split 2 / 2 / 1 with custom windows."""

    @pytest.fixture
    def frame(self) -> pd.DataFrame:
        return daily_frame(
            ["2023-01-01", "2023-01-02", "2023-01-03",
             "2023-01-04", "2023-01-05"],
            items=(1, 2),
        )

    def split(self, frame):
        return splits.chronological_split(
            frame,
            train_end="2023-01-02",
            validation_start="2023-01-03",
            validation_end="2023-01-04",
            test_start="2023-01-05",
            test_end="2023-01-05",
            train_start="2023-01-01",
        )

    def test_three_non_overlapping_windows(self, frame) -> None:
        train, validation, test = self.split(frame)
        expected = lambda strings: [pd.Timestamp(s) for s in strings]
        assert train["date"].tolist() == expected(
            ["2023-01-01", "2023-01-01", "2023-01-02", "2023-01-02"]
        )
        assert validation["date"].tolist() == expected(
            ["2023-01-03", "2023-01-03", "2023-01-04", "2023-01-04"]
        )
        assert test["date"].tolist() == expected(
            ["2023-01-05", "2023-01-05"]
        )

    def test_no_future_leakage_across_splits(self, frame) -> None:
        train, validation, test = self.split(frame)
        assert train["date"].max() < validation["date"].min()
        assert validation["date"].max() < test["date"].min()

    def test_fresh_indexes_and_sorting(self, frame) -> None:
        scrambled = frame.sample(frac=1.0, random_state=7)
        train, _, _ = self.split(scrambled)
        assert train.index.is_monotonic_increasing
        dates = pd.to_datetime(train["date"])
        assert dates.is_monotonic_increasing

    def test_original_frame_untouched(self, frame) -> None:
        before = frame.copy()
        self.split(frame)
        pd.testing.assert_frame_equal(frame, before)


class TestSplitGuards:
    def test_date_outside_all_windows_refused(self) -> None:
        frame = daily_frame(
            ["2023-01-01", "2023-01-02", "2023-01-03",
             "2023-01-04", "2023-01-05"]
        )
        # 2023-01-03 is deliberately outside every custom window.
        with pytest.raises(
            splits.SplitError, match="outside every split window"
        ):
            splits.chronological_split(
                frame,
                train_end="2023-01-02",
                validation_start="2023-01-04",
                validation_end="2023-01-04",
                test_start="2023-01-05",
                test_end="2023-01-05",
                train_start="2023-01-01",
            )

    def test_reversed_boundaries_rejected(self) -> None:
        frame = daily_frame(
            ["2023-01-01", "2023-01-02", "2023-01-03",
             "2023-01-04", "2023-01-05"]
        )
        with pytest.raises(splits.SplitError, match="strictly increase"):
            splits.chronological_split(
                frame,
                train_end="2023-01-04",
                validation_start="2023-01-03",  # before train_end
                validation_end="2023-01-04",
                test_start="2023-01-05",
                test_end="2023-01-05",
                train_start="2023-01-01",
            )

    def test_per_item_windows(self) -> None:
        # Each item appears exactly once per day across all windows.
        frame = daily_frame(
            ["2023-01-01", "2023-01-02", "2023-01-03",
             "2023-01-04", "2023-01-05"],
            items=(1, 2, 3),
        )
        train, validation, test = splits.chronological_split(
            frame,
            train_end="2023-01-02",
            validation_start="2023-01-03",
            validation_end="2023-01-04",
            test_start="2023-01-05",
            test_end="2023-01-05",
            train_start="2023-01-01",
        )
        assert len(train) == 6    # 3 items × 2 days
        assert len(validation) == 6  # 3 items × 2 days
        assert len(test) == 3     # 3 items × 1 day


@pytest.fixture(scope="class")
def store1():
    """The real preprocessed store-1 dataset (when present)."""
    from smartstock.ml import preprocessing

    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return frame


class TestRealDec056Split:
    """Calendar-year row counts pinned to code (doc: DEC-056)."""

    def test_default_split_row_counts(self, store1) -> None:
        train, validation, test = splits.chronological_split(store1)
        # Calendar years: 2013–2015 = 3 × 365 days; 2016 = 366 (leap);
        # 2017 = 365. 50 items share every day.
        assert len(train) == 50 * 1095 == 54_750
        assert len(validation) == 50 * 366 == 18_300
        assert len(test) == 50 * 365 == 18_250

    def test_windows_are_strictly_chronological(self, store1) -> None:
        train, validation, test = splits.chronological_split(store1)
        assert train["date"].max() == pd.Timestamp("2015-12-31")
        assert validation["date"].min() == pd.Timestamp("2016-01-01")
        assert validation["date"].max() == pd.Timestamp("2016-12-31")
        assert test["date"].min() == pd.Timestamp("2017-01-01")
        assert test["date"].max() == pd.Timestamp("2017-12-31")

    def test_every_window_keeps_all_50_items(self, store1) -> None:
        train, validation, test = splits.chronological_split(store1)
        for part in (train, validation, test):
            assert part["item"].nunique() == 50

    def test_empty_window_rejected(self) -> None:
        frame = daily_frame(
            ["2023-01-01", "2023-01-02", "2023-01-05"]
        )
        # Validation window 01-03 → 01-04 covers no dates at all, while
        # boundaries still strictly increase.
        with pytest.raises(splits.SplitError, match="validation window"):
            splits.chronological_split(
                frame,
                train_end="2023-01-02",
                validation_start="2023-01-03",
                validation_end="2023-01-04",
                test_start="2023-01-05",
                test_end="2023-01-05",
                train_start="2023-01-01",
            )

    def test_bad_columns_and_empty_rejected(self) -> None:
        with pytest.raises(splits.SplitError, match="empty"):
            splits.chronological_split(pd.DataFrame())
        frame = daily_frame(["2023-01-01", "2023-01-02"])
        with pytest.raises(splits.SplitError, match="missing columns"):
            splits.chronological_split(frame.drop(columns=["sales"]))
