"""Tests for dataset loading and validation (TASK-006, TASK-007, TASK-008).

Uses small controlled CSV files instead of the full Kaggle dataset,
per docs/06-development/testing-strategy.md.
"""

from pathlib import Path

import pandas as pd
import pytest

from smartstock.ml.preprocessing import (
    DatasetError,
    detect_date_gaps,
    filter_store,
    load_historical_dataset,
    preprocess_dataset,
    sort_chronologically,
    validate_and_parse_dataset,
)

VALID_CSV = """date,store,item,sales
2013-01-01,1,1,13
2013-01-02,1,1,11
"""

VALID_CSV_PATH = Path(__file__).parent / "fixtures" / "valid_small.csv"


@pytest.fixture(scope="module")
def valid_csv(tmp_path_factory) -> Path:
    """A small valid dataset file available for the whole test module."""
    path = tmp_path_factory.mktemp("data") / "valid_small.csv"
    path.write_text(VALID_CSV)
    return path


@pytest.fixture(scope="module")
def empty_csv(tmp_path_factory) -> Path:
    """A CSV file with headers only (no data rows)."""
    path = tmp_path_factory.mktemp("data") / "empty.csv"
    path.write_text("date,store,item,sales\n")
    return path


@pytest.fixture(scope="module")
def missing_column_csv(tmp_path_factory) -> Path:
    """A CSV file missing the required `sales` column."""
    path = tmp_path_factory.mktemp("data") / "missing_column.csv"
    path.write_text("date,store,item\n2013-01-01,1,1\n")
    return path


@pytest.fixture(scope="module")
def not_readable_csv(tmp_path_factory) -> Path:
    """A CSV with an unclosed quote that pandas cannot parse."""
    path = tmp_path_factory.mktemp("data") / "broken.csv"
    path.write_text('date,store,item,sales\n"unclosed,1,1\n')
    return path


class TestLoadHistoricalDataset:
    """Loader behavior: valid files, missing files, and bad files."""

    def test_loads_valid_file(self, valid_csv: Path) -> None:
        df = load_historical_dataset(valid_csv)

        assert list(df.columns) == ["date", "store", "item", "sales"]
        assert len(df) == 2
        assert df.loc[0, "sales"] == 13

    def test_missing_file_raises_clear_error(self, tmp_path: Path) -> None:
        with pytest.raises(DatasetError, match="not found"):
            load_historical_dataset(tmp_path / "does_not_exist.csv")

    def test_empty_file_raises_clear_error(self, empty_csv: Path) -> None:
        with pytest.raises(DatasetError, match="no records"):
            load_historical_dataset(empty_csv)

    def test_missing_column_raises_clear_error(
        self, missing_column_csv: Path
    ) -> None:
        with pytest.raises(DatasetError, match="missing required columns"):
            load_historical_dataset(missing_column_csv)

    def test_unreadable_file_raises_clear_error(
        self, not_readable_csv: Path
    ) -> None:
        with pytest.raises(DatasetError, match="Could not read"):
            load_historical_dataset(not_readable_csv)

    def test_error_message_includes_path(self, tmp_path: Path) -> None:
        path = tmp_path / "any_file.csv"
        with pytest.raises(DatasetError) as excinfo:
            load_historical_dataset(path)
        assert "any_file.csv" in str(excinfo.value)


def _df_from_csv(text: str) -> pd.DataFrame:
    """Build an in-memory DataFrame from raw CSV text."""
    import io

    return pd.read_csv(io.StringIO(text))


