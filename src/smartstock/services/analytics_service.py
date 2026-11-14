"""Application service for the Sales Analytics page (TASK-041).

Computes quantity-based sales analytics over a user-selected date
range (F-006 v1: quantities only — monetary analytics need reliable
price information, which the application does not store). Uses only
existing sales services; this layer is read-only composition.

Patterns returned are calendar-based per DEC-059's calendar-day view:
weekday averages include zero-sale days inside the selected range.
"""

import datetime as dt
from pathlib import Path

from smartstock.i18n import t
from smartstock.services import sales_service

WEEKDAY_NAMES = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday",
)

# F-011 trend direction: compare the average daily units of the two
# calendar halves of the selected range. A change within ±15% counts
# as steady — anything smaller is noise for a small business's daily
# quantities.
RISING_THRESHOLD = 1.15
FALLING_THRESHOLD = 0.85


def get_sales_analytics(
    start_date: str,
    end_date: str,
    product_id: int | None = None,
    db_path: Path | None = None,
) -> dict:
    """One analytics snapshot for an inclusive date range.

    Args:
        start_date: Inclusive lower bound (``YYYY-MM-DD``).
        end_date: Inclusive upper bound (``YYYY-MM-DD``).
        product_id: Optional product filter.
        db_path: Database to use; defaults to the configured path.

    Returns:
        Dictionary with:

        - ``totals``: ``units_sold``, ``sale_count``,
          ``days_in_range``, ``days_with_sales``, ``avg_units_per_day``
          (over all days in the range, zeros included).
        - ``daily``: ``{date: units}`` per-day totals.
        - ``weekday_pattern``: average units per weekday (zeros
          included; listed Monday → Sunday).
        - ``monthly``: ``{YYYY-MM: units}`` month totals.
        - ``per_product``: per-product rows (units, sale count, share
          of range units), best seller first — every product in the
          range, or only the filtered one.

    Raises:
        ValueError: If the dates are invalid or the range is inverted.
        DatabaseError: If a read fails.
    """
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        _validate_iso(label, value)
    if start_date > end_date:
        raise ValueError(
            t(
                "svc.analytics.range_inverted",
                start=start_date,
                end=end_date,
            )
        )

    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    days_in_range = (end - start).days + 1

    if product_id is not None:
        daily = sales_service.get_daily_sales(
            product_id, start_date, end_date, db_path=db_path
        )
        summary = [
            row for row in sales_service.get_product_sales_summary(
                start_date, end_date, db_path=db_path
            )
            if row["product_id"] == product_id
        ]
    else:
        daily = sales_service.get_daily_totals(
            start_date, end_date, db_path=db_path
        )
        summary = sales_service.get_product_sales_summary(
            start_date, end_date, db_path=db_path
        )

    units_sold = sum(daily.values())
    sale_count = sum(row["sale_count"] for row in summary)

    weekday_pattern = _weekday_pattern(daily, start, end)
    monthly: dict[str, int] = {}
    for day, units in daily.items():
        monthly[day[:7]] = monthly.get(day[:7], 0) + units

    per_product = []
    for row in summary:
        share = row["units_sold"] / units_sold if units_sold else 0.0
        per_product.append({**row, "share_of_units": round(share, 4)})

    return {
        "totals": {
            "units_sold": units_sold,
            "sale_count": sale_count,
            "days_in_range": days_in_range,
            "days_with_sales": len(daily),
            "avg_units_per_day": round(units_sold / days_in_range, 3),
        },
        "daily": daily,
        "weekday_pattern": weekday_pattern,
        "monthly": monthly,
        "per_product": per_product,
    }


def _validate_iso(label: str, value: str) -> None:
    """Require a ``YYYY-MM-DD`` string that parses as a date."""
    try:
        dt.date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            t("svc.analytics.date_invalid", label=label, value=value)
        ) from error


