"""Tests for the TASK-026 sales exploration module.

Synthetic frames with hand-computable expectations verify the logic;
the real store-1 dataset (when present) verifies the documented
report numbers, ensuring measured facts stay reproducible.
"""

from pathlib import Path

import pandas as pd
import pytest

from smartstock.ml import exploration


@pytest.fixture
def synthetic():
    """Two items × 8 consecutive days starting Monday 2024-01-01.

    Item 1 sells 1..8 (a rising ramp); item 2 sells 10 each day except
    one zero-sale day. Coverage of weekday patterns over two weeks
    keeps expectations simple.
    """
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    rows = []
    for item, values in ((1, range(1, 9)), (2, [10, 10, 10, 0, 4, 5, 6, 7])):
        for date, value in zip(dates, values):
            rows.append(
                {
                    "store": 1,
                    "item": item,
                    "date": date.strftime("%Y-%m-%d"),
                    "sales": value,
                }
            )
    return pd.DataFrame(rows)


class TestOverview:
    def test_overview_facts(self, synthetic) -> None:
        overview = exploration.compute_overview(synthetic)
        assert overview["total_records"] == 16
        assert overview["date_min"] == "2024-01-01"
        assert overview["date_max"] == "2024-01-08"
        assert overview["days_covered"] == 8
        assert overview["item_count"] == 2
        assert overview["zero_sales_records"] == 1

    def test_empty_and_missing_columns_rejected(self, synthetic) -> None:
        with pytest.raises(ValueError, match="empty"):
            exploration.compute_overview(synthetic.iloc[0:0])
        with pytest.raises(ValueError, match="missing columns"):
            exploration.compute_overview(synthetic.drop(columns=["sales"]))


class TestDistribution:
    def test_known_distribution(self, synthetic) -> None:
        stats = exploration.compute_sales_distribution(synthetic)
        # Item 1 sums 36 (1..8), item 2 sums 52 → 88 total over 16 rows.
        assert stats["min"] == 0
        assert stats["max"] == 10
        assert stats["mean"] == pytest.approx(88 / 16)
        # Sorted: 0,1,2,3,4,4,5,5,6,6,7,7,8,10,10,10 → median 5.5.
        assert stats["percentiles"]["50"] == pytest.approx(5.5)

    def test_zero_sales_accepted(self, synthetic) -> None:
        # Zero is a legitimate observation value (dataset fact).
        stats = exploration.compute_sales_distribution(synthetic)
        assert stats["min"] == 0


class TestCalendarPatterns:
    def test_weekday_pattern_labels_and_values(self, synthetic) -> None:
        pattern = exploration.compute_weekday_pattern(synthetic)
        assert list(pattern) == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
                                 "Sun"]
        # Jan 1 and Jan 8 are both Mondays: Jan 1 pairs (1+10)/2 = 5.5,
        # Jan 8 pairs (8+7)/2 = 7.5 → Monday means 6.5.
        assert pattern["Mon"] == pytest.approx(6.5)
        # Tuesday: (2+10)/2 = 6.0 (a single Tuesday).
        assert pattern["Tue"] == pytest.approx(6.0)

    def test_monthly_pattern_keys(self, synthetic) -> None:
        pattern = exploration.compute_monthly_pattern(synthetic)
        assert list(pattern) == [1]
        assert pattern[1] == pytest.approx(88 / 16, abs=0.01)

    def test_yearly_totals(self, synthetic) -> None:
        totals = exploration.compute_yearly_totals(synthetic)
        assert totals[2024] == {
            "total": 88,
            "mean": pytest.approx(88 / 16, abs=0.01),
            "records": 16,
        }


class TestLagCorrelations:
    def test_lags_shift_within_item_not_across_items(
        self, synthetic
    ) -> None:
        # Restricting to item 2 (10,10,10,0,4,5,6,7), lag-1 alignment is
        # internal to the series. A cross-item bug would align item 2's
        # first row against item 1's last row and change the result.
        item2 = synthetic[synthetic["item"] == 2]
        lags = exploration.compute_lag_correlations(item2)
        pairs = (item2.assign(date=lambda f: pd.to_datetime(f["date"]))
                 .sort_values("date"))
        manually = pairs["sales"].corr(pairs["sales"].shift(1))
        assert lags["lag_1"] == pytest.approx(float(manually), abs=5e-4)

    def test_perfect_weekly_period_gives_perfect_lag7(self) -> None:
        # An exactly 7-day periodic series: the lag-7 series equals the
        # original on every comparable pair → correlation exactly 1.
        dates = pd.date_range("2024-01-01", periods=14, freq="D")
        frame = pd.DataFrame(
            {
                "store": 1,
                "item": 1,
                "date": dates.strftime("%Y-%m-%d"),
                "sales": [5, 2, 1, 4, 2, 8, 3] * 2,
            }
        )
        lags = exploration.compute_lag_correlations(frame)
        assert lags["lag_7"] == pytest.approx(1.0)
        assert lags["lag_1"] < 0.5  # unrelated day-to-day ups and downs


