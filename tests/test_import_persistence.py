"""Tests for historical import persistence (TASK-024).

Repository-level transaction and duplicate handling, service-level
execution, and page-level confirm flows with Streamlit AppTest. Tests
never touch the real ``data/smartstock.db``.
"""

import io
import sqlite3
from pathlib import Path

import pytest

from smartstock.database.connection import DatabaseError
from smartstock.database.initialization import (
    initialize_database,
    verify_tables,
)
from smartstock.repositories import historical_repository
from smartstock.services import import_service

VALID_CSV = """date,store,item,sales
2013-01-01,1,1,13
2013-01-02,1,1,11
2013-01-03,1,2,9
2013-01-03,2,1,7
"""


def _named_stream(content: str, name: str = "train.csv") -> io.BytesIO:
    stream = io.BytesIO(content.encode("utf-8"))
    stream.name = name
    return stream


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "import_test.db"
    initialize_database(path)
    return path


class TestHistoricalRepository:
    def _meta(self) -> dict:
        return {
            "source_filename": "train.csv",
            "file_sha256": "a" * 64,
            "store": 1,
            "total_rows": 4,
            "out_of_store_rows": 1,
            "rejected_rows": 1,
            "duplicate_rows": 0,
            "first_date": "2013-01-01",
            "last_date": "2013-01-03",
        }

    def _rows(self) -> list:
        return [(1, "2013-01-01", 13), (1, "2013-01-02", 11),
                (2, "2013-01-03", 9)]

    def test_batch_and_rows_stored(self, db_path: Path) -> None:
        from smartstock.database.connection import session

        with session(db_path) as connection:
            batch = historical_repository.create_import_batch(
                connection, self._meta(), self._rows()
            )
        assert batch["id"] == 1
        # Out-of-store and rejected rows were already excluded by the
        # validation pipeline; the batch records their counts.
        assert batch["imported_rows"] == 3
        assert batch["duplicate_rows"] == 0
        assert batch["created_at"]
        assert batch["first_date"] == "2013-01-01"

        with session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 3
            batches = historical_repository.get_import_batches(connection)
        assert len(batches) == 1

    def test_duplicate_fingerprint_rejected(self, db_path: Path) -> None:
        from smartstock.database.connection import session

        with session(db_path) as connection:
            historical_repository.create_import_batch(
                connection, self._meta(), self._rows()
            )
        meta = self._meta()
        meta["source_filename"] = "renamed.csv"  # name alone does not matter (DEC-053)
        with session(db_path) as connection:
            with pytest.raises(
                historical_repository.DuplicateImportError
            ) as excinfo:
                historical_repository.create_import_batch(
                    connection, meta, self._rows()
                )
        error = excinfo.value
        assert error.original_filename == "train.csv"
        assert error.original_batch_id == 1
        with session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 3
            assert len(historical_repository.get_import_batches(connection)) == 1

    def test_overlapping_file_skips_existing_rows(
        self, db_path: Path
    ) -> None:
        from smartstock.database.connection import session

        with session(db_path) as connection:
            historical_repository.create_import_batch(
                connection, self._meta(), self._rows()
            )
            # A different file containing one existing key and one new key.
            second_meta = self._meta()
            second_meta["file_sha256"] = "b" * 64
            second_meta["total_rows"] = 2
            second_meta["first_date"] = "2013-01-03"
            second = historical_repository.create_import_batch(
                connection,
                second_meta,
                [
                    (1, "2013-01-01", 13),  # already stored by batch 1
                    (5, "2013-01-05", 21),  # new
                ],
            )
        assert second["imported_rows"] == 1
        assert second["duplicate_rows"] == 1  # the skipped existing row
        with session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 4

    def test_failed_insert_rolls_everything_back(self, db_path: Path) -> None:
        from smartstock.database.connection import session

        # EXECUTEmany with a CHECK-violating row (negative quantity is
        # impossible via the service pipeline) must leave nothing behind.
        with pytest.raises(DatabaseError):
            with session(db_path) as connection:
                rows = [(1, "2013-01-01", 13), (1, "2013-01-02", -5)]
                historical_repository.create_import_batch(
                    connection, self._meta(), rows
                )
        with session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 0
            assert (
                len(historical_repository.get_import_batches(connection)) == 0
            )