def get_product_performance(
    start_date: str,
    end_date: str,
    product_id: int | None = None,
    db_path: Path | None = None,
) -> list:
    """Per-product performance rows for a range (F-011, TASK-043).

    Args:
        start_date: Inclusive lower bound (``YYYY-MM-DD``).
        end_date: Inclusive upper bound (``YYYY-MM-DD``).
        product_id: Optional filter to one product.
        db_path: Database to use; defaults to the configured path.

    Returns:
        List of dicts (best seller first): ``product_id``, ``name``,
        ``sku``, ``units_sold``, ``sale_count``, ``avg_units_per_day``
        (calendar days of the range, zeros included), ``first_sale``,
        ``last_sale`` (dates with sales in the range), and ``trend``
        (direction label comparing the two calendar halves — see
        ``_trend_direction``). Only products that sold in the range
        appear; stock-warning frequency is not tracked in v1.

    Raises:
        ValueError: If the dates are invalid or the range is inverted.
        DatabaseError: If a read fails.
    """
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        _validate_iso(label, value)
    if start_date > end_date:
        raise ValueError(
            t(
                "svc.analytics.range_inverted",
                start=start_date,
                end=end_date,
            )
        )

    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    days_in_range = (end - start).days + 1

    summary = sales_service.get_product_sales_summary(
        start_date, end_date, db_path=db_path
    )
    daily_by_product = sales_service.get_daily_sales_by_product(
        start_date, end_date, db_path=db_path
    )

    rows = []
    for entry in summary:
        if product_id is not None and entry["product_id"] != product_id:
            continue
        daily = daily_by_product.get(entry["product_id"], {})
        sale_days = sorted(daily)
        rows.append(
            {
                **entry,
                "avg_units_per_day": round(
                    entry["units_sold"] / days_in_range, 3
                ),
                "first_sale": sale_days[0] if sale_days else None,
                "last_sale": sale_days[-1] if sale_days else None,
                "trend": _trend_direction(daily, start, days_in_range),
            }
        )
    return rows


def _trend_direction(
    daily: dict[str, int], start: dt.date, days_in_range: int
) -> str:
    """Demand direction over the range, halves compared.

    The range is split into two calendar halves (an odd extra day
    joins the second half). Zeros count — a quiet first half with
    sales only in the second half reads as rising demand, mirroring
    the DEC-059 "no sale = zero demand" calendar view.

    Returns ``"Rising"``, ``"Falling"``, ``"Steady"``, or
    ``"No sales in range"``. A single-day range cannot be split, so
    it reports ``"Steady"`` (nothing to compare).
    """
    if days_in_range < 2:
        return t("svc.analytics.trend_steady")
    first_days = days_in_range // 2
    first_end = start + dt.timedelta(days=first_days)  # exclusive bound
    first_units = second_units = 0
    for day, units in daily.items():
        day_date = dt.date.fromisoformat(day)
        if day_date < first_end:
            first_units += units
        else:
            second_units += units

    first_avg = first_units / first_days if first_days else 0.0
    second_days = days_in_range - first_days
    second_avg = second_units / second_days if second_days else 0.0

    if first_avg == 0.0 and second_avg == 0.0:
        return t("svc.analytics.trend_no_sales")
    if first_avg == 0.0:
        return t("svc.analytics.trend_rising_new")
    if second_avg == 0.0:
        return t("svc.analytics.trend_falling_stopped")
    ratio = second_avg / first_avg
    if ratio >= RISING_THRESHOLD:
        return t("svc.analytics.trend_rising")
    if ratio <= FALLING_THRESHOLD:
        return t("svc.analytics.trend_falling")
    return t("svc.analytics.trend_steady")


def _weekday_pattern(
    daily: dict[str, int], start: dt.date, end: dt.date
) -> list:
    """Average units per weekday over the full range, zeros included.

    Returns 7 floats (Monday → Sunday). Every day in the range
    contributes — zero-sale days belong to the pattern, mirroring the
    DEC-059 demand view of "no sale = zero demand".
    """
    sums = [0] * 7
    counts = [0] * 7
    current = start
    while current <= end:
        weekday = current.weekday()
        sums[weekday] += daily.get(current.isoformat(), 0)
        counts[weekday] += 1
        current += dt.timedelta(days=1)
    return [
        round(total / counts[index], 3) if counts[index] else 0.0
        for index, total in enumerate(sums)
    ]
