"""Restocking recommendation composition (TASK-035).

Combines the approved inventory formulas into one recommendation per
product. This layer stays independent of Streamlit and of the database:
:func:`build_restock_recommendation` receives the product dictionary
and the product's daily sales totals and returns plain data.

Decision references:

- BR-020/DEC-032: Reorder Point = ceil(ADD × lead time) + safety stock.
- BR-024/DEC-038: Target Stock = ceil(ADD) × (lead time + 7) + safety.
- BR-023/DEC-033: Order Quantity = max(0, target − current stock).
- BR-022: reorder check ``current stock ≤ reorder point`` (inventory
  position = current stock in v1, DEC-031).
- DEC-059: ADD = calendar-window mean anchored at the last recorded
  sale, zeros filled, window min(30, history span).
- DEC-037/DEC-036: lead time and safety stock are manual per-product
  fields (defaults applied by the product schema: 3 days and 0).
- Recommendations are advisory (DEC-031): nothing here changes stock.
"""

from dataclasses import dataclass

from smartstock.domain.inventory import (
    DEMAND_WINDOW_DAYS,
    calculate_average_daily_demand,
    calculate_reorder_point,
    calculate_recommended_order_quantity,
    calculate_target_stock,
    classify_stock,
    demand_window_days_used,
)

# Products without history cannot yield a meaningful demand estimate:
# ADD would be 0.0 for purely arithmetic reasons, which would read as
# "for sure no reorder" rather than "unknown" (DEC-033 availability).
UNAVAILABLE_NO_HISTORY = (
    "No sales are recorded for this product yet, so average daily "
    "demand cannot be estimated. Add a sale first."
)
UNAVAILABLE_NO_STOCK_FIELD = (
    "This product has no recorded stock level, so the order quantity "
    "cannot be calculated. Set the stock level first."
)


@dataclass
class RestockRecommendation:
    """One product's advisory restocking picture.

    When ``available`` is ``False`` all numeric advice fields are
    ``None`` and ``unavailable_reason`` explains why (advisory absence,
    never a silent zero — DEC-031's transparency requirement).
    """

    product_id: int
    product_name: str
    product_sku: str
    available: bool
    unavailable_reason: str | None
    current_stock: int | None
    average_daily_demand: float | None
    demand_window_days_used: int | None
    reorder_point: int | None
    stock_status: str | None
    needs_reorder: bool | None
    target_stock: int | None
    recommended_order_quantity: int | None
    explanation: str


def build_restock_recommendation(
    product: dict,
    daily_totals: dict[str, int],
) -> RestockRecommendation:
    """Compose one product's recommendation from approved formulas.

    Args:
        product: Product dictionary (schema fields like
            ``current_stock``, ``lead_time_days``, ``safety_stock``).
        daily_totals: The product's full observed daily sales totals
            (``YYYY-MM-DD`` → quantity; DEC-059 anchoring applies).

    Returns:
        A :class:`RestockRecommendation`. Unavailable (with a plain
        explanation) when the product has no sales history at all or
        lacks a recorded stock level; otherwise all advice fields are
        filled and ``needs_reorder`` follows BR-022.
    """
    base = {
        "product_id": product["id"],
        "product_name": product["name"],
        "product_sku": product["sku"],
    }
    daily_totals = dict(daily_totals)

    if product.get("current_stock") is None:
        return RestockRecommendation(
            available=False,
            unavailable_reason=UNAVAILABLE_NO_STOCK_FIELD,
            current_stock=None,
            average_daily_demand=None,
            demand_window_days_used=None,
            reorder_point=None,
            stock_status=None,
            needs_reorder=None,
            target_stock=None,
            recommended_order_quantity=None,
            explanation=UNAVAILABLE_NO_STOCK_FIELD,
            **base,
        )

    if not daily_totals:
        return RestockRecommendation(
            available=False,
            unavailable_reason=UNAVAILABLE_NO_HISTORY,
            current_stock=int(product["current_stock"]),
            average_daily_demand=None,
            demand_window_days_used=0,
            reorder_point=None,
            stock_status=None,
            needs_reorder=None,
            target_stock=None,
            recommended_order_quantity=None,
            explanation=(
                f"No sales history: {UNAVAILABLE_NO_HISTORY} A restock "
                "recommendation appears from the first recorded sale "
                "(DEC-058 availability policy)."
            ),
            **base,
        )

    current_stock = int(product["current_stock"])
    lead_time_days = int(product["lead_time_days"])
    safety_stock = int(product["safety_stock"])

    demand = calculate_average_daily_demand(
        daily_totals, DEMAND_WINDOW_DAYS
    )
    window_days = demand_window_days_used(daily_totals, DEMAND_WINDOW_DAYS)
    reorder_point = calculate_reorder_point(
        demand, lead_time_days, safety_stock
    )
    target_stock = calculate_target_stock(
        demand, lead_time_days, safety_stock
    )
    order_quantity = calculate_recommended_order_quantity(
        target_stock, current_stock
    )
    stock_status = classify_stock(current_stock, reorder_point)
    needs_reorder = current_stock <= reorder_point  # BR-022

    explanation = (
        f"Average daily demand is {demand:.2f} units/day over the "
        f"last {window_days} day(s) up to the most recent sale "
        "(DEC-059). "
        f"Reorder point = {reorder_point} (ceil(demand × lead time "
        f"{lead_time_days}) + safety {safety_stock}, DEC-032); "
        f"target stock = {target_stock} "
        f"(ceil(demand) × ({lead_time_days} + 7) + safety, DEC-038); "
        f"order {order_quantity} unit(s) to reach target "
        "(max(0, target − stock), DEC-033). "
        "The decision to order stays with you (advisory, DEC-031)."
    )

    return RestockRecommendation(
        available=True,
        unavailable_reason=None,
        current_stock=current_stock,
        average_daily_demand=demand,
        demand_window_days_used=window_days,
        reorder_point=reorder_point,
        stock_status=stock_status,
        needs_reorder=needs_reorder,
        target_stock=target_stock,
        recommended_order_quantity=order_quantity,
        explanation=explanation,
        **base,
    )
