"""Tests for the historical import preview (TASK-023).

Covers the service-level preview summary and the Data Import page with
Streamlit AppTest (page services resolve ``config.DATABASE_PATH`` at
call time; no real database is touched — preview reads files only).
"""

import hashlib
import io
from pathlib import Path

import pytest

from smartstock.domain.csv_import import CsvStructureError

VALID_CSV = """date,store,item,sales
2013-01-01,1,1,13
2013-01-02,1,1,11
2013-01-03,1,2,9
2013-01-03,2,1,7
2013-01-03,1,3,-1
"""


def _upload(content: str = VALID_CSV, name: str = "train.csv") -> tuple:
    """Upload tuple as accepted by ``FileUploader.set_value``."""
    return (name, content.encode("utf-8"), "text/csv")


def _named_stream(content: str, name: str = "file.csv") -> io.BytesIO:
    """Named stream as the service receives from real uploads."""
    stream = io.BytesIO(content.encode("utf-8"))
    stream.name = name
    return stream


def _run_page():
    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_string(
        "from smartstock.pages.imports import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


class TestPreviewService:
    def test_preview_summary_fields(self) -> None:
        from smartstock.services import import_service

        content = VALID_CSV.encode("utf-8")
        preview = import_service.preview_import(
            _named_stream(VALID_CSV, name="train.csv")
        )
        assert preview.filename == "train.csv"
        assert preview.file_size_bytes == len(content)
        assert preview.sha256_fingerprint == hashlib.sha256(
            content
        ).hexdigest()
        assert preview.store == 1
        assert preview.total_rows == 5
        assert preview.valid_row_count == 3
        assert preview.invalid_in_scope_rows == 1
        assert preview.out_of_store_rows == 1
        assert preview.in_scope_rows == 4
        assert preview.duplicate_row_count == 0
        assert preview.date_range == ("2013-01-01", "2013-01-03")
        assert preview.importable is True

    def test_identical_content_same_fingerprint_despite_names(
        self, tmp_path: Path
    ) -> None:
        # DEC-053: the fingerprint hashes bytes, so a renamed copy of
        # the same file is still the exact same upload.
        from smartstock.services import import_service

        file_a = tmp_path / "a.csv"
        file_b = tmp_path / "b.csv"
        file_a.write_text(VALID_CSV)
        file_b.write_text(VALID_CSV)
        preview_a = import_service.preview_import(file_a)
        preview_b = import_service.preview_import(file_b)
        assert (
            preview_a.sha256_fingerprint == preview_b.sha256_fingerprint
        )
        assert preview_a.filename != preview_b.filename

    def test_preview_sample_rows_capped(self) -> None:
        from smartstock.services import import_service

        rows = ["date,store,item,sales"]
        for day in range(1, 201):
            rows.append(
                f"2013-{(day - 1) // 28 + 1:02d}-{(day - 1) % 28 + 1:02d},"
                f"1,{day % 5 + 1},{(day % 9) + 1}"
            )
        preview = import_service.preview_import(
            _named_stream("\n".join(rows) + "\n", name="many.csv")
        )
        assert preview.valid_row_count == 200
        assert len(preview.sample_rows) == 5
        assert preview.sample_rows[0]["date"] == "2013-01-01"
        assert preview.date_range == ("2013-01-01", "2013-08-04")

    def test_rejected_examples_capped_with_full_count(self) -> None:
        from smartstock.services import import_service

        rows = ["date,store,item,sales", "2013-01-01,1,1,5"]
        for index in range(1, 10):
            rows.append(f"bad-date-{index},1,1,5")
        preview = import_service.preview_import(
            _named_stream("\n".join(rows) + "\n", name="broken.csv")
        )
        assert preview.valid_row_count == 1
        assert preview.invalid_in_scope_rows == 9  # full count
        assert len(preview.rejected_rows) == 5  # examples only
        assert preview.rejected_truncated is True

    def test_in_file_duplicates_capped_with_full_count(self) -> None:
        from smartstock.services import import_service

        rows = ["date,store,item,sales", "2013-01-01,1,1,5"]
        for _ in range(8):
            rows.append("2013-01-01,1,1,5")
        preview = import_service.preview_import(
            _named_stream("\n".join(rows) + "\n", name="dup.csv")
        )
        assert preview.valid_row_count == 1
        assert preview.duplicate_row_count == 8
        assert len(preview.duplicate_rows) == 5
        assert preview.duplicate_truncated is True

    def test_file_level_errors_raise(self) -> None:
        from smartstock.domain.csv_import import CsvFileError
        from smartstock.services import import_service

        with pytest.raises(CsvFileError, match="no CSV data"):
            import_service.preview_import(
                _named_stream("", name="empty.csv")
            )

    def test_structure_errors_raise_with_column_names(self) -> None:
        from smartstock.services import import_service

        with pytest.raises(CsvStructureError, match="Missing required"):
            import_service.preview_import(
                _named_stream(
                    "date,store,item\n2013-01-01,1,1\n", name="missing.csv"
                )
            )

    def test_no_rows_in_scope_is_not_an_error(self) -> None:
        from smartstock.services import import_service

        preview = import_service.preview_import(
            _named_stream(
                "date,store,item,sales\n2013-01-01,9,1,13\n",
                name="other.csv",
            )
        )
        assert preview.valid_row_count == 0
        assert preview.importable is False
        assert preview.date_range is None

    def test_preview_readable_again_after_service_call(self) -> None:
        # Uploaded files must survive a preview: persistence re-reads
        # them (TASK-024), so the stream must be seeked back.
        from smartstock.services import import_service

        stream = io.BytesIO(VALID_CSV.encode())
        import_service.preview_import(stream)
        assert stream.read() == VALID_CSV.encode()


class TestImportPage:
    def test_empty_state_without_upload(self) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        assert any(
            "Upload a CSV file" in info.value for info in app_test.info
        )

    def test_valid_file_preview_with_metrics_and_sample(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(_upload())
        app_test.run()

        assert app_test.exception == []
        metric_values = {
            metric.label: metric.value for metric in app_test.metric
        }
        assert metric_values["Rows in file"] == "5"
        assert metric_values["Valid for store 1"] == "3"
        assert metric_values["Rejected (invalid)"] == "1"
        assert metric_values["Other stores"] == "1"
        assert len(app_test.dataframe) == 1  # sample table
        assert any(
            "Date range of accepted rows" in c.value
            for c in app_test.caption
        )
        assert app_test.warning == []  # a clean file has nothing to flag

    def test_rejection_reasons_shown(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(_upload())
        app_test.run()
        labels = [expander.label for expander in app_test.expander]
        assert any("Rejected rows" in label for label in labels)

    def test_structure_error_message(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(
            _upload(
                "date,store,item\n2013-01-01,1,1\n", name="missing.csv"
            )
        )
        app_test.run()
        assert app_test.exception == []
        assert any(
            "Missing required columns" in error.value
            for error in app_test.error
        )
        assert app_test.metric == []  # no preview metrics render

    def test_file_level_error_message(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(
            _upload("", name="empty.csv")
        )
        app_test.run()
        assert app_test.exception == []
        assert any(
            "cannot be imported" in error.value
            for error in app_test.error
        )

    def test_no_rows_in_scope_warning(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(
            _upload(
                "date,store,item,sales\n2013-01-01,9,1,13\n",
                name="other.csv",
            )
        )
        app_test.run()
        assert app_test.exception == []
        assert any(
            "Nothing to import" in w.value for w in app_test.warning
        )
        assert app_test.dataframe == []  # no accepted rows to sample

    def test_fingerprint_caption_shown(self) -> None:
        app_test = _run_page()
        app_test.file_uploader[0].set_value(_upload())
        app_test.run()
        assert any(
            "fingerprint" in c.value for c in app_test.caption
        )
