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
            analytics_service.get_product_performance(
                "2026-02-01", "2026-01-01", db_path=db_path
            )
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
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            analytics_service.get_product_performance(
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


class TestProductPerformance:
    """TASK-043 (F-011): trend halves, averages, first/last sale."""

    def test_rows_match_source_data(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        assert [row["sku"] for row in rows] == ["SKU-A", "SKU-B"]
        a = rows[0]
        assert a["units_sold"] == 35
        assert a["sale_count"] == 3
        assert a["avg_units_per_day"] == pytest.approx(
            round(35 / 59, 3)
        )
        assert a["first_sale"] == "2026-01-05"
        assert a["last_sale"] == "2026-02-01"
        b = rows[1]
        assert b["units_sold"] == 3
        assert b["first_sale"] == "2026-01-06"
        assert b["last_sale"] == "2026-01-06"

    def test_rising_when_second_half_heavier(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        # 28-day range → 14 + 14. Item A: 20 units in the first half
        # (Jan 5–6), 5 in the second (Feb 1)... that falls. Build a
        # dedicated rising pattern instead: 2 units in week one,
        # 10 units in the second half.
        product = product_service.create_product(
            name="Riser", sku="SKU-R", initial_stock=30, db_path=db_path
        )
        sales_service.record_sale(product["id"], 2, "2026-01-03", db_path=db_path)
        sales_service.record_sale(product["id"], 10, "2026-01-20", db_path=db_path)
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-01-28", db_path=db_path
        )
        riser = next(row for row in rows if row["sku"] == "SKU-R")
        # First half (Jan 1–14): 2/14 ≈ 0.14; second half: 10/14 ≈ 0.71
        # → ratio ≈ 5 ≥ 1.15 → Rising.
        assert riser["trend"] == "Rising"

    def test_falling_when_second_half_lighter(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        # Item A: first half (Jan 1–29) = 30 units/29 d ≈ 1.034;
        # second half (Jan 30–Feb 28) = 5/30 ≈ 0.167 → ratio 0.16
        # ≤ 0.85 → Falling.
        assert rows[0]["trend"] == "Falling"

    def test_steady_and_stopped_and_single_day(
        self, db_path: Path
    ) -> None:
        steady = product_service.create_product(
            name="Steady", sku="SKU-S", initial_stock=30, db_path=db_path
        )
        stopped = product_service.create_product(
            name="Stopped", sku="SKU-X", initial_stock=30, db_path=db_path
        )
        # Steady: 5 + 6 units, one per half → ratio 1.2... choose 5/5
        # for a clean Steady: same daily average both halves.
        sales_service.record_sale(steady["id"], 5, "2026-01-10", db_path=db_path)
        sales_service.record_sale(steady["id"], 5, "2026-01-24", db_path=db_path)
        # Stopped: sales only in the first half (Jan 1–15 of a
        # 30-day range starting Jan 1).
        sales_service.record_sale(stopped["id"], 8, "2026-01-05", db_path=db_path)
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-01-30", db_path=db_path
        )
        by_sku = {row["sku"]: row for row in rows}
        # Steady: 5/15 vs 5/15 → ratio 1.0.
        assert by_sku["SKU-S"]["trend"] == "Steady"
        # Stopped: 8/15 first half, 0/15 second → Falling (stopped).
        assert by_sku["SKU-X"]["trend"] == "Falling (stopped)"
        # Single-day range cannot be split → Steady.
        single = analytics_service.get_product_performance(
            "2026-01-10", "2026-01-10", db_path=db_path
        )
        assert single[0]["trend"] == "Steady"

    def test_product_filter_narrows_rows(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        a = two_products_with_sales["a"]
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-02-28", product_id=a["id"], db_path=db_path
        )
        assert [row["sku"] for row in rows] == ["SKU-A"]

    def test_products_without_sales_absent(
        self, db_path: Path, two_products_with_sales
    ) -> None:
        product_service.create_product(
            name="Quiet", sku="SKU-Q", initial_stock=5, db_path=db_path
        )
        rows = analytics_service.get_product_performance(
            "2026-01-01", "2026-02-28", db_path=db_path
        )
        assert "SKU-Q" not in [row["sku"] for row in rows]