class TestExecuteImportService:
    def test_valid_file_persists_with_result(self, db_path: Path) -> None:
        result = import_service.execute_import(
            _named_stream(VALID_CSV), db_path=db_path
        )
        assert result.imported_rows == 3
        assert result.total_rows == 4
        assert result.out_of_store_rows == 1
        assert result.rejected_rows == 0
        assert result.date_range == ("2013-01-01", "2013-01-03")
        assert result.filename == "train.csv"
        assert result.store == 1
        assert result.created_at

        with import_service.session(db_path) as connection:
            assert (
                historical_repository.count_historical_rows(connection) == 3
            )

    def test_no_importable_rows_rejected(self, db_path: Path) -> None:
        only_other_store = (
            "date,store,item,sales\n2013-01-01,9,1,13\n"
        )
        with pytest.raises(
            import_service.ImportRejectedError, match="Nothing to import"
        ):
            import_service.execute_import(
                _named_stream(only_other_store, name="other.csv"),
                db_path=db_path,
            )
        with import_service.session(db_path) as connection:
            assert (
                historical_repository.count_historical_rows(connection) == 0
            )

    def test_identical_re_upload_rejected_without_changes(
        self, db_path: Path
    ) -> None:
        import_service.execute_import(
            _named_stream(VALID_CSV), db_path=db_path
        )
        # Same bytes under a different name must still be rejected
        # (DEC-053 fingerprint, not filename).
        with pytest.raises(import_service.DuplicateImportError):
            import_service.execute_import(
                _named_stream(VALID_CSV, name="renamed.csv"),
                db_path=db_path,
            )
        with import_service.session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 3
            assert (
                len(historical_repository.get_import_batches(connection)) == 1
            )

    def test_overlapping_but_different_files_merge(self, db_path: Path) -> None:
        import_service.execute_import(
            _named_stream(VALID_CSV), db_path=db_path
        )
        second = VALID_CSV.replace(
            "2013-01-03,1,2,9", "2013-01-04,1,2,5"
        )
        result = import_service.execute_import(
            _named_stream(second, name="second.csv"), db_path=db_path
        )
        assert result.imported_rows == 1  # the new store-1 row
        assert result.duplicate_rows == 2  # two overlapping (item, date) rows
        with import_service.session(db_path) as connection:
            assert historical_repository.count_historical_rows(connection) == 4

    def test_existing_pre_import_database_gets_import_tables(
        self, tmp_path: Path
    ) -> None:
        # A database created before DEC-052 only has products + sales;
        # execute_import must safely create the missing import tables.
        legacy = tmp_path / "legacy.db"
        legacy.touch()
        connection = sqlite3.connect(legacy)
        connection.executescript(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT '',
                current_stock INTEGER NOT NULL DEFAULT 0
                    CHECK (current_stock >= 0),
                lead_time_days INTEGER NOT NULL DEFAULT 3
                    CHECK (lead_time_days >= 0),
                safety_stock INTEGER NOT NULL DEFAULT 0
                    CHECK (safety_stock >= 0),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                sale_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.commit()
        connection.close()

        result = import_service.execute_import(
            _named_stream(VALID_CSV), db_path=legacy
        )
        assert result.imported_rows == 3
        columns = verify_tables(legacy)
        assert "import_batches" in columns
        assert "historical_sales" in columns


class TestImportPagePersistence:
    @pytest.fixture
    def app_db(self, tmp_path: Path, monkeypatch) -> Path:
        import config
        import smartstock.services.import_service as service_module

        db_path = tmp_path / "app_import_test.db"
        initialize_database(db_path)
        # The service resolves the database at call time from config
        # (page passes no db_path); patch both so the page and the
        # assertions agree.
        monkeypatch.setattr(config, "DATABASE_PATH", db_path)
        yield db_path

    def test_confirm_button_imports_rows(self, app_db: Path) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.imports import render\nrender()",
            default_timeout=60,
        )
        app_test.run()
        app_test.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        app_test.run()
        buttons = [button for button in app_test.button if "Import " in button.label]
        assert len(buttons) == 1
        assert buttons[0].label == "Import 3 record(s)"

        buttons[0].click()
        app_test.run()
        assert app_test.exception == []
        assert any(
            "Imported 3 historical record(s)" in success.value
            for success in app_test.success
        )
        with import_service.session(app_db) as connection:
            assert (
                historical_repository.count_historical_rows(connection) == 3
            )

    def test_fresh_session_reimporting_same_file_rejected(
        self, app_db: Path
    ) -> None:
        # Same-session re-imports are blocked by the result panel
        # (TASK-025); the DEC-053 UI-level rejection matters for a
        # fresh session uploading the identical bytes.
        from streamlit.testing.v1 import AppTest

        first = AppTest.from_string(
            "from smartstock.pages.imports import render\nrender()",
            default_timeout=60,
        )
        first.run()
        first.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        first.run()
        first.button[0].click()  # first import succeeds
        first.run()

        fresh = AppTest.from_string(
            "from smartstock.pages.imports import render\nrender()",
            default_timeout=60,
        )
        fresh.run()
        fresh.file_uploader[0].set_value(
            ("renamed.csv", VALID_CSV.encode(), "text/csv")
        )
        fresh.run()
        fresh.button[0].click()
        fresh.run()
        assert fresh.exception == []
        assert any(
            "already imported" in error.value for error in fresh.error
        )
        with import_service.session(app_db) as connection:
            assert (
                len(historical_repository.get_import_batches(connection)) == 1
            )

    def test_no_confirm_button_when_nothing_importable(
        self, app_db: Path
    ) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.imports import render\nrender()",
            default_timeout=60,
        )
        app_test.run()
        app_test.file_uploader[0].set_value(
            (
                "other.csv",
                b"date,store,item,sales\n2013-01-01,9,1,13\n",
                "text/csv",
            )
        )
        app_test.run()
        assert any(
            "Nothing to import" in warning.value
            for warning in app_test.warning
        )
        assert app_test.button == []


