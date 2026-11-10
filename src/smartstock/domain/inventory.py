"""Core inventory business rules.

Contains stock-level calculations that are independent of Streamlit and
of the database implementation: callers pass in plain numbers.

Decision references:
- DEC-032: ``Reorder Point = Average Daily Demand * Lead Time + Safety
  Stock`` (inputs defined by DEC-037/DEC-036 and DEC-038 for demand).
- DEC-038: Average Daily Demand uses the most recent 30-day window.
- DEC-059 (2026-11-10, TASK-035): the window is anchored at the
  product's **last recorded sale date**, covers the min(30, history
  span) calendar days, and no-sale days inside the window count as
  zero demand.
- DEC-038: Target Stock = Average Daily Demand × (Lead Time + 7 days)
  + Safety Stock, with demand rounded up to whole units.
- DEC-033: Recommended Order Quantity = max(0, Target Stock − Current
  Stock).
- BR-008: stock status classes are Out of Stock, Low Stock, In Stock.
"""

import datetime as dt
import math

# Demand window used by the reorder point (DEC-038).
DEMAND_WINDOW_DAYS = 30

# Days of post-replenishment buffer in the target stock (DEC-038).
TARGET_STOCK_BUFFER_DAYS = 7

# Stock status classes (BR-008).
STATUS_IN_STOCK = "In Stock"
STATUS_LOW_STOCK = "Low Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"


def calculate_average_daily_demand(
    daily_totals: dict[str, int],
    window_days: int = DEMAND_WINDOW_DAYS,
) -> float:
    """Average demand per day over the product's available history.

    Per DEC-059 the window ends at the product's last recorded sale
    date and covers up to ``window_days`` calendar days — fewer when
    the whole history spans less — with days without sales counting as
    zero demand. A product that sells only once in a month has a low
    average, which is the correct signal for restocking decisions.

    Args:
        daily_totals: Sold quantity per ``YYYY-MM-DD`` day (from the
            sales repository's aggregate queries). The full available
            history may be passed; earlier records outside the window
            are ignored.
        window_days: Maximum window length (default 30, DEC-038).

    Returns:
        The average daily demand as a nonnegative float. With no sales
        at all the result is 0.0.
    """
    if isinstance(window_days, bool) or not isinstance(
        window_days, int
    ) or window_days <= 0:
        raise ValueError(
            f"window_days must be a positive integer, got {window_days!r}."
        )
    if not daily_totals:
        return 0.0
    parsed_dates = {value: _parse_date(value) for value in daily_totals}
    end_date = max(parsed_dates.values())
    first_date = min(parsed_dates.values())
    window_start = max(
        first_date, end_date - dt.timedelta(days=window_days - 1)
    )
    window_used = (end_date - window_start).days + 1

    total_quantity = 0
    current = window_start
    while current <= end_date:
        total_quantity += daily_totals.get(current.isoformat(), 0)
        current += dt.timedelta(days=1)
    return total_quantity / window_used


def demand_window_days_used(
    daily_totals: dict[str, int], window_days: int = DEMAND_WINDOW_DAYS
) -> int:
    """Calendar days in the DEC-059 demand window (0 without history)."""
    if isinstance(window_days, bool) or not isinstance(
        window_days, int
    ) or window_days <= 0:
        raise ValueError(
            f"window_days must be a positive integer, got {window_days!r}."
        )
    if not daily_totals:
        return 0
    parsed_dates = [_parse_date(value) for value in daily_totals]
    span = (max(parsed_dates) - min(parsed_dates)).days + 1
    return min(span, window_days)


