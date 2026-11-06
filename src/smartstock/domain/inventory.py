"""Core inventory business rules.

Contains stock-level calculations that are independent of Streamlit and
of the database implementation: callers pass in plain numbers.

Decision references:
- DEC-032: ``Reorder Point = Average Daily Demand * Lead Time + Safety
  Stock`` (inputs defined by DEC-037/DEC-036 and DEC-038 for demand).
- DEC-038: Average Daily Demand uses the most recent 30-day window.
- BR-008: stock status classes are Out of Stock, Low Stock, In Stock.
"""

import datetime as dt
import math

from smartstock.utils.dates import utc_today_iso

# Demand window used by the reorder point (DEC-038).
DEMAND_WINDOW_DAYS = 30

# Stock status classes (BR-008).
STATUS_IN_STOCK = "In Stock"
STATUS_LOW_STOCK = "Low Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"


def calculate_average_daily_demand(
    daily_totals: dict[str, int],
    window_days: int = DEMAND_WINDOW_DAYS,
    today: str | None = None,
) -> float:
    """Average demand per day over the most recent calendar window.

    The window covers ``window_days`` calendar days ending on ``today``
    (inclusive). Days without sales count as zero demand, so a product
    that sells only once in a month has a low average — which is the
    correct signal for restocking decisions.

    Args:
        daily_totals: Sold quantity per ``YYYY-MM-DD`` day (from the
            sales service/aggregate queries). Days outside the window
            are ignored.
        window_days: Length of the demand window (default 30, DEC-038).
        today: Last day of the window as ``YYYY-MM-DD``. Defaults to
            the current UTC date.

    Returns:
        The average daily demand as a nonnegative float. With no sales
        at all in the window the result is 0.0.
    """
    if window_days <= 0:
        raise ValueError(
            f"window_days must be positive, got {window_days!r}."
        )
    end_date = _parse_date(today) if today is not None else (
        _parse_date(utc_today_iso())
    )
    total_quantity = 0
    for offset in range(window_days):
        day = end_date - dt.timedelta(days=offset)
        total_quantity += int(daily_totals.get(day.isoformat(), 0))
    return total_quantity / window_days


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
    reorder_point = (
        average_daily_demand * lead_time_days + safety_stock
    )
    return math.ceil(reorder_point)


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
