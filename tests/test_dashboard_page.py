"""Tests for the Dashboard page (TASK-037/038/039).

Streamlit AppTest runs the real page against a temporary database
injected by patching ``config.DATABASE_PATH``; the real
``data/smartstock.db`` is never touched.
"""

import datetime as dt
from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import product_service, sales_service

# Streamlit 1.66's own chart internals trip a pandas-4 deprecation
# (upstream issue, not project code); the suite stays warning-free.
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
        "from smartstock.pages.dashboard import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _metric(app_test, label: str) -> str:
    matches = [m for m in app_test.metric if m.label == label]
    assert matches, f"metric {label!r} not found"
    return matches[0].value


def _days_ago(days: int) -> str:
    return (dt.date.today() - dt.timedelta(days=days)).isoformat()


class TestDashboardPage:
    def test_empty_state_shows_zero_metrics_and_guidance(
        self, app_db
    ) -> None:
        app_test = _run_page()
        assert not app_test.exception
        assert _metric(app_test, "Active products") == "0"
        assert _metric(app_test, "Total stock") == "0"
        assert any(
            "No active products" in info.value
            for info in app_test.info
        )

    def test_metrics_use_real_application_data(self, app_db) -> None:
        a = product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=20
        )
        product_service.create_product(
            name="Item B", sku="SKU-B", initial_stock=5
        )
        sales_service.record_sale(
            a["id"], 14, dt.date.today().isoformat()
        )
        app_test = _run_page()
        assert not app_test.exception
        assert _metric(app_test, "Active products") == "2"
        assert _metric(app_test, "Total stock") == "11"  # 20 − 14 + 5
        assert _metric(app_test, "Units sold (last 7 days)") == "14"
        assert _metric(
            app_test, "Sales recorded (last 7 days)"
        ) == "1"
        assert _metric(app_test, "Top seller (30 days)") == "14"
        # Needs-reorder metric: a 1-day-span demand of 14 → reorder 42
        # (lead 3 default, safety 0); Item A stock 6 ≤ 42 → breach.
        # Item B has no sales → reorder 0 → In Stock.
        assert _metric(app_test, "Products needing reorder") == "1"

    def test_trend_chart_and_window(
        self, app_db
    ) -> None:
        a = product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=50
        )
        sales_service.record_sale(a["id"], 4, _days_ago(2))
        sales_service.record_sale(a["id"], 6, _days_ago(1))
        app_test = _run_page()
        assert not app_test.exception
        # Line chart present (rendered as a vega-lite chart element).
        charts = [
            element for element in app_test.main
            if getattr(element, "type", "") == "vega_lite_chart"
        ]
        assert charts, "sales trend chart missing"
        radios = [r for r in app_test.radio if r.key == "dashboard_trend_window"]
        assert radios, "trend window selector missing"
        app_test = radios[0].set_value(30).run()
        assert not app_test.exception

    def test_low_stock_overview_matches_business_rules(
        self, app_db
    ) -> None:
        a = product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=50
        )
        sales_service.record_sale(a["id"], 48, dt.date.today().isoformat())
        product_service.create_product(
            name="Calm", sku="SKU-CALM", initial_stock=30
        )
        app_test = _run_page()
        assert not app_test.exception
        # Item A: stock 2 vs. span-1 demand 48 → reorder 144 → Low
        # Stock; Calm: no sales → reorder point 0 → In Stock.
        frames = app_test.dataframe
        low_table = frames[-1].value
        assert "SKU-A" in low_table["SKU"].tolist()
        assert "SKU-CALM" not in low_table["SKU"].tolist()
        warnings = [w.value for w in app_test.warning]
        assert any("Low Stock" in text for text in warnings)

    def test_forecast_readiness_line(self, app_db) -> None:
        product_service.create_product(
            name="Linked", sku="SKU-L", dataset_item_id=3
        )
        product_service.create_product(name="Not", sku="SKU-N")
        app_test = _run_page()
        captions = [c.value for c in app_test.caption]
        assert any("1 of 2" in text for text in captions)