class TestItemSummary:
    def test_coverage_and_ranking(self, synthetic) -> None:
        summary = exploration.compute_item_summary(synthetic)
        assert summary["days_per_item_min"] == 8
        assert summary["days_per_item_max"] == 8
        assert summary["weakest_items"][2] == pytest.approx(6.5)
        assert summary["strongest_items"][1] == pytest.approx(4.5)


@pytest.fixture(scope="class")
def store1() -> "pd.DataFrame":
    """The real preprocessed store-1 dataset (when present)."""
    from smartstock.ml import preprocessing

    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    return frame


class TestRealDataset:
    """Documented-report numbers must reproduce from the real dataset.

    These assertions pin the facts in
    ``docs/04-machine-learning/data-exploration.md`` to code so doc
    drift is a test failure.
    """

    def test_documented_overview(self, store1) -> None:
        overview = exploration.compute_overview(store1)
        assert overview["total_records"] == 91_300
        assert overview["date_min"] == "2013-01-01"
        assert overview["date_max"] == "2017-12-31"
        assert overview["item_count"] == 50
        # TASK-005 found exactly one zero-sales record in the FULL
        # dataset; it belongs to another store, so store 1 has none.
        assert overview["zero_sales_records"] == 0

    def test_documented_distribution(self, store1) -> None:
        stats = exploration.compute_sales_distribution(store1)
        assert stats["mean"] == pytest.approx(47.27, abs=0.01)
        assert stats["std"] == pytest.approx(24.01, abs=0.01)
        assert stats["min"] == 1
        assert stats["max"] == 155
        assert stats["percentiles"]["50"] == pytest.approx(44.0, abs=0.01)
        assert stats["percentiles"]["95"] == pytest.approx(92.0, abs=0.01)

    def test_documented_weekday_ramp(self, store1) -> None:
        pattern = exploration.compute_weekday_pattern(store1)
        values = list(pattern.values())
        assert pattern["Mon"] == pytest.approx(37.47, abs=0.01)
        assert pattern["Sun"] == pytest.approx(56.27, abs=0.01)
        # The ramp holds end-to-end: Sunday demand exceeds Monday's.
        assert values[-1] > values[0] * 1.4

    def test_documented_monthly_peak_and_trough(self, store1) -> None:
        pattern = exploration.compute_monthly_pattern(store1)
        assert pattern[7] == pytest.approx(60.66, abs=0.01)  # July peak
        assert pattern[1] == pytest.approx(32.17, abs=0.01)  # Jan trough
        assert max(pattern.values()) > min(pattern.values()) * 1.85

    def test_documented_yearly_growth(self, store1) -> None:
        totals = exploration.compute_yearly_totals(store1)
        assert totals[2013]["mean"] == pytest.approx(39.33, abs=0.01)
        assert totals[2017]["mean"] == pytest.approx(53.25, abs=0.01)
        assert totals[2017]["total"] == 971_774
        if totals[2013]["total"]:
            assert totals[2017]["mean"] > totals[2013]["mean"] * 1.3

    def test_documented_lag_structure(self, store1) -> None:
        lags = exploration.compute_lag_correlations(store1)
        assert lags["lag_7"] == pytest.approx(0.908, abs=0.01)
        assert lags["lag_1"] == pytest.approx(0.852, abs=0.01)
        assert lags["lag_30"] == pytest.approx(0.793, abs=0.01)
        # lag_7 strongest: weekly seasonality is the dominant pattern.
        assert lags["lag_7"] == max(lags.values())

    def test_documented_item_coverage(self, store1) -> None:
        summary = exploration.compute_item_summary(store1)
        assert summary["days_per_item_min"] == 1826
        assert summary["days_per_item_max"] == 1826
