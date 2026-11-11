"""Tests for the Sales Analytics page (TASK-041).

Streamlit AppTest runs the real page against a temporary database
injected by patching ``config.DATABASE_PATH``; the real
``data/smartstock.db`` is never touched.
"""

from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import product_service, sales_service

pytestmark = pytest.mark.filterwarnings(
    "ignore:The inplace keyword:Warning"
)


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
        "from smartstock.pages.analytics import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _set_range(app_test, start: str, end: str) -> None:
    """Set the analytics date range, then rerun."""
    import datetime as dt

    date_inputs = {di.key: di for di in app_test.date_input}
    date_inputs["analytics_start"].set_value(
        dt.date.fromisoformat(start)
    ).run()
    app_test = date_inputs["analytics_end"].set_value(
        dt.date.fromisoformat(end)
    ).run()
    return app_test


class TestAnalyticsPage:
    def test_renders_with_empty_database(self, app_db) -> None:
        app_test = _run_page()
        assert not app_test.exception
        assert any(
            "No active products" in info.value for info in app_test.info
        )

    def test_database_failure_shows_friendly_error(
        self, app_db, monkeypatch
    ) -> None:
        # TASK-045: a read failure degrades to a message, not a crash.
        from smartstock.database.connection import DatabaseError
        from smartstock.services import product_service

        def broken(db_path=None, **kwargs):
            raise DatabaseError("disk unavailable")

        monkeypatch.setattr(product_service, "list_products", broken)
        app_test = _run_page()
        assert not app_test.exception
        assert any(
            "Could not load products" in e.value for e in app_test.error
        )

    def test_supported_analytics_displayed(
        self, app_db
    ) -> None:
        a = product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=40
        )
        b = product_service.create_product(
            name="Item B", sku="SKU-B", initial_stock=10
        )
        sales_service.record_sale(a["id"], 10, "2026-01-05")
        sales_service.record_sale(a["id"], 20, "2026-01-06")
        sales_service.record_sale(a["id"], 5, "2026-02-01")
        sales_service.record_sale(b["id"], 3, "2026-01-06")
        app_test = _run_page()
        app_test = _set_range(app_test, "2026-01-01", "2026-02-28")
        assert not app_test.exception
        metrics = {m.label: m.value for m in app_test.metric}
        assert metrics["Units sold"] == "38"
        assert metrics["Sales recorded"] == "4"
        # Trend and pattern charts present (vega elements).
        charts = [
            element for element in app_test.main
            if getattr(element, "type", "") == "vega_lite_chart"
        ]
        assert len(charts) >= 2  # daily trend + weekday pattern
        # Per-product ranking table with the right totals.
        tables = app_test.dataframe
        ranking = tables[0].value
        assert ranking["SKU"].tolist() == ["SKU-A", "SKU-B"]
        assert ranking["Units sold"].tolist() == [35, 3]
        # Performance table (TASK-043) with trend directions.
        performance = tables[1].value
        assert performance["SKU"].tolist() == ["SKU-A", "SKU-B"]
        assert performance["Trend"].tolist() == [
            "Falling", "Falling (stopped)",
        ]
        # Item A: first sale Jan 5, last sale Feb 1.
        a_row = performance[performance["SKU"] == "SKU-A"].iloc[0]
        assert a_row["First sale"] == "2026-01-05"
        assert a_row["Last sale"] == "2026-02-01"
        # Monthly totals table present with split months.
        monthly = tables[2].value
        assert monthly["Month"].tolist() == ["2026-01", "2026-02"]
        assert monthly["Units sold"].tolist() == [33, 5]
