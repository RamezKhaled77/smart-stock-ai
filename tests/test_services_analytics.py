"""Tests for the sales analytics service (TASK-041).

Hand-computed expectations against a temporary database; the real
``data/smartstock.db`` is never touched.
"""

from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import (
    analytics_service,
    product_service,
    sales_service,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


@pytest.fixture
def two_products_with_sales(db_path: Path) -> dict:
    a = product_service.create_product(
        name="Item A", sku="SKU-A", initial_stock=40, db_path=db_path
    )
    b = product_service.create_product(
        name="Item B", sku="SKU-B", initial_stock=10, db_path=db_path
    )
    sales_service.record_sale(a["id"], 10, "2026-01-05", db_path=db_path)
    sales_service.record_sale(a["id"], 20, "2026-01-06", db_path=db_path)
    sales_service.record_sale(a["id"], 5, "2026-02-01", db_path=db_path)
    sales_service.record_sale(b["id"], 3, "2026-01-06", db_path=db_path)
    return {"a": a, "b": b}


class TestRangeTotals:
    def test_totals_match_source_data(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        totals = data["totals"]
        assert totals["units_sold"] == 38  # 10 + 20 + 5 + 3
        assert totals["sale_count"] == 4
        assert totals["days_in_range"] == 59
        assert totals["days_with_sales"] == 3
        assert totals["avg_units_per_day"] == pytest.approx(
            round(38 / 59, 3)
        )

    def test_daily_series(self, db_path: Path, two_products_with_sales) -> None:
        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        assert data["daily"] == {
            "2026-01-05": 10,
            "2026-01-06": 23,  # A 20 + B 3
            "2026-02-01": 5,
        }

    def test_monthly_totals_split_across_months(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        assert data["monthly"] == {"2026-01": 33, "2026-02": 5}


class TestWeekdayPattern:
    def test_zero_sale_days_included_in_averages(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        import datetime as dt

        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-08", db_path=db_path
        )
        # Mirror the service computation from the daily source data.
        daily = data["daily"]
        sums = [0] * 7
        counts = [0] * 7
        day = dt.date(2026, 1, 1)
        while day <= dt.date(2026, 2, 8):
            weekday = day.weekday()
            sums[weekday] += daily.get(day.isoformat(), 0)
            counts[weekday] += 1
            day += dt.timedelta(days=1)
        expected = [
            round(s / c, 3) if c else 0.0 for s, c in zip(sums, counts)
        ]
        assert data["weekday_pattern"] == expected
        # Sanity: the 5-unit and 5-unit sales days land where the
        # pattern shows the mass.
        assert sum(sums) == 38


class TestPerProduct:
    def test_ranking_and_share(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        rows = data["per_product"]
        assert [row["sku"] for row in rows] == ["SKU-A", "SKU-B"]
        assert rows[0]["units_sold"] == 35
        assert rows[0]["sale_count"] == 3
        assert rows[0]["share_of_units"] == pytest.approx(
            round(35 / 38, 4)
        )
        assert rows[1]["share_of_units"] == pytest.approx(
            round(3 / 38, 4)
        )

    def test_product_filter_narrows_everything(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        data = analytics_service.get_sales_analytics(
            "2026-01-01", "2026-02-28",
            product_id=two_products_with_sales["a"]["id"],
            db_path=db_path,
        )
        assert data["totals"]["units_sold"] == 35
        assert data["daily"] == {
            "2026-01-05": 10, "2026-01-06": 20, "2026-02-01": 5,
        }
        assert [row["sku"] for row in data["per_product"]] == ["SKU-A"]


class TestValidation:
    def test_inverted_range_rejected(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        with pytest.raises(ValueError, match="must not be after"):
            analytics_service.get_sales_analytics(
                "2026-02-01", "2026-01-01", db_path=db_path
            )

    def test_bad_date_format_rejected(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            analytics_service.get_sales_analytics(
                "01/01/2026", "2026-02-28", db_path=db_path
            )

    def test_empty_range_yields_zeros(self, db_path: Path) -> None:
        data = analytics_service.get_sales_analytics(
            "2030-01-01", "2030-01-07", db_path=db_path
        )
        assert data["totals"]["units_sold"] == 0
        assert data["totals"]["avg_units_per_day"] == 0.0
        assert data["per_product"] == []
        assert all(value == 0.0 for value in data["weekday_pattern"])