class TestImportSummaryDisplay:
    """TASK-025: post-import result and import history (spec §14)."""

    @pytest.fixture
    def app_db(self, tmp_path: Path, monkeypatch) -> Path:
        import config

        db_path = tmp_path / "app_summary_test.db"
        initialize_database(db_path)
        monkeypatch.setattr(config, "DATABASE_PATH", db_path)
        return db_path

    def _run(self) -> "AppTest":
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.imports import render\nrender()",
            default_timeout=60,
        )
        app_test.run()
        return app_test

    def test_result_panel_replaces_button_after_import(
        self, app_db: Path
    ) -> None:
        app_test = self._run()
        app_test.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        app_test.run()
        app_test.button[0].click()
        app_test.run()

        assert app_test.exception == []
        # Success banner + spec §14 metrics replace the confirm step.
        assert any(
            "Import completed — batch #1" in success.value
            for success in app_test.success
        )
        metric_values = {
            metric.label: metric.value for metric in app_test.metric
        }
        assert metric_values["Accepted and stored"] == "3"
        assert metric_values["Rejected (invalid)"] == "0"
        assert metric_values["Duplicates skipped"] == "0"
        assert metric_values["Other stores"] == "1"
        assert not [
            button for button in app_test.button if "Import " in button.label
        ], "an identical file must not offer a second import run"

    def test_result_panel_notes_timestamp_and_range(
        self, app_db: Path
    ) -> None:
        app_test = self._run()
        app_test.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        app_test.run()
        app_test.button[0].click()
        app_test.run()
        captions = [c.value for c in app_test.caption]
        assert any(
            "Historical dataset import, store 1" in value
            and "2013-01-01 → 2013-01-03" in value
            for value in captions
        )
        # The §14 timestamp is part of the success banner.
        assert any(
            "batch #1 (" in success.value for success in app_test.success
        )

    def test_import_history_lists_batches_and_totals(
        self, app_db: Path
    ) -> None:
        app_test = self._run()
        app_test.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        app_test.run()
        app_test.button[0].click()
        app_test.run()

        labels = [expander.label for expander in app_test.expander]
        assert any("Previous imports" in label for label in labels)

        # Newest-first batch table with accurate counts.
        batch_frames = [
            frame for frame in app_test.dataframe if "Batch" in frame.value.columns
        ]
        assert len(batch_frames) == 1
        records = batch_frames[0].value.to_dict(orient="records")
        assert records[0]["File"] == "train.csv"
        assert records[0]["Imported"] == 3
        assert records[0]["Batch"] == 1

        # The stored-records caption.
        assert any(
            "historical record(s) stored in total" in c.value
            for c in app_test.caption
        )

    def test_new_file_reopens_confirm_step(self, app_db: Path) -> None:
        app_test = self._run()
        app_test.file_uploader[0].set_value(
            ("train.csv", VALID_CSV.encode(), "text/csv")
        )
        app_test.run()
        app_test.button[0].click()
        app_test.run()
        assert not [
            b for b in app_test.button if "Import " in b.label
        ]

        # A different file (different fingerprint) restarts the flow.
        app_test.file_uploader[0].set_value(
            (
                "more.csv",
                (
                    "date,store,item,sales\n"
                    "2013-02-01,1,1,20\n"
                    "2013-02-02,1,1,22\n"
                ).encode(),
                "text/csv",
            )
        )
        app_test.run()
        assert app_test.exception == []
        buttons = [
            button for button in app_test.button if "Import " in button.label
        ]
        assert len(buttons) == 1
        assert buttons[0].label == "Import 2 record(s)"

    def test_history_before_any_import(self, app_db: Path) -> None:
        app_test = self._run()
        assert any(
            "No imports recorded yet" in info.value
            for info in app_test.info
        )

    def test_service_summary_counts(self, app_db: Path) -> None:
        import_service.execute_import(
            _named_stream(VALID_CSV), db_path=app_db
        )
        summary = import_service.get_import_summary(db_path=app_db)
        assert summary["total_records"] == 3
        assert len(summary["batches"]) == 1
        assert summary["batches"][0]["imported_rows"] == 3
