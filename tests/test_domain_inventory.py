"""Tests for the inventory domain calculations (TASK-016 groundwork,
restocked for TASK-035's DEC-059 anchoring).

Pure functions over plain numbers: demand windowing (DEC-059), reorder
point (DEC-032), target stock (DEC-038), order quantity (DEC-033), and
stock classification (BR-008).
"""

import pytest

from smartstock.domain.inventory import (
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
    calculate_average_daily_demand,
    calculate_recommended_order_quantity,
    calculate_reorder_point,
    calculate_target_stock,
    classify_stock,
    demand_window_days_used,
)
from smartstock.domain.restocking import build_restock_recommendation


class TestAverageDailyDemand:
    """DEC-059: window anchored at the last sale, zeros filled."""

    def test_no_sales_means_zero_demand(self) -> None:
        assert calculate_average_daily_demand({}) == 0.0

    def test_lone_backdated_sale_spans_one_day(self) -> None:
        # DEC-059: the window ends at the last recorded sale; a single
        # sale day is a 1-day span, so the demand is the sale itself —
        # NOT the sale divided by 30.
        daily = {"2026-01-05": 10}
        assert calculate_average_daily_demand(daily) == pytest.approx(10.0)

    def test_gaps_inside_the_window_count_as_zero(self) -> None:
        # Sales 10 calendar days apart: window = 10 days, both inside.
        daily = {"2026-01-01": 4, "2026-01-10": 2}
        demand = calculate_average_daily_demand(daily)
        assert demand == pytest.approx(6 / 10)

    def test_window_capped_at_requested_length(self) -> None:
        # History spans 60 days; only the most recent 30 count.
        daily = {
            "2026-09-01": 30,  # 41 days before the last sale: out
            "2026-10-01": 10,  # 01 days before the last sale: in
            "2026-10-02": 60,  # last sale day (window end)
        }
        assert calculate_average_daily_demand(daily) == pytest.approx(
            70 / 30
        )

    def test_days_outside_the_window_are_ignored(self) -> None:
        daily = {
            "2026-08-01": 100,  # more than 30 days before the last sale
            "2026-09-01": 5,
        }
        # Span = 32 days > 30 → window = 30 days ending 09-01, from
        # 08-03 on: the 08-01 sale drops out, 09-01 stays.
        assert calculate_average_daily_demand(daily) == pytest.approx(
            5 / 30
        )

    def test_edges_of_a_short_window_are_inclusive(self) -> None:
        # Span 7 days with window_days=7: both edges count.
        daily = {
            "2026-01-01": 7,
            "2026-01-07": 0,  # zero-sale day still inside the span
        }
        assert calculate_average_daily_demand(
            daily, window_days=7
        ) == pytest.approx(1.0)
        # history_sales sums 7 over 7 days.

    def test_invalid_window_rejected(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            calculate_average_daily_demand({}, window_days=0)

    def test_invalid_date_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            calculate_average_daily_demand({"11/06/2026": 5})


class TestDemandWindowDaysUsed:
    """REPORT: the calendar denominator DEC-059 actually used."""

    def test_zero_without_history(self) -> None:
        assert demand_window_days_used({}) == 0

    def test_single_day_history_uses_one(self) -> None:
        assert demand_window_days_used({"2026-01-05": 3}) == 1

    def test_span_capped_at_thirty(self) -> None:
        daily = {"2025-01-01": 1, "2026-01-01": 1}
        assert demand_window_days_used(daily) == 30

    def test_short_span_used_whole(self) -> None:
        daily = {"2025-01-01": 1, "2025-01-04": 1}
        assert demand_window_days_used(daily) == 4


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


class TestTargetStock:
    """DEC-038: ceil(demand) × (lead + 7) + safety, whole units."""

    def test_exact_values(self) -> None:
        # 2.0 × (5 + 7) + 3 = 27.
        assert calculate_target_stock(2.0, 5, 3) == 27

    def test_demand_ceiled_before_multiplication(self) -> None:
        # 0.5 → ceil = 1 → 1 × (3 + 7) + 0 = 10 (not 0.5 × 10 + 0).
        assert calculate_target_stock(0.5, 3, 0) == 10

    def test_floored_demand_would_undercount(self) -> None:
        # 1.8 → ceil 2 → 2 × 12 = 24; floor(1.8) × 12 = 12 would hide
        # nearly two days of covered demand.
        assert calculate_target_stock(1.8, 5, 0) == 24

    def test_zero_demand_yields_safety_only(self) -> None:
        assert calculate_target_stock(0.0, 3, 4) == 4

    def test_buffer_days_are_part_of_the_factor(self) -> None:
        # Zero lead time still carries the 7-day buffer (DEC-038).
        assert calculate_target_stock(1.0, 0, 0) == 7

    def test_negative_inputs_rejected(self) -> None:
        with pytest.raises(ValueError, match="nonnegative"):
            calculate_target_stock(-1.0, 3, 0)
        with pytest.raises(ValueError, match="Lead time"):
            calculate_target_stock(1.0, -3, 0)
        with pytest.raises(ValueError, match="Safety stock"):
            calculate_target_stock(1.0, 3, -2)

    def test_non_finite_demand_rejected(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            calculate_target_stock(float("inf"), 3, 0)


class TestRecommendedOrderQuantity:
    """DEC-033: max(0, target − current), nonnegative actionable."""

    def test_stock_below_target_needs_positive_order(self) -> None:
        assert calculate_recommended_order_quantity(27, 5) == 22

    def test_stock_at_target_orders_nothing(self) -> None:
        assert calculate_recommended_order_quantity(27, 27) == 0

    def test_stock_above_target_is_clamped_to_zero(self) -> None:
        assert calculate_recommended_order_quantity(27, 40) == 0
        # No negative "surplus" recommendations (DEC-033).

    def test_all_zero_inputs(self) -> None:
        assert calculate_recommended_order_quantity(0, 0) == 0

    def test_negative_inputs_rejected(self) -> None:
        with pytest.raises(ValueError, match="Target stock"):
            calculate_recommended_order_quantity(-1, 0)
        with pytest.raises(ValueError, match="Current stock"):
            calculate_recommended_order_quantity(1, -1)

    def test_non_integer_inputs_rejected(self) -> None:
        with pytest.raises(ValueError, match="Target stock"):
            calculate_recommended_order_quantity(2.5, 0)
        with pytest.raises(ValueError, match="Current stock"):
            calculate_recommended_order_quantity(1, True)  # bool guard


class TestRestockRecommendation:
    """Composition (TASK-035): formulas into one advisory record."""

    def product(self, **overrides) -> dict:
        base = {
            "id": 1,
            "name": "Item A",
            "sku": "SKU-A",
            "current_stock": 2,
            "lead_time_days": 5,
            "safety_stock": 2,
        }
        base.update(overrides)
        return base

    def test_unavailable_without_history_keeps_stock_visible(self) -> None:
        recommendation = build_restock_recommendation(self.product(), {})
        assert recommendation.available is False
        assert "No sales are recorded" in recommendation.unavailable_reason
        # Known fields stay visible; advice fields are absent (not 0).
        assert recommendation.current_stock == 2
        assert recommendation.average_daily_demand is None
        assert recommendation.reorder_point is None
        assert recommendation.target_stock is None
        assert recommendation.recommended_order_quantity is None
        assert recommendation.demand_window_days_used == 0

    def test_unavailable_without_stock_level(self) -> None:
        recommendation = build_restock_recommendation(
            self.product(current_stock=None), {"2026-11-10": 4}
        )
        assert recommendation.available is False
        assert "stock level" in recommendation.unavailable_reason
        assert recommendation.reorder_point is None

    def test_available_recommendation_follows_all_formulas(self) -> None:
        # Sales today (8) and 4 days ago (4): span 5 → ADD = 12/5 = 2.4.
        daily = {"2026-11-10": 8, "2026-11-06": 4}
        recommendation = build_restock_recommendation(
            self.product(), daily
        )
        assert recommendation.available is True
        assert recommendation.average_daily_demand == pytest.approx(2.4)
        assert recommendation.demand_window_days_used == 5
        # reorder = ceil(2.4 * 5) + 2 = 14 (DEC-032)
        assert recommendation.reorder_point == 14
        # target = ceil(2.4)=3 → 3 * (5 + 7) + 2 = 38 (DEC-038)
        assert recommendation.target_stock == 38
        # order = max(0, 38 - 2) = 36 (DEC-033)
        assert recommendation.recommended_order_quantity == 36
        assert recommendation.stock_status == STATUS_LOW_STOCK  # 2 <= 14
        assert recommendation.needs_reorder is True
        assert "DEC-032" in recommendation.explanation
        assert "DEC-038" in recommendation.explanation
        assert "DEC-033" in recommendation.explanation

    def test_no_reorder_needed_when_stock_exceeds_target(self) -> None:
        # One sale of 1 → 1-day span → ADD = 1.0
        # target = 1 * (5 + 7) + 2 = 14 < 50 → order 0, In Stock.
        recommendation = build_restock_recommendation(
            self.product(current_stock=50), {"2026-11-10": 1}
        )
        assert recommendation.target_stock == 14
        assert recommendation.recommended_order_quantity == 0
        assert recommendation.needs_reorder is False
        assert recommendation.stock_status == STATUS_IN_STOCK

    def test_out_of_stock_always_needs_reorder(self) -> None:
        recommendation = build_restock_recommendation(
            self.product(current_stock=0), {"2026-11-10": 2}
        )
        assert recommendation.stock_status == STATUS_OUT_OF_STOCK
        assert recommendation.needs_reorder is True
        assert recommendation.recommended_order_quantity > 0


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
