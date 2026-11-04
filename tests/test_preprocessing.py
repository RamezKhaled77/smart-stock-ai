"""Tests for dataset loading and validation (TASK-006, TASK-007, TASK-008).

Uses small controlled CSV files instead of the full Kaggle dataset,
per docs/06-development/testing-strategy.md.
"""

from pathlib import Path

import pandas as pd
import pytest

from smartstock.ml.preprocessing import (
    DatasetError,
    load_historical_dataset,
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
