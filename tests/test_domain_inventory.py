"""Tests for the inventory domain calculations (TASK-016 groundwork).

Pure functions over plain numbers: demand windowing (DEC-038), reorder
point (DEC-032), and stock classification (BR-008).
"""

import pytest

from smartstock.domain.inventory import (
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
    calculate_average_daily_demand,
    calculate_reorder_point,
    classify_stock,
)


class TestAverageDailyDemand:
    """30-day window demand (DEC-038)."""

    def test_no_sales_means_zero_demand(self) -> None:
        assert calculate_average_daily_demand({}, today="2026-11-06") == 0.0

    def test_zero_sale_days_count_toward_the_window(self) -> None:
        # One sale of 10 on a single day in a 30-day window.
        daily = {"2026-11-05": 10}
        demand = calculate_average_daily_demand(
            daily, window_days=30, today="2026-11-06"
        )
        assert demand == pytest.approx(10 / 30)

    def test_sales_outside_the_window_are_ignored(self) -> None:
        daily = {"2026-10-01": 100, "2026-11-05": 3}
        demand = calculate_average_daily_demand(
            daily, window_days=30, today="2026-11-06"
        )
        assert demand == pytest.approx(3 / 30)

    def test_window_ending_today_includes_today(self) -> None:
        daily = {"2026-11-06": 15}
        demand = calculate_average_daily_demand(
            daily, window_days=30, today="2026-11-06"
        )
        assert demand == pytest.approx(15 / 30)

    def test_window_edges_are_inclusive(self) -> None:
        # For a 7-day window ending 2026-11-06, sales on 10-31 are in,
        # sales on 10-30 are out.
        inside = calculate_average_daily_demand(
            {"2026-10-31": 7}, window_days=7, today="2026-11-06"
        )
        outside = calculate_average_daily_demand(
            {"2026-10-30": 7}, window_days=7, today="2026-11-06"
        )
        assert inside == pytest.approx(1.0)
        assert outside == 0.0

    def test_invalid_window_rejected(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_average_daily_demand({}, window_days=0)

    def test_invalid_date_rejected(self) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            calculate_average_daily_demand({}, today="11/06/2026")


class TestReorderPoint:
    """DEC-032: demand * lead time + safety stock, rounded up."""

    def test_exact_values(self) -> None:
        assert calculate_reorder_point(2.0, 5, 3) == 13

    def test_ceiling_keeps_shortages_visible(self) -> None:
        # 0.5 * 3 = 1.5 + 0 = 1.5 → 2 (rounding up, never down).
        assert calculate_reorder_point(0.5, 3, 0) == 2

    def test_zero_demand_and_safety(self) -> None:
        # New product with no sales and no safety stock.
        assert calculate_reorder_point(0.0, 3, 0) == 0

    def test_safety_stock_only(self) -> None:
        assert calculate_reorder_point(0.0, 5, 4) == 4

    def test_negative_inputs_rejected(self) -> None:
        with pytest.raises(ValueError, match="nonnegative"):
            calculate_reorder_point(-1.0, 3, 0)
        with pytest.raises(ValueError, match="Lead time"):
            calculate_reorder_point(1.0, -3, 0)
        with pytest.raises(ValueError, match="Safety stock"):
            calculate_reorder_point(1.0, 3, -2)

    def test_non_finite_demand_rejected(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            calculate_reorder_point(float("nan"), 3, 0)


class TestClassifyStock:
    """BR-008 thresholds."""

    def test_out_of_stock_at_zero(self) -> None:
        assert classify_stock(0, 10) == STATUS_OUT_OF_STOCK

    def test_low_stock_at_or_below_reorder_point(self) -> None:
        assert classify_stock(1, 10) == STATUS_LOW_STOCK
        assert classify_stock(10, 10) == STATUS_LOW_STOCK

    def test_in_stock_above_reorder_point(self) -> None:
        assert classify_stock(11, 10) == STATUS_IN_STOCK

    def test_ready_for_new_product(self) -> None:
        # No sales, no safety stock → reorder point 0 → any stock is
        # In Stock; a brand-new empty product is Out of Stock.
        assert classify_stock(0, 0) == STATUS_OUT_OF_STOCK
        assert classify_stock(1, 0) == STATUS_IN_STOCK

    def test_negative_inputs_rejected(self) -> None:
        with pytest.raises(ValueError, match="Current stock"):
            classify_stock(-1, 0)
        with pytest.raises(ValueError, match="Reorder point"):
            classify_stock(1, -1)
