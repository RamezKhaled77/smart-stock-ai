"""End-to-end integration tests (TASK-044).

Two levels:

1. Real ``app.py`` startup — proves every page module imports and the
   navigation registers all pages (core workflows are reachable).
2. One business workflow walked through the service layers on a single
   temporary database: product → sales → inventory → analytics →
   performance → restocking → CSV import → forecast. No UI driving and
   no SQL — the tests prove the layers connect.
"""

import datetime as dt
from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.domain.inventory import classify_stock
from smartstock.services import (
    analytics_service,
    dashboard_service,
    forecast_service,
    inventory_service,
    product_service,
    restock_service,
    sales_service,
)
from smartstock.services import evaluation_service


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "integration.db"
    initialize_database(path)
    return path


def _days_ago(days: int) -> str:
    return (dt.date.today() - dt.timedelta(days=days)).isoformat()


class TestAppStartup:
    def test_app_starts_and_registers_all_pages(self) -> None:
        from streamlit.testing.v1 import AppTest

        repo_root = Path(__file__).resolve().parents[2]
        app_test = AppTest.from_file(
            str(repo_root / "app.py"), default_timeout=60
        )
        app_test.run()
        # Startup imports all seven page modules (app.py imports every
        # render function at module level) and registers the full
        # st.navigation structure — a broken page module fails here.
        assert not app_test.exception
        # AppTest 1.66 does not expose the st.navigation switcher as
        # sidebar widgets, so assert the default page actually ran.
        titles = [t.value for t in app_test.main.title]
        assert any("Dashboard" in text for text in titles)


class TestBusinessWorkflow:
    def test_product_to_forecast_end_to_end(self, db_path: Path) -> None:
        # 1. Product created with opening stock.
        product = product_service.create_product(
            name="Widget",
            sku="SKU-W",
            category="Tools",
            initial_stock=50,
            lead_time_days=3,
            safety_stock=2,
            dataset_item_id=11,
            db_path=db_path,
        )
        assert product["current_stock"] == 50

        # 2. Sales recorded → stock decremented atomically.
        sales_service.record_sale(
            product["id"], 2, _days_ago(5), db_path=db_path
        )
        sales_service.record_sale(
            product["id"], 3, _days_ago(0), db_path=db_path
        )
        overview = inventory_service.get_stock_overview(db_path=db_path)
        assert overview[0]["current_stock"] == 45

        # 3. Dashboard metrics see the same data (7-day window).
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["total_active_products"] == 1
        assert data["total_stock"] == 45
        assert data["recent_sales"] == {
            "sale_count": 2, "units_sold": 5,
        }
        # Stock 45 vs. reorder ceil(5/6 × 3) + 2 = 5 → In Stock.
        assert data["products_needing_reorder"] == 0

        # 4. Analytics aggregates the same sales (range = last 30 d).
        today = _days_ago(0)
        month_ago = _days_ago(29)
        analytics = analytics_service.get_sales_analytics(
            month_ago, today, db_path=db_path
        )
        assert analytics["totals"]["units_sold"] == 5
        assert analytics["totals"]["sale_count"] == 2
        # Both sales in the second calendar half → rising (new) demand.
        assert analytics["per_product"][0]["share_of_units"] == 1.0

        # 5. Performance analysis reads the same source.
        performance = analytics_service.get_product_performance(
            month_ago, today, db_path=db_path
        )
        assert performance[0]["trend"] == "Rising (new)"
        assert performance[0]["first_sale"] == _days_ago(5)
        assert performance[0]["last_sale"] == today

        # 6. Restocking advice derived from the same history.
        recommendations = restock_service.get_restock_recommendations(
            db_path=db_path
        )
        assert len(recommendations) == 1
        row = recommendations[0]
        assert row["available"] is True
        assert row["needs_reorder"] is False
        assert row["stock_status"] == classify_stock(
            45, row["reorder_point"]
        )

        # 7. Imported dataset history drives the forecast (DEC-060).
        _import_history(db_path, item=11, days=10, daily_units=4)
        result = forecast_service.get_forecast(
            product["id"], 7, db_path=db_path
        )
        assert result["model_used"] == "moving_average_7"  # < 31 days
        assert result["rows"][0]["predicted_demand"] == 4.0
        total = sum(r["predicted_demand"] for r in result["rows"])
        assert total == 28.0

        # 8. Evaluation display reports the stored training metrics.
        summary = evaluation_service.get_evaluation_summary(
            artifacts_dir=evaluation_service.ARTIFACTS_DIR
        )
        assert summary["model_name"] == "random_forest"

    def test_reorder_flow_end_to_end(self, db_path: Path) -> None:
        # A product selling heavily against small stock breaches BR-022
        # and shows up in both the restock service and the dashboard.
        product = product_service.create_product(
            name="Mover",
            sku="SKU-M",
            initial_stock=10,
            lead_time_days=3,
            safety_stock=0,
            db_path=db_path,
        )
        sales_service.record_sale(
            product["id"], 8, _days_ago(0), db_path=db_path
        )
        recommendations = restock_service.get_restock_recommendations(
            db_path=db_path
        )
        row = recommendations[0]
        # Span-1 demand 8.0 → reorder point ceil(8 × 3) = 24 (breach,
        # 2 ≤ 24) and DEC-038 target stock = ceil(8) × (3 + 7) + 0 =
        # 80 → ROQ = 80 − 2 = 78.
        assert row["needs_reorder"] is True
        assert row["recommended_order_quantity"] == 78
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["products_needing_reorder"] == 1
        assert data["low_stock"][0]["product_sku"] == "SKU-M"


def _import_history(
    db_path: Path, item: int, days: int, daily_units: int
) -> None:
    """Store one imported batch: ``days`` days of constant quantity."""
    from smartstock.database.connection import session
    from smartstock.repositories import historical_repository

    start = dt.date(2024, 1, 1)
    totals = {
        (start + dt.timedelta(offset)).isoformat(): daily_units
        for offset in range(days)
    }
    rows = [(item, date, qty) for date, qty in totals.items()]
    meta = {
        "source_filename": "integration.csv",
        "file_sha256": f"integration-sha-{item}",
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
