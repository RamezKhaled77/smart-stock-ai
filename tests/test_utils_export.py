"""Tests for the CSV export helper (TASK-049, DEC-063)."""

from smartstock.utils.export import to_csv


class TestToCsv:
    def test_header_and_rows_in_column_order(self) -> None:
        rows = [
            {"sku": "SKU-A", "units_sold": 35, "name": "Item A"},
            {"sku": "SKU-B", "units_sold": 3, "name": "Item B"},
        ]
        text = to_csv(rows, ["sku", "name", "units_sold"])
        lines = text.splitlines()
        assert lines[0] == "sku,name,units_sold"
        assert lines[1] == "SKU-A,Item A,35"
        assert lines[2] == "SKU-B,Item B,3"

    def test_missing_values_become_empty_cells(self) -> None:
        rows = [{"sku": "SKU-C", "trend": None}]
        text = to_csv(rows, ["sku", "trend", "first_sale"])
        assert text.splitlines()[1] == "SKU-C,,"

    def test_empty_rows_yield_header_only(self) -> None:
        assert to_csv([], ["a", "b"]) == "a,b\r\n"

    def test_csv_quoting_and_rfc4180_line_endings(self) -> None:
        rows = [{"name": 'Widget "Pro", large', "note": "line\nbreak"}]
        text = to_csv(rows, ["name", "note"])
        # RFC 4180: CRLF endings, quotes doubled, field quoted.
        assert text.endswith('"line\nbreak"\r\n')
        assert '"Widget ""Pro"", large"' in text

    def test_extra_keys_ignored(self) -> None:
        rows = [{"a": 1, "hidden": "x"}]
        text = to_csv(rows, ["a"])
        assert "hidden" not in text