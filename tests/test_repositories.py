"""Tests for repositories (TASK-012).

Each test runs against a freshly initialized temporary database with a
controlled product set. Small fixtures, not the real dataset.
"""

from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.database.connection import session
from smartstock.repositories import (
    inventory_repository,
    product_repository,
    sales_repository,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


@pytest.fixture
def product_a(db_path: Path) -> dict:
    """A product existing across all tests (id 1)."""
    with session(db_path) as conn:
        return product_repository.create_product(
            conn,
            name="Item A",
            sku="SKU-A",
            category="Sweets",
            current_stock=10,
        )


class TestProductRepository:
    """Create, read, update, and soft-delete behavior."""

    def test_create_with_defaults(self, db_path: Path, product_a: dict) -> None:
        assert product_a["name"] == "Item A"
        assert product_a["sku"] == "SKU-A"
        assert product_a["current_stock"] == 10
        # Approved defaults (DEC-036, DEC-037, DEC-048).
        assert product_a["lead_time_days"] == 3
        assert product_a["safety_stock"] == 0
        assert product_a["is_active"] == 1

    def test_create_applies_only_defaults(self, db_path: Path) -> None:
        with session(db_path) as conn:
            created = product_repository.create_product(
                conn, name="Item K", sku="SKU-K"
            )
        assert created["current_stock"] == 0
        assert created["category"] == ""

    def test_create_rejects_empty_name(self, db_path: Path) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="name"):
                product_repository.create_product(conn, name="  ", sku="S1")

    def test_create_rejects_negative_stock(self, db_path: Path) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="current_stock"):
                product_repository.create_product(
                    conn, name="X", sku="S2", current_stock=-5
                )

    def test_duplicate_sku_rejected_with_clear_error(
        self, db_path: Path, product_a: dict
    ) -> None:
        with pytest.raises(ValueError, match="SKU-A"):
            with session(db_path) as conn:
                product_repository.create_product(conn, name="Copy", sku="SKU-A")

    def test_get_and_list(self, db_path: Path, product_a: dict) -> None:
        with session(db_path) as conn:
            product_repository.create_product(conn, name="Item B", sku="SKU-B")
            fetched = product_repository.get_product(conn, product_a["id"])
            assert fetched is not None
            assert fetched["sku"] == "SKU-A"
            missing = product_repository.get_product(conn, 999)
            by_sku = product_repository.get_product_by_sku(conn, "SKU-B")
            listed = product_repository.list_products(conn)

        assert missing is None
        assert by_sku["name"] == "Item B"
        assert [product["sku"] for product in listed] == ["SKU-A", "SKU-B"]

    def test_update_fields_and_updated_at(
        self, db_path: Path, product_a: dict
    ) -> None:
        old_updated_at = product_a["updated_at"]
        with session(db_path) as conn:
            product_repository.set_product_active(conn, product_a["id"], True)
            updated = product_repository.update_product(
                conn,
                product_a["id"],
                name="Item A2",
                lead_time_days=5,
                safety_stock=2,
            )
        assert updated["name"] == "Item A2"
        assert updated["lead_time_days"] == 5
        assert updated["safety_stock"] == 2
        # category/current_stock untouched when not provided
        assert updated["current_stock"] == 10

    def test_update_sku_conflict_rejected(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            product_repository.create_product(conn, name="Item B", sku="SKU-B")
            with pytest.raises(ValueError, match="SKU-B"):
                product_repository.update_product(
                    conn, product_a["id"], sku="SKU-B"
                )

    def test_soft_delete_keeps_row(
        self, db_path: Path, product_a: dict
    ) -> None:
        product_id = product_a["id"]
        with session(db_path) as conn:
            deactivated = product_repository.set_product_active(
                conn, product_id, False
            )
            active_list = product_repository.list_products(conn)
            all_list = product_repository.list_products(conn, active_only=False)
            still_there = product_repository.get_product(conn, product_id)

        assert deactivated["is_active"] == 0
        assert active_list == []
        assert len(all_list) == 1  # row preserved (DEC-048)
        assert still_there == all_list[0]

    def test_invalid_is_active_argument(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="boolean"):
                product_repository.set_product_active(
                    conn, product_a["id"], 1
                )


class TestInventoryRepository:
    """Stock reads and adjustments with the DEC-034 guard."""

    def test_get_current_stock(self, db_path: Path, product_a: dict) -> None:
        with session(db_path) as conn:
            stock = inventory_repository.get_current_stock(
                conn, product_a["id"]
            )
        assert stock == 10

    def test_get_current_stock_unknown_product(self, db_path: Path) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="does not exist"):
                inventory_repository.get_current_stock(conn, 999)

    def test_adjust_stock_up_and_down(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            after_add = inventory_repository.adjust_stock(
                conn, product_a["id"], +4
            )
            after_remove = inventory_repository.adjust_stock(
                conn, product_a["id"], -2
            )
        assert (after_add, after_remove) == (14, 12)

    def test_adjust_stock_to_negative_rejected(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="negative stock is not allowed"):
                inventory_repository.adjust_stock(
                    conn, product_a["id"], -11
                )
            # Stock unchanged after the rejected adjustment.
            assert inventory_repository.get_current_stock(
                conn, product_a["id"]
            ) == 10

    def test_adjust_stock_zero_rejected(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="zero"):
                inventory_repository.adjust_stock(conn, product_a["id"], 0)

    def test_adjust_stock_non_integer_rejected(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="integer"):
                inventory_repository.adjust_stock(conn, product_a["id"], 2.5)

    def test_set_stock_level_correction(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            new_level = inventory_repository.set_stock_level(
                conn, product_a["id"], 25
            )
        assert new_level == 25
        with session(db_path) as conn:
            assert inventory_repository.get_current_stock(
                conn, product_a["id"]
            ) == 25

    def test_set_stock_level_rejects_negative(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="nonnegative"):
                inventory_repository.set_stock_level(conn, product_a["id"], -1)


class TestSalesRepository:
    """Recording and reading sales."""

    def test_record_and_list_sale(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            sale = sales_repository.record_sale(
                conn, product_a["id"], 3, "2026-11-01"
            )
            listed = sales_repository.list_sales(conn, product_a["id"])
        assert sale["quantity"] == 3
        assert sale["product_id"] == product_a["id"]
        assert sale["sale_date"] == "2026-11-01"
        assert len(listed) == 1
        assert listed[0]["quantity"] == 3

    def test_record_sale_validations(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(ValueError, match="positive"):
                sales_repository.record_sale(
                    conn, product_a["id"], 0, "2026-11-01"
                )
            with pytest.raises(ValueError, match="YYYY-MM-DD"):
                sales_repository.record_sale(
                    conn, product_a["id"], 2, "01/11/2026"
                )
            with pytest.raises(ValueError, match="integer"):
                sales_repository.record_sale(
                    conn, product_a["id"], 2.5, "2026-11-01"
                )

    def test_record_sale_unknown_product_raises_database_error(
        self, db_path: Path
    ) -> None:
        with session(db_path) as conn:
            with pytest.raises(
                sales_repository.DatabaseError, match="does not exist"
            ):
                sales_repository.record_sale(
                    conn, 999, 1, "2026-11-01"
                )

    def test_list_sales_filters(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            product_b = product_repository.create_product(
                conn, name="Item B", sku="SKU-B"
            )
            sales_repository.record_sale(conn, product_a["id"], 1, "2026-10-30")
            sales_repository.record_sale(conn, product_a["id"], 2, "2026-11-01")
            sales_repository.record_sale(conn, product_b["id"], 5, "2026-11-01")

            in_window = sales_repository.list_sales(
                conn, product_a["id"], "2026-11-01", "2026-11-30"
            )
            ending_bounds = sales_repository.list_sales(
                conn, start_date="2026-11-01", end_date="2026-11-01"
            )
            none = sales_repository.list_sales(
                conn, product_b["id"], "2026-10-01", "2026-10-31"
            )

        assert len(in_window) == 1
        assert in_window[0]["quantity"] == 2
        assert len(ending_bounds) == 2  # A(2) + B(5) on 2026-11-01
        assert none == []

    def test_daily_sales_aggregation(self, db_path: Path, product_a: dict) -> None:
        with session(db_path) as conn:
            sales_repository.record_sale(conn, product_a["id"], 1, "2026-11-01")
            sales_repository.record_sale(conn, product_a["id"], 2, "2026-11-01")
            sales_repository.record_sale(conn, product_a["id"], 4, "2026-11-03")
            daily = sales_repository.get_daily_sales(
                conn, product_a["id"], "2026-11-01", "2026-11-30"
            )
        # Days without sales are absent (preprocessing policy).
        assert daily == {"2026-11-01": 3, "2026-11-03": 4}

    def test_daily_sales_by_product_groups_all_products(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            product_b = product_repository.create_product(
                conn, name="Item B", sku="SKU-B"
            )
            sales_repository.record_sale(conn, product_a["id"], 3, "2026-11-01")
            sales_repository.record_sale(conn, product_a["id"], 1, "2026-11-02")
            sales_repository.record_sale(conn, product_b["id"], 5, "2026-11-02")
            totals = sales_repository.get_daily_sales_by_product(
                conn, "2026-11-01", "2026-11-30"
            )
        assert totals == {
            product_a["id"]: {"2026-11-01": 3, "2026-11-02": 1},
            product_b["id"]: {"2026-11-02": 5},
        }

    def test_daily_sales_by_product_empty_window(
        self, db_path: Path, product_a: dict
    ) -> None:
        with session(db_path) as conn:
            sales_repository.record_sale(conn, product_a["id"], 1, "2026-11-01")
            totals = sales_repository.get_daily_sales_by_product(
                conn, "2026-12-01", "2026-12-31"
            )
        assert totals == {}
