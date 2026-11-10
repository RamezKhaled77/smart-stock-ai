"""Tests for application services (TASK-013, TASK-014, TASK-015).

Services run against a temporary database passed explicitly via
``db_path``, so the real ``data/smartstock.db`` is never touched while
still exercising the same code path (session handling and repository
composition) the pages will use.
"""

from pathlib import Path

import datetime as dt

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import (
    inventory_service,
    product_service,
    restock_service,
    sales_service,
)
from smartstock.utils.dates import utc_today_iso


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


@pytest.fixture
def product(db_path: Path) -> dict:
    """A product with 10 units in stock."""
    return product_service.create_product(
        name="Item A",
        sku="SKU-A",
        initial_stock=10,
        lead_time_days=5,
        safety_stock=2,
        db_path=db_path,
    )


class TestProductService:
    """Product creation, retrieval, update, and soft delete."""

    def test_create_applies_defaults_and_initial_stock(
        self, db_path: Path
    ) -> None:
        created = product_service.create_product(
            name="Item B", sku="SKU-B", db_path=db_path
        )
        assert created["current_stock"] == 0
        assert created["lead_time_days"] == 3  # DEC-037 default
        assert created["safety_stock"] == 0  # DEC-036 default
        assert created["is_active"] == 1  # DEC-048

    def test_create_duplicate_sku_rejected(self, db_path: Path, product) -> None:
        with pytest.raises(ValueError, match="SKU-A.*already exists"):
            product_service.create_product(
                name="Copy", sku="SKU-A", db_path=db_path
            )

    def test_get_by_id_and_sku(self, db_path: Path, product) -> None:
        assert product_service.get_product(
            product["id"], db_path=db_path
        )["name"] == "Item A"
        assert product_service.get_product_by_sku(
            "SKU-A", db_path=db_path
        )["id"] == product["id"]
        assert product_service.get_product(999, db_path=db_path) is None

    def test_list_excludes_deactivated(self, db_path: Path, product) -> None:
        other = product_service.create_product(
            name="Item B", sku="SKU-B", db_path=db_path
        )
        product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        active = product_service.list_products(db_path=db_path)
        everyone = product_service.list_products(
            active_only=False, db_path=db_path
        )
        assert [p["id"] for p in active] == [other["id"]]  # BR-026
        assert len(everyone) == 2  # rows preserved (DEC-048)

    def test_update_editable_fields_only(self, db_path: Path, product) -> None:
        updated = product_service.update_product(
            product["id"],
            db_path=db_path,
            name="Item A Renamed",
            lead_time_days=7,
        )
        assert updated["name"] == "Item A Renamed"
        assert updated["lead_time_days"] == 7
        assert updated["current_stock"] == 10  # untouched

    def test_update_stock_through_update_rejected(
        self, db_path: Path, product
    ) -> None:
        with pytest.raises(ValueError, match="inventory service"):
            product_service.update_product(
                product["id"], db_path=db_path, current_stock=99
            )
        # Stock really unchanged.
        assert inventory_service.get_current_stock(
            product["id"], db_path=db_path
        ) == 10

    def test_soft_delete_and_reactivate(self, db_path: Path, product) -> None:
        deactivated = product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        assert deactivated["is_active"] == 0
        assert product_service.get_product(
            product["id"], db_path=db_path
        ) is not None  # row preserved
        reactivated = product_service.set_product_active(
            product["id"], True, db_path=db_path
        )
        assert reactivated["is_active"] == 1


