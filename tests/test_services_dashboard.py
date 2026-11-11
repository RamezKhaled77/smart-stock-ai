"""Tests for the dashboard service (TASK-037/038/039, DEC-061).

Hand-computed expectations against a temporary database; the real
``data/smartstock.db`` is never touched.
"""

import datetime as dt
from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import (
    dashboard_service,
    product_service,
    sales_service,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


def _days_ago(days: int) -> str:
    return (dt.date.today() - dt.timedelta(days=days)).isoformat()


@pytest.fixture
def populated(db_path: Path) -> dict:
    """Two products with sales inside/outside the metric windows.

    A 7-day window ending today covers today back to 6 days ago, so:
    Item A: 8 today, 10 five days ago (inside the week), 30 twenty-
    nine days ago (inside the 30-day month window, outside the week).
    Stock 50 covers the 48 sold units, leaving 2 → below the reorder
    point. Item B: 3 six days ago (inside the week). Stock 15, safe.
    """
    a = product_service.create_product(
        name="Item A",
        sku="SKU-A",
        initial_stock=50,
        lead_time_days=5,
        safety_stock=0,
        db_path=db_path,
    )
    b = product_service.create_product(
        name="Item B",
        sku="SKU-B",
        initial_stock=15,
        lead_time_days=5,
        safety_stock=0,
        db_path=db_path,
    )
    sales_service.record_sale(
        a["id"], 8, dt.date.today().isoformat(), db_path=db_path
    )
    sales_service.record_sale(a["id"], 10, _days_ago(5), db_path=db_path)
    sales_service.record_sale(a["id"], 30, _days_ago(29), db_path=db_path)
    sales_service.record_sale(b["id"], 3, _days_ago(6), db_path=db_path)
    return {"a": a, "b": b}


class TestEmptyState:
    def test_all_zero_without_products_or_sales(
        self, db_path: Path
    ) -> None:
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["total_active_products"] == 0
        assert data["total_stock"] == 0
        assert data["products_needing_reorder"] == 0
        assert data["recent_sales"] == {
            "sale_count": 0, "units_sold": 0,
        }
        assert data["top_products"] == []
        assert data["forecast_ready"] == {"linked": 0, "total": 0}
        assert data["trend"] == {}
        assert data["low_stock"] == []

    def test_zero_with_products_but_no_sales(self, db_path: Path) -> None:
        product_service.create_product(
            name="Item A", sku="SKU-A", initial_stock=7, db_path=db_path
        )
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["total_active_products"] == 1
        assert data["total_stock"] == 7
        assert data["products_needing_reorder"] == 0
        assert data["low_stock"] == []  # In Stock, reorder point 0


class TestMetricsWithSales:
    def test_recent_sales_window_is_inclusive(
        self, db_path: Path, populated
    ) -> None:
        # Inside the 7-day window (today back to 6 days ago): 8 (today)
        # + 10 (5 days ago) + 3 (6 days ago) = 21 units in 3 sales; the
        # 29-days-ago sale is outside the week.
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["recent_sales"]["units_sold"] == 21
        assert data["recent_sales"]["sale_count"] == 3

    def test_top_products_ranked_by_units(
        self, db_path: Path, populated
    ) -> None:
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        # 30-day window: A = 8 + 10 + 30 = 48; B = 3.
        assert [
            (row["sku"], row["units_sold"])
            for row in data["top_products"]
        ] == [("SKU-A", 48), ("SKU-B", 3)]

    def test_needs_reorder_counts_breach_only(
        self, db_path: Path, populated
    ) -> None:
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        # Item A: stock 2; the DEC-059 window ends at its last sale
        # (today), history spans 30 days → ADD = 48/30 = 1.6 → reorder
        # ceil(1.6 × 5) = 8 (safety 0); 2 ≤ 8 → breach. Item B: its
        # only sale is the last recorded sale (6 days ago) → 1-day
        # span → ADD 3.0 → reorder 15; stock 15 ≤ 15 → Low Stock too.
        assert data["products_needing_reorder"] == 2

    def test_trend_daily_totals(self, db_path: Path, populated) -> None:
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        trend = data["trend"]
        assert trend[dt.date.today().isoformat()] == 8
        assert trend[_days_ago(5)] == 10
        assert trend[_days_ago(6)] == 3
        assert trend[_days_ago(29)] == 30
        # Days without sales are absent from the trend dict.
        assert _days_ago(4) not in trend

    def test_low_stock_lists_the_breaches(
        self, db_path: Path, populated
    ) -> None:
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert [row["product_sku"] for row in data["low_stock"]] == [
            "SKU-A",
            "SKU-B",
        ]
        assert all(
            row["stock_status"] == "Low Stock"
            for row in data["low_stock"]
        )


class TestWindowFiltering:
    def test_trend_window_changes_with_trend_days(
        self, db_path: Path, populated
    ) -> None:
        short = dashboard_service.get_dashboard_data(
            db_path=db_path, trend_days=7
        )
        # 7-day trend window: the 29-days-ago sale drops out.
        assert _days_ago(29) not in short["trend"]
        assert short["trend"][_days_ago(5)] == 10
        # Top sellers stay on the fixed 30-day window (DEC-061).
        assert [
            (row["sku"], row["units_sold"])
            for row in short["top_products"]
        ] == [("SKU-A", 48), ("SKU-B", 3)]


class TestForecastReadiness:
    def test_linked_products_counted(self, db_path: Path) -> None:
        product_service.create_product(
            name="Linked", sku="SKU-L", dataset_item_id=2,
            db_path=db_path,
        )
        product_service.create_product(
            name="Unlinked", sku="SKU-U", db_path=db_path
        )
        data = dashboard_service.get_dashboard_data(db_path=db_path)
        assert data["forecast_ready"] == {"linked": 1, "total": 2}


class TestValidation:
    def test_invalid_trend_days_rejected(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            dashboard_service.get_dashboard_data(
                db_path=db_path, trend_days=0
            )