class TestValidateAndParseDataset:
    """Validation behavior: valid data accepted, invalid data rejected."""

    def test_valid_data_is_accepted_and_typed(self) -> None:
        df = _df_from_csv(VALID_CSV)
        result = validate_and_parse_dataset(df)

        assert str(result["date"].dtype).startswith("datetime64")
        assert str(result["store"].dtype) == "int64"
        assert str(result["item"].dtype) == "int64"
        assert pd.api.types.is_numeric_dtype(result["sales"])

    def test_missing_value_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,1,1,\n")
        with pytest.raises(DatasetError, match="missing 'sales'"):
            validate_and_parse_dataset(df)

    def test_missing_identifier_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,,1,5\n")
        with pytest.raises(DatasetError, match="missing 'store'"):
            validate_and_parse_dataset(df)

    def test_nonnumeric_sales_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,1,1,abc\n")
        with pytest.raises(DatasetError, match="nonnumeric 'sales'"):
            validate_and_parse_dataset(df)

    def test_noninteger_identifier_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,1.5,1,5\n")
        with pytest.raises(DatasetError, match="noninteger 'store'"):
            validate_and_parse_dataset(df)

    def test_invalid_date_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "not-a-date,1,1,5\n")
        with pytest.raises(DatasetError, match="invalid 'date'"):
            validate_and_parse_dataset(df)

    def test_negative_sales_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,1,1,-4\n")
        with pytest.raises(DatasetError, match="negative 'sales'"):
            validate_and_parse_dataset(df)

    def test_duplicate_key_is_rejected(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-02,1,1,9\n")
        with pytest.raises(DatasetError, match="duplicate"):
            validate_and_parse_dataset(df)

    def test_positive_fractional_sales_is_accepted(self) -> None:
        # Fractional sales are flagged in reports, not rejected outright.
        df = _df_from_csv("date,store,item,sales\n2013-01-01,1,1,2.5\n")
        result = validate_and_parse_dataset(df)
        assert result.loc[0, "sales"] == 2.5

    def test_input_frame_is_not_mutated(self) -> None:
        df = _df_from_csv(VALID_CSV)
        validate_and_parse_dataset(df)
        # date stays unparsed (string) in the original frame
        assert not pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_error_reports_source_name(self) -> None:
        df = _df_from_csv(VALID_CSV + "2013-01-03,1,1,\n")
        with pytest.raises(DatasetError, match="train.csv"):
            validate_and_parse_dataset(df, source_name="train.csv")


def _validated_two_store_df() -> pd.DataFrame:
    """A small validated dataset with two stores and a date gap."""
    csv_text = (
        "date,store,item,sales\n"
        "2013-01-02,1,1,11\n"
        "2013-01-01,1,1,13\n"
        "2013-01-01,2,1,7\n"
        "2013-01-02,2,1,9\n"
        "2013-01-03,2,1,4\n"
        "2013-01-01,1,2,2\n"
        "2013-01-03,1,2,3\n"
    )
    return validate_and_parse_dataset(_df_from_csv(csv_text))


class TestFilterStore:
    """Store filtering per DEC-015 (one store, item -> product)."""

    def test_keeps_only_selected_store(self) -> None:
        df = _validated_two_store_df()
        result = filter_store(df, store_id=1)
        assert set(result["store"]) == {1}
        assert len(result) == 4

    def test_unknown_store_raises_with_available_list(self) -> None:
        df = _validated_two_store_df()
        with pytest.raises(DatasetError, match="Available stores"):
            filter_store(df, store_id=99)


class TestSortChronologically:
    """Sorting by store, item, then date."""

    def test_sorts_by_store_item_date(self) -> None:
        df = _validated_two_store_df()
        result = sort_chronologically(df)
        # Stores in ascending order; dates ascending within each series.
        assert list(result["store"]) == sorted(result["store"])
        grouped = result.groupby(["store", "item"])["date"]
        for _, dates in grouped:
            assert list(dates) == sorted(dates)
        # Date gap remains visible: store 1 item 2 skips 2013-01-02.
        item2_dates = sorted(
            result.loc[
                (result["store"] == 1) & (result["item"] == 2), "date"
            ].dt.strftime("%Y-%m-%d")
        )
        assert "2013-01-02" not in item2_dates


class TestDetectDateGaps:
    """Daily-sequence completeness checking."""

    def test_reports_gap_for_incomplete_series(self) -> None:
        df = sort_chronologically(filter_store(
            _validated_two_store_df(), store_id=1
        ))
        gaps = detect_date_gaps(df)
        assert gaps["combinations_checked"] == 2
        assert gaps["combinations_with_gaps"] == 1
        assert gaps["total_missing_dates"] == 1

    def test_reports_no_gap_for_complete_series(self) -> None:
        df = _validated_two_store_df()
        # Store 2 has three consecutive days for item 1.
        store2 = df[df["store"] == 2]
        gaps = detect_date_gaps(store2)
        assert gaps == {
            "combinations_checked": 1,
            "combinations_with_gaps": 0,
            "total_missing_dates": 0,
        }


class TestPreprocessDataset:
    """End-to-end pipeline on a small CSV file."""

    def test_pipeline_returns_sorted_store_1_data(self, valid_csv: Path) -> None:
        result, report = preprocess_dataset(valid_csv, store_id=1)
        assert list(result["store"]) == [1, 1]
        assert list(result["date"].dt.strftime("%Y-%m-%d")) == [
            "2013-01-01", "2013-01-02",
        ]
        assert report["prepared_record_count"] == 2
        assert report["source_record_count"] == 2
        assert report["product_count"] == 1
        assert report["total_missing_dates"] == 0

    def test_pipeline_rejects_unknown_store(self, valid_csv: Path) -> None:
        with pytest.raises(DatasetError, match="Available stores"):
            preprocess_dataset(valid_csv, store_id=42)