class TestInventoryService:
    """Stock reads and adjustments through the approved operations."""

    def test_adjust_stock_up_and_down(self, db_path: Path, product) -> None:
        assert (
            inventory_service.adjust_stock(
                product["id"], 5, db_path=db_path
            )
            == 15
        )
        assert (
            inventory_service.adjust_stock(
                product["id"], -3, db_path=db_path
            )
            == 12
        )

    def test_adjust_stock_below_zero_rejected(
        self, db_path: Path, product
    ) -> None:
        with pytest.raises(ValueError, match="negative stock is not allowed"):
            inventory_service.adjust_stock(
                product["id"], -11, db_path=db_path
            )
        # DEC-034: stock unchanged after the rejected adjustment.
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 10
        )

    def test_adjust_stock_invalid_change_rejected(
        self, db_path: Path, product
    ) -> None:
        with pytest.raises(ValueError, match="zero"):
            inventory_service.adjust_stock(product["id"], 0, db_path=db_path)
        with pytest.raises(ValueError, match="integer"):
            inventory_service.adjust_stock(
                product["id"], 1.5, db_path=db_path
            )

    def test_set_stock_level_corrections_only(
        self, db_path: Path, product
    ) -> None:
        assert (
            inventory_service.set_stock_level(
                product["id"], 40, db_path=db_path
            )
            == 40
        )
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 40
        )
        with pytest.raises(ValueError, match="nonnegative"):
            inventory_service.set_stock_level(
                product["id"], -1, db_path=db_path
            )

    def test_unknown_product_raises_value_error(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            inventory_service.get_current_stock(999, db_path=db_path)


class TestSalesService:
    """Sales recording with the atomic DEC-035 transaction."""

    def test_record_sale_reduces_stock_and_stores_sale(
        self, db_path: Path, product
    ) -> None:
        sale = sales_service.record_sale(
            product["id"], 4, "2026-11-05", db_path=db_path
        )
        assert sale["quantity"] == 4
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 6  # 10 - 4 (BR-012)
        )
        listed = sales_service.list_sales(
            product["id"], db_path=db_path
        )
        assert [s["id"] for s in listed] == [sale["id"]]

    def test_insufficient_stock_rejects_whole_sale(
        self, db_path: Path, product
    ) -> None:
        with pytest.raises(
            sales_service.InsufficientStockError, match="requested 15"
        ) as error:
            sales_service.record_sale(
                product["id"], 15, "2026-11-05", db_path=db_path
            )
        assert error.value.available == 10
        assert error.value.requested == 15
        # Atomicity (DEC-035): no sale row, stock unchanged.
        assert sales_service.list_sales(product["id"], db_path=db_path) == []
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 10
        )

    def test_quantities_greater_than_stock_after_partial_sales(
        self, db_path: Path, product
    ) -> None:
        sales_service.record_sale(
            product["id"], 3, "2026-11-05", db_path=db_path
        )
        with pytest.raises(sales_service.InsufficientStockError):
            sales_service.record_sale(
                product["id"], 8, "2026-11-05", db_path=db_path
            )
        # Exactly the remaining quantity still works.
        sale = sales_service.record_sale(
            product["id"], 7, "2026-11-06", db_path=db_path
        )
        assert sale["quantity"] == 7
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 0
        )

    def test_future_sale_date_rejected(self, db_path: Path, product) -> None:
        today = utc_today_iso()
        with pytest.raises(ValueError, match="future"):
            sales_service.record_sale(
                product["id"], 1, "2099-01-01", db_path=db_path
            )
        # Today itself is allowed.
        sales_service.record_sale(
            product["id"], 1, today, db_path=db_path
        )
        # Backdated entries are allowed.
        sales_service.record_sale(
            product["id"], 1, "2026-01-15", db_path=db_path
        )

    def test_inactive_product_cannot_be_sold(
        self, db_path: Path, product
    ) -> None:
        product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        with pytest.raises(ValueError, match="inactive"):
            sales_service.record_sale(
                product["id"], 1, "2026-11-05", db_path=db_path
            )
        assert sales_service.list_sales(product["id"], db_path=db_path) == []
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 10
        )

    def test_invalid_quantity_and_date_rejected_before_writes(
        self, db_path: Path, product
    ) -> None:
        with pytest.raises(ValueError, match="positive"):
            sales_service.record_sale(
                product["id"], 0, "2026-11-05", db_path=db_path
            )
        with pytest.raises(ValueError, match="integer"):
            sales_service.record_sale(
                product["id"], 2.5, "2026-11-05", db_path=db_path
            )
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            sales_service.record_sale(
                product["id"], 1, "05/11/2026", db_path=db_path
            )
        assert sales_service.list_sales(product["id"], db_path=db_path) == []
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == 10
        )

