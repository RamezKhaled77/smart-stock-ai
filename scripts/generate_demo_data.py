"""Generate a realistic demo sales-history file for the app (v1.1).

Creates ``data/samples/demo_sales_history.csv`` — a seeded, plausible
sales history in the exact historical-import format
(``date,store,item,sales``, DEC-052). It is dummy data shaped to feel
real: weekday rhythms, a seasonal item, a growing item, and one new
item with only a few weeks of history, so every forecast path of the
app (DEC-058) can be exercised with believable numbers.

The output is safe to commit: no real data, ~1,600 rows, and item
numbers 10-14, chosen so the file can never collide with the small
manual-test samples (items 1, 2, 3, 7) through the UNIQUE
``(item, sale_date)`` rule (DEC-053).

Run from the repository root:

    .venv/bin/python scripts/generate_demo_data.py

The random seed is fixed, so regenerating the file always produces
byte-identical data.
"""

import csv
import datetime as dt
import random
from pathlib import Path

# Output location (relative to the repository root).
OUTPUT_PATH = Path("data/samples/demo_sales_history.csv")

# Fixed seed: regenerating reproduces the same file exactly.
SEED = 2026

# The file ends yesterday and runs END_DAYS days back, so the app sees
# a continuous history and today stays free for real sales.
END_DATE = dt.date(2026, 11, 13)
END_DAYS = 400

# The new item gets only this many days of history so the Demand
# Forecast page demonstrates the trailing 7-day average fallback
# (DEC-058: fewer than 31 observed days → MA-7).
NEW_ITEM_DAYS = 21


def weekend_factor(date: dt.date, strength: float) -> float:
    """Friday/Saturday are busier; Monday is the quietest day."""
    if date.weekday() in (4, 5):  # Friday, Saturday
        return strength
    if date.weekday() == 0:  # Monday
        return 0.7
    return 1.0


def seasonal_summer_factor(date: dt.date, peak: float) -> float:
    """Smooth June-August peak, deep December-February trough."""
    month = date.month
    if month in (6, 7, 8):
        return peak
    if month in (12, 1, 2):
        return 1.0 - (peak - 1.0) * 0.8  # a low, but not zero, season
    return 1.0


def growth_factor(date: dt.date, start: dt.date, end: dt.date,
                  first: float, last: float) -> float:
    """Linear ramp from ``first`` at the start to ``last`` at the end."""
    span = (end - start).days
    progress = (date - start).days / span if span else 0.0
    return first + (last - first) * progress


def noisy_sales(mean: float, rng: random.Random) -> int:
    """One day's sales: bell-shaped noise around the mean, never negative."""
    noise = rng.gauss(0.0, max(0.8, mean * 0.3))
    return max(0, int(round(mean + noise)))


def item_days(item: int, start: dt.date, end: dt.date) -> list[dt.date]:
    """The calendar days one item sold for (item 14 is the newcomer)."""
    if item == 14:
        return [end - dt.timedelta(days=offset)
                for offset in range(NEW_ITEM_DAYS - 1, -1, -1)]
    return [start + dt.timedelta(days=offset)
            for offset in range((end - start).days + 1)]


def day_demand(item: int, day: dt.date, start: dt.date, end: dt.date,
               rng: random.Random) -> int:
    """One item's expected sales on one day, with noise."""
    if item == 10:  # Morning coffee beans: steady, weekend bump.
        mean = 8.0 * weekend_factor(day, 1.5)
    elif item == 11:  # Fresh bread: high volume, strong weekly rhythm.
        mean = 15.0 * weekend_factor(day, 1.8)
    elif item == 12:  # Iced tea: hot-weather favorite.
        mean = 6.0 * seasonal_summer_factor(day, 2.2)
    elif item == 13:  # Protein bars: a product that catches on.
        mean = 6.0 * growth_factor(day, start, end, 0.5, 1.7)
    else:  # item == 14: new snack, settling in.
        mean = 4.0 * weekend_factor(day, 1.4)
    return noisy_sales(mean, rng)


def main() -> None:
    start = END_DATE - dt.timedelta(days=END_DAYS - 1)
    rng = random.Random(SEED)

    rows = []
    for item in (10, 11, 12, 13, 14):
        for day in item_days(item, start, END_DATE):
            rows.append(
                (day.isoformat(), 1, item, day_demand(
                    item, day, start, END_DATE, rng))
            )
    # Calendar order inside each item, items in ascending order — the
    # layout a real export would have, and easy to eyeball.
    rows.sort(key=lambda row: (row[2], row[0]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "store", "item", "sales"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    print(f"Date range: {start.isoformat()} → {END_DATE.isoformat()}")
    print(f"Items: 10-13 full history, 14 short history "
          f"({NEW_ITEM_DAYS} days)")


if __name__ == "__main__":
    main()
