"""Tests for historical CSV import validation (TASK-022)."""

import io

import pandas as pd
import pytest

from smartstock.domain import csv_import


def _csv_bytes(content: str) -> io.BytesIO:
    return io.BytesIO(content.encode("utf-8"))


def _all_reasons(report: csv_import.RowAnalysis) -> str:
    return " | ".join(reason for _, reason in report.rejected_rows)


# Store 1 rows: rows 1 and 4 share the (item=1, 2013-01-01) key.
# Row 2 belongs to store 2 (out of scope per DEC-015), not an error.
VALID_CSV = """date,store,item,sales
2013-01-01,1,1,13
2013-01-01,2,1,7
2013-01-02,1,2,9
2013-01-01,1,1,5
"""


@pytest.fixture
def analysis() -> csv_import.RowAnalysis:
    return csv_import.analyze_rows(
        csv_import.read_csv_file(_csv_bytes(VALID_CSV))
    )


class TestReadCsvFile:
    def test_reads_valid_csv(self) -> None:
        frame = csv_import.read_csv_file(_csv_bytes(VALID_CSV))
        assert list(frame.columns) == ["date", "store", "item", "sales"]
        assert len(frame) == 4

    def test_empty_file_rejected(self) -> None:
        with pytest.raises(csv_import.CsvFileError, match="no CSV data"):
            csv_import.read_csv_file(_csv_bytes(""))

    def test_header_only_file_rejected(self) -> None:
        with pytest.raises(csv_import.CsvFileError, match="no data rows"):
            csv_import.read_csv_file(
                _csv_bytes("date,store,item,sales\n")
            )

    def test_read_from_path_string(self, tmp_path) -> None:
        file = tmp_path / "sample.csv"
        file.write_text(VALID_CSV)
        assert len(csv_import.read_csv_file(file)) == 4


class TestFileStructure:
    def _read(self) -> pd.DataFrame:
        return csv_import.read_csv_file(_csv_bytes(VALID_CSV))

    def test_correct_structure_passes(self) -> None:
        csv_import.validate_file_structure(self._read())

    def test_missing_column_rejected(self) -> None:
        with pytest.raises(
            csv_import.CsvStructureError, match="Missing required columns"
        ) as excinfo:
            csv_import.validate_file_structure(self._read().drop(columns=["sales"]))
        assert "sales" in str(excinfo.value)

    def test_extra_column_rejected(self) -> None:
        frame = self._read()
        frame["price"] = "3.5"
        with pytest.raises(
            csv_import.CsvStructureError, match="Unexpected columns"
        ) as excinfo:
            csv_import.validate_file_structure(frame)
        assert "price" in str(excinfo.value)

    def test_duplicated_column_names_rejected(self) -> None:
        # pandas auto-renames a repeated "sales" to "sales.1"; the
        # unexpected-column check must reject the mangled import.
        content = "date,store,item,sales,sales\n2013-01-01,1,1,13,20\n"
        frame = csv_import.read_csv_file(_csv_bytes(content))
        with pytest.raises(
            csv_import.CsvStructureError, match="Unexpected columns"
        ) as excinfo:
            csv_import.validate_file_structure(frame)
        assert "sales.1" in str(excinfo.value)


class TestAnalyzeRows:
    def test_valid_file_classification(self, analysis) -> None:
        assert analysis.total_rows == 4
        # Row 2 is store 2: skipped as out of scope (DEC-015), not an error.
        assert analysis.out_of_store_rows == 1
        assert analysis.invalid_row_count == 0
        # Rows 1 and 4 repeat (item 1, 2013-01-01): first stays valid.
        assert analysis.duplicate_rows == [
            (4, "duplicate (item, date) within the file: item 1, "
                "date 2013-01-01"),
        ]
        assert len(analysis.valid_rows) == 2

    def test_valid_rows_keep_storage_values(self, analysis) -> None:
        rows = analysis.valid_rows.sort_values(by="date").to_dict(
            orient="records"
        )
        assert rows == [
            {"date": "2013-01-01", "store": 1, "item": 1, "sales": 13},
            {"date": "2013-01-02", "store": 1, "item": 2, "sales": 9},
        ]

    def test_date_range_covers_accepted_rows(self, analysis) -> None:
        assert analysis.date_range == ("2013-01-01", "2013-01-02")

    def test_in_scope_rows_count(self, analysis) -> None:
        assert analysis.in_scope_rows == 3

    def test_other_store_files_are_not_errors_but_empty(self) -> None:
        content = "date,store,item,sales\n2013-01-01,3,1,13\n"
        analysis = csv_import.analyze_rows(
            csv_import.read_csv_file(_csv_bytes(content))
        )
        assert analysis.out_of_store_rows == 1
        assert len(analysis.valid_rows) == 0
        assert analysis.invalid_row_count == 0
        assert analysis.date_range is None


class TestRowValidation:
    INVALID_CSV = """date,store,item,sales
2013-01-01,1,1,13
not-a-date,1,1,4
2013-02-30,1,1,4
2013-01-01,1,1,-3
2013-01-01,1,1,2.5
2013-01-01,1,3.5,4
2013-01-01,ab,2,4
,,1,4
2013-01-02,1,1,0
"""

    @pytest.fixture
    def report(self) -> csv_import.RowAnalysis:
        return csv_import.analyze_rows(
            csv_import.read_csv_file(_csv_bytes(self.INVALID_CSV))
        )

    def test_rejected_row_count(self, report) -> None:
        # Rows 2-8 are invalid; row 9 (zero sales) is valid.
        assert report.invalid_row_count == 7

    def test_invalid_text_date_rejected(self, report) -> None:
        assert "not a valid date" in _all_reasons(report)

    def test_impossible_calendar_date_rejected(self, report) -> None:
        # 2013-02-30 does not exist and must not silently pass.
        assert any(
            "2013-02-30" in reason for _, reason in report.rejected_rows
        )

    def test_negative_sales_rejected(self, report) -> None:
        assert any("'-3'" in reason for _, reason in report.rejected_rows)

    def test_fractional_sales_rejected(self, report) -> None:
        assert any("'2.5'" in reason for _, reason in report.rejected_rows)

    def test_fractional_item_rejected(self, report) -> None:
        assert any("item" in reason for _, reason in report.rejected_rows
                   if "'3.5'" in reason)

    def test_non_numeric_store_rejected(self, report) -> None:
        assert any(
            "'ab'" in reason for _, reason in report.rejected_rows
        )

    def test_missing_values_reported(self, report) -> None:
        reasons = _all_reasons(report)
        assert "date is missing" in reasons
        assert "store is missing" in reasons

    def test_zero_sales_is_valid(self, report) -> None:
        # The dataset contains exactly one zero-sales observation, so
        # zero must be accepted (DEC-052 preserves source meaning).
        # Valid rows: row 1 (2013-01-01) and row 9 (2013-01-02, zero).
        assert (report.valid_rows["sales"] == 0).any()
        assert len(report.valid_rows) == 2
        assert report.date_range == ("2013-01-01", "2013-01-02")

    def test_row_numbers_increase_in_file_order(self, report) -> None:
        numbers = [number for number, _ in report.rejected_rows]
        assert numbers == sorted(numbers)
        assert all(1 <= number <= report.total_rows for number in numbers)


class TestCountProperties:
    def test_count_properties_consistent(self, analysis) -> None:
        assert analysis.in_scope_rows == (
            analysis.total_rows - analysis.out_of_store_rows
        )
        assert analysis.invalid_row_count == len(analysis.rejected_rows)
        assert analysis.duplicate_row_count == len(analysis.duplicate_rows)