class TestStockOverview:
    """Listing overview: demand (DEC-059), reorder point (DEC-032),
    status (BR-008) per active product."""

    def test_new_product_without_sales(self, db_path: Path) -> None:
        product_service.create_product(
            name="New Item", sku="SKU-NEW", db_path=db_path
        )
        overview = inventory_service.get_stock_overview(db_path=db_path)
        assert len(overview) == 1
        row = overview[0]
        assert row["average_daily_demand"] == 0.0
        assert row["reorder_point"] == 0  # 0 demand, safety 0 by default
        assert row["stock_status"] == "Out of Stock"  # stock 0

    def test_status_uses_demand_lead_and_safety(
        self, db_path: Path, product
    ) -> None:
        # Sale of 8 today: the DEC-059 window ends at this last sale,
        # span 1 day → demand = 8.0.
        sales_service.record_sale(
            product["id"], 8, utc_today_iso(), db_path=db_path
        )
        overview = inventory_service.get_stock_overview(db_path=db_path)
        row = overview[0]
        # Stock after the sale: 10 - 8 = 2.
        assert row["current_stock"] == 2
        assert row["average_daily_demand"] == pytest.approx(8.0)
        # reorder = ceil(8 * 5) + 2 = 42 (DEC-032)
        assert row["reorder_point"] == 42
        assert row["stock_status"] == "Low Stock"  # 2 <= 42

    def test_overview_excludes_inactive_products(
        self, db_path: Path, product
    ) -> None:
        other = product_service.create_product(
            name="Item B", sku="SKU-B", db_path=db_path
        )
        product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        overview = inventory_service.get_stock_overview(db_path=db_path)
        assert [row["id"] for row in overview] == [other["id"]]

    def test_backdated_sale_anchors_the_demand_window(
        self, db_path: Path, product
    ) -> None:
        # DEC-059: an old backdated sale is the last recorded sale, so
        # the window ends there (1-day span → demand = 5.0) rather than
        # today going forward with zeros.
        sales_service.record_sale(
            product["id"], 5, "2026-01-01", db_path=db_path
        )
        overview = inventory_service.get_stock_overview(db_path=db_path)
        row = overview[0]
        assert row["average_daily_demand"] == pytest.approx(5.0)
        assert row["reorder_point"] == 27  # ceil(5 * 5) + 2 = 27
        assert row["stock_status"] == "Low Stock"  # 5 <= 27

    def test_daily_sales_and_filters(self, db_path: Path, product) -> None:
        sales_service.record_sale(
            product["id"], 2, "2026-11-01", db_path=db_path
        )
        sales_service.record_sale(
            product["id"], 1, "2026-11-01", db_path=db_path
        )
        sales_service.record_sale(
            product["id"], 3, "2026-11-03", db_path=db_path
        )
        daily = sales_service.get_daily_sales(
            product["id"], "2026-11-01", "2026-11-30", db_path=db_path
        )
        assert daily == {"2026-11-01": 3, "2026-11-03": 3}
        window = sales_service.list_sales(
            product["id"],
            start_date="2026-11-02",
            end_date="2026-11-30",
            db_path=db_path,
        )
        assert [s["sale_date"] for s in window] == ["2026-11-03"]


class TestRestockRecommendations:
    """Advisory recommendation listing (TASK-035, read-only)."""

    def test_unavailable_without_history_but_stock_shown(
        self, db_path: Path
    ) -> None:
        product_service.create_product(
            name="No Sales Yet", sku="SKU-NONE", db_path=db_path
        )
        rows = restock_service.get_restock_recommendations(
            db_path=db_path
        )
        assert len(rows) == 1
        row = rows[0]
        assert row["available"] is False
        assert "No sales are recorded" in row["unavailable_reason"]
        assert row["current_stock"] == 0
        assert row["average_daily_demand"] is None
        assert row["reorder_point"] is None
        assert row["target_stock"] is None
        assert row["recommended_order_quantity"] is None

    def test_recommendation_follows_all_confirmed_formulas(
        self, db_path: Path
    ) -> None:
        stocky = product_service.create_product(
            name="Item B",
            sku="SKU-B",
            initial_stock=20,
            lead_time_days=5,
            safety_stock=2,
            db_path=db_path,
        )
        # Sale of 8 today and 4 four days ago: span 5 → ADD = 12/5.
        today = utc_today_iso()
        four_days_ago = (
            dt.date.fromisoformat(today) - dt.timedelta(days=4)
        ).isoformat()
        sales_service.record_sale(
            stocky["id"], 8, today, db_path=db_path
        )
        sales_service.record_sale(
            stocky["id"], 4, four_days_ago, db_path=db_path
        )
        row = restock_service.get_restock_recommendations(
            db_path=db_path
        )[0]
        assert row["available"] is True
        assert row["demand_window_days_used"] == 5
        assert row["average_daily_demand"] == pytest.approx(2.4)
        # reorder = ceil(2.4 * 5) + 2 = 14 (DEC-032)
        assert row["reorder_point"] == 14
        # target = ceil(2.4)=3 → 3 * (5 + 7) + 2 = 38 (DEC-038)
        assert row["target_stock"] == 38
        # order = max(0, 38 - 8) = 30 (DEC-033; stock 20 - 12 = 8)
        assert row["current_stock"] == 8
        assert row["recommended_order_quantity"] == 30
        assert row["needs_reorder"] is True
        assert row["stock_status"] == "Low Stock"

    def test_recommendations_are_read_only(
        self, db_path: Path, product
    ) -> None:
        sales_service.record_sale(
            product["id"], 3, "2026-11-05", db_path=db_path
        )
        stock_before = inventory_service.get_current_stock(
            product["id"], db_path=db_path
        )
        restock_service.get_restock_recommendations(db_path=db_path)
        restock_service.get_restock_recommendations(db_path=db_path)
        # Nothing mutated: stock identical, sale rows identical.
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=db_path
            )
            == stock_before
        )
        assert len(
            sales_service.list_sales(product["id"], db_path=db_path)
        ) == 1

    def test_recommendations_exclude_inactive_products(
        self, db_path: Path, product
    ) -> None:
        product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        assert (
            restock_service.get_restock_recommendations(db_path=db_path)
            == []
        )
