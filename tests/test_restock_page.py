"""Tests for the Restocking Recommendations page (TASK-036).

Streamlit AppTest runs the real page against a temporary database
injected by patching ``config.DATABASE_PATH``; the real
``data/smartstock.db`` is never touched.
"""

from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import product_service, sales_service
from smartstock.utils.dates import utc_today_iso


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
        "from smartstock.pages.restock import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _info_texts(app_test) -> list:
    return [info.value for info in app_test.info]


def _metric(app_test, label: str):
    matches = [m for m in app_test.metric if m.label == label]
    assert matches, f"metric {label!r} not found"
    return matches[0]


class TestRestockPage:
    def test_empty_state_without_products(self, app_db) -> None:
        app_test = _run_page()
        assert not app_test.exception
        texts = _info_texts(app_test)
        assert any("No active products" in text for text in texts)

    def test_needs_attention_table_and_metrics(self, app_db) -> None:
        stocked = product_service.create_product(
            name="Item A",
            sku="SKU-A",
            initial_stock=20,
            lead_time_days=5,
            safety_stock=2,
        )
        sales_service.record_sale(stocked["id"], 8, utc_today_iso())
        app_test = _run_page()
        assert not app_test.exception
        # Sale of 8 today → span 1 → ADD 8.0; reorder 42; stock 2.
        assert _metric(
            app_test, "Products needing reorder"
        ).value == "1"
        assert (
            _metric(app_test, "Recommendations available").value == "1"
        )
        assert _metric(app_test, "Without enough data").value == "0"
        assert any(
            "restock" in subheader.value.lower()
            for subheader in app_test.subheader
        )
        frames = app_test.dataframe
        assert frames, "recommendation table missing"
        table = frames[0].value
        row = table[table["SKU"] == "SKU-A"].iloc[0]
        assert row["Stock"] == 12  # 20 − 8 sold
        assert row["Avg daily demand"] == pytest.approx(8.0)
        assert row["Reorder point"] == 42
        # target = ceil(8) × (5 + 7) + 2 = 98; order = 98 − 12 = 86.
        assert row["Target stock"] == 98
        assert row["Order"] == 86
        assert row["Lead time (days)"] == 5
        assert row["Safety stock"] == 2
        # TASK-049/DEC-063: CSV export of the recommendations.
        downloads = [
            d for d in app_test.download_button
            if "recommendations" in d.label
        ]
        assert downloads, "recommendations export button missing"

    def test_no_reorder_needed_success_state(self, app_db) -> None:
        stocked = product_service.create_product(
            name="Calm Item",
            sku="SKU-CALM",
            initial_stock=50,
            lead_time_days=5,
            safety_stock=2,
        )
        sales_service.record_sale(stocked["id"], 1, utc_today_iso())
        app_test = _run_page()
        assert not app_test.exception
        # ADD 1.0 → target 14 < 50 → nothing needs reordering.
        assert _metric(
            app_test, "Products needing reorder"
        ).value == "0"
        assert any(
            "No product is at or below its reorder point" in success.value
            for success in app_test.success
        )

    def test_unavailable_product_shows_reason(self, app_db) -> None:
        product_service.create_product(name="No Sales", sku="SKU-NONE")
        app_test = _run_page()
        assert not app_test.exception
        assert _metric(
            app_test, "Recommendations available"
        ).value == "0"
        assert _metric(app_test, "Without enough data").value == "1"
        texts = _info_texts(app_test)
        assert any(
            "SKU-NONE" in text and "No sales are recorded" in text
            for text in texts
        )

    def test_no_automatic_purchasing_side_effects(self, app_db) -> None:
        stocked = product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=10
        )
        sales_service.record_sale(stocked["id"], 3, utc_today_iso())
        app_test = _run_page()
        assert not app_test.exception
        # Rendering is read-only: stock unchanged, no order happened —
        # the only service mutation-free by design (DEC-031/BR-012).
        refreshed = product_service.get_product(stocked["id"])
        assert refreshed["current_stock"] == 7
        assert _metric(
            app_test, "Products needing reorder"
        ).value == "1"


class TestAppNavigation:
    def test_app_starts_with_restock_page_registered(self, app_db) -> None:
        from streamlit.testing.v1 import AppTest

        repo_root = Path(__file__).resolve().parents[1]
        app_test = AppTest.from_file(
            str(repo_root / "app.py"), default_timeout=60
        )
        app_test.run()
        # Startup proves the navigation registers every page module.
        assert not app_test.exception
