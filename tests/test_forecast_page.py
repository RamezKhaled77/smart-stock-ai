"""Tests for the Demand Forecast page (DEC-060).

Streamlit AppTest runs the real page against a temporary database
injected by patching ``config.DATABASE_PATH`` (services resolve the
path at call time). The real ``data/smartstock.db`` is never touched.
"""

from pathlib import Path

import pytest

from smartstock.database.connection import session
from smartstock.database.initialization import initialize_database
from smartstock.repositories import historical_repository
from smartstock.services import product_service


@pytest.fixture
def app_db(tmp_path: Path, monkeypatch) -> Path:
    import config

    db_path = tmp_path / "app_test.db"
    initialize_database(db_path)
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    return db_path


def _run_page() -> object:
    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_string(
        "from smartstock.pages.forecast import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _import_for_linked(db_path: Path, item: int, days: int) -> None:
    import datetime as dt

    totals = {
        (dt.date(2024, 1, 1) + dt.timedelta(offset)).isoformat(): 3
        for offset in range(days)
    }
    rows = [(item, date, qty) for date, qty in totals.items()]
    meta = {
        "source_filename": "page-test.csv",
        "file_sha256": f"page-sha-{item}-{days}",
        "store": 1,
        "total_rows": len(rows),
        "out_of_store_rows": 0,
        "rejected_rows": 0,
        "duplicate_rows": 0,
        "first_date": min(totals),
        "last_date": max(totals),
    }
    with session(db_path) as connection:
        historical_repository.create_import_batch(connection, meta, rows)


def _select(app_test, key: str, value: str) -> None:
    matches = [s for s in app_test.selectbox if s.key == key]
    assert matches, f"selectbox {key!r} not found"
    matches[0].set_value(value).run()
    app_test.run()


class TestForecastPage:
    def test_empty_state_without_products(self, app_db) -> None:
        app_test = _run_page()
        assert not app_test.exception
        texts = [info.value for info in app_test.info]
        assert any("No active products" in text for text in texts)

    def test_unlinked_product_shows_link_guidance(self, app_db) -> None:
        product_service.create_product(name="Item A", sku="SKU-A")
        app_test = _run_page()
        assert not app_test.exception
        texts = [info.value for info in app_test.info]
        assert any(
            "no dataset item linked" in text for text in texts
        )

    def test_linked_product_generates_fallback_forecast(
        self, app_db
    ) -> None:
        product = product_service.create_product(
            name="Item A", sku="SKU-A", dataset_item_id=7
        )
        # 10 observed days < 31 → DEC-058 fallback path, no artifact
        # loading needed for the MA-7 maths (the real artifact exists
        # in this checkout but is not consumed on this path).
        _import_for_linked(app_db, 7, 10)
        app_test = _run_page()
        label = f"{product['name']} ({product['sku']})"
        _select(app_test, "forecast_product", label)
        generate = [b for b in app_test.button if b.label == "Generate forecast"]
        assert generate, "generate button missing"
        app_test = generate[0].click().run()
        assert not app_test.exception
        captions = [c.value for c in app_test.caption]
        assert any(
            "Trailing 7-day average fallback" in text
            for text in captions
        )
        metrics = {m.label: m.value for m in app_test.metric}
        # Constant daily sales of 3 → all predictions 3.0 (3 × 7 days).
        assert metrics["Total demand (7 days)"] == "21.0"
        assert metrics["Average per day"] == "3.0"
        assert metrics["Dataset item"] == "7"

    def test_generate_without_history_shows_history_notice(
        self, app_db
    ) -> None:
        product_service.create_product(
            name="Item B", sku="SKU-B", dataset_item_id=9
        )
        app_test = _run_page()
        _select(app_test, "forecast_product", "Item B (SKU-B)")
        generate = [b for b in app_test.button if b.label == "Generate forecast"]
        app_test = generate[0].click().run()
        assert not app_test.exception
        texts = [i.value for i in app_test.info]
        assert any("No suitable history exists" in text for text in texts)
