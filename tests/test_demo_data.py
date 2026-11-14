"""Pin the committed demo dataset against the real import validator.

``data/samples/demo_sales_history.csv`` backs the demo walkthrough
(``docs/08-user-guide/demo-data-walkthrough.md``), whose expected
numbers assume this exact file. Re-validating it in the suite keeps
the walkthrough honest: if the file is edited or regenerated badly,
these tests fail before the guide's figures drift from reality.
"""

from pathlib import Path

import pandas as pd

from smartstock.services import import_service

DEMO_FILE = Path("data/samples/demo_sales_history.csv")


def _preview():
    return import_service.preview_import(DEMO_FILE)


class TestDemoDataset:
    def test_file_is_fully_importable(self) -> None:
        preview = _preview()
        assert preview.importable is True
        assert preview.total_rows == 1621
        assert preview.valid_row_count == 1621
        assert preview.invalid_in_scope_rows == 0
        assert preview.out_of_store_rows == 0
        assert preview.duplicate_row_count == 0
        assert preview.date_range == ("2025-10-10", "2026-11-13")

    def test_item_profile_shares_match_the_walkthrough(self) -> None:
        # The walkthrough's demand figures depend on these history
        # shapes: items 10-13 with 400 days each, item 14 with 21.
        frame = pd.read_csv(DEMO_FILE)
        day_counts = frame.groupby("item")["date"].count().to_dict()
        assert day_counts == {10: 400, 11: 400, 12: 400, 13: 400, 14: 21}

    def test_regeneration_is_deterministic(self, tmp_path: Path) -> None:
        # The generator script must be reproducible: running it twice
        # produces the same bytes (same seed), so the committed file
        # can always be rebuilt exactly.
        import subprocess
        import sys

        committed = DEMO_FILE.read_bytes()
        backup = tmp_path / "committed.csv"
        backup.write_bytes(committed)
        try:
            result = subprocess.run(
                [sys.executable, "scripts/generate_demo_data.py"],
                capture_output=True,
                text=True,
                check=True,
            )
            regenerated = DEMO_FILE.read_bytes()
            assert regenerated == committed, (
                "Regenerated demo data differs from the committed file; "
                f"generator output: {result.stdout}"
            )
        finally:
            backup.write_bytes(committed)
            DEMO_FILE.write_bytes(committed)