def _validated_demand_inputs(
    average_daily_demand: float,
    lead_time_days: int,
    safety_stock: int,
) -> None:
    """Shared validation for DEC-032/DEC-038 formula inputs."""
    if not math.isfinite(average_daily_demand):
        raise ValueError(
            f"Average demand must be a finite number, got "
            f"{average_daily_demand!r}."
        )
    if average_daily_demand < 0:
        raise ValueError("Average demand must be nonnegative.")
    if isinstance(lead_time_days, bool) or not isinstance(
        lead_time_days, int
    ) or lead_time_days < 0:
        raise ValueError(
            f"Lead time must be a nonnegative integer, got "
            f"{lead_time_days!r}."
        )
    if isinstance(safety_stock, bool) or not isinstance(
        safety_stock, int
    ) or safety_stock < 0:
        raise ValueError(
            f"Safety stock must be a nonnegative integer, got "
            f"{safety_stock!r}."
        )


def calculate_reorder_point(
    average_daily_demand: float,
    lead_time_days: int,
    safety_stock: int,
) -> int:
    """Reorder point per DEC-032, rounded up to whole units.

    ``Reorder Point = Average Daily Demand * Lead Time + Safety Stock``

    Rounding is upward (ceiling) so rounding can never hide a shortage.

    Raises:
        ValueError: If any input is negative or the demand is not
            finite.
    """
    _validated_demand_inputs(
        average_daily_demand, lead_time_days, safety_stock
    )
    reorder_point = (
        average_daily_demand * lead_time_days + safety_stock
    )
    return math.ceil(reorder_point)


def calculate_target_stock(
    average_daily_demand: float,
    lead_time_days: int,
    safety_stock: int,
) -> int:
    """Target stock per DEC-038, rounded up to whole units.

    ``Target Stock = ceil(Average Daily Demand) * (Lead Time + 7 days)
    + Safety Stock``

    The (Lead Time + 7 days) factor covers expected demand during
    replenishment plus a 7-day buffer after restock. The demand is
    rounded up to a whole unit **before** multiplication so the result
    interprets as whole ordered units (DEC-038 rounding policy).

    Raises:
        ValueError: If any input is negative or the demand is not
            finite.
    """
    _validated_demand_inputs(
        average_daily_demand, lead_time_days, safety_stock
    )
    whole_demand_units = math.ceil(average_daily_demand)
    return (
        whole_demand_units
        * (lead_time_days + TARGET_STOCK_BUFFER_DAYS)
        + safety_stock
    )


def calculate_recommended_order_quantity(
    target_stock: int,
    current_stock: int,
) -> int:
    """Order quantity per DEC-033: how much to order to reach target.

    ``Recommended Order Quantity = max(0, Target Stock - Current
    Stock)``

    The clamp keeps a recommendation an actionable nonnegative number:
    when stock already meets or exceeds target, the recommendation is 0
    ("no need to order") rather than a negative surplus value.

    Raises:
        ValueError: If either input is not a nonnegative integer.
    """
    for name, value in (
        ("Target stock", target_stock),
        ("Current stock", current_stock),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(
                f"{name} must be a nonnegative integer, got {value!r}."
            )
    return max(0, target_stock - current_stock)


def classify_stock(current_stock: int, reorder_point: int) -> str:
    """Classify stock status per BR-008.

    - Out of Stock: current stock equals zero.
    - Low Stock: current stock is positive and at or below the reorder
      point.
    - In Stock: current stock is above the reorder point.

    Raises:
        ValueError: If the inputs are nonnegative integers only when
            they are not.
    """
    if isinstance(current_stock, bool) or not isinstance(
        current_stock, int
    ) or current_stock < 0:
        raise ValueError(
            f"Current stock must be a nonnegative integer, got "
            f"{current_stock!r}."
        )
    if isinstance(reorder_point, bool) or not isinstance(
        reorder_point, int
    ) or reorder_point < 0:
        raise ValueError(
            f"Reorder point must be a nonnegative integer, got "
            f"{reorder_point!r}."
        )
    if current_stock == 0:
        return STATUS_OUT_OF_STOCK
    if current_stock <= reorder_point:
        return STATUS_LOW_STOCK
    return STATUS_IN_STOCK


def _parse_date(value: str) -> dt.date:
    """Parse a ``YYYY-MM-DD`` string, raising ValueError otherwise."""
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Dates must be 'YYYY-MM-DD' strings, got {value!r}."
        ) from error
