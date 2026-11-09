# Data Exploration — Store 1 Historical Sales (TASK-026)

## 1. Purpose

This document records the measured findings from exploring the
historical sales data used by the forecasting phase. All numbers are
produced by `src/smartstock/ml/exploration.py` (store 1 per DEC-015,
2013-01-01 → 2017-12-31) and pinned by `tests/test_ml_exploration.py`,
so the report stays reproducible: if the numbers drift from reality,
tests fail.

---

## 2. Time Coverage and Completeness

| Fact | Measured Value |
|---|---|
| Records (store 1, all items) | 91,300 |
| Date range | 2013-01-01 → 2017-12-31 |
| Days covered | 1,826 (incl. leap day 2016-02-29) |
| Items with full daily coverage | 50 of 50 — every item has 1,826 observations |
| Zero-sales records in store 1 | 0 |

Note: the dataset-wide inspection (TASK-005) found exactly one
zero-sales record in the full 913,000-row dataset; it belongs to a
different store. **Store 1 series are complete and strictly positive** —
no missing-data or zero-demand handling is needed for model training.

---

## 3. Sales Distribution (Daily Quantity, Store 1, Pooled)

| Statistic | Value |
|---|---|
| Mean | 47.27 units/day/item |
| Std dev | 24.01 |
| Min / Max | 1 / 155 |
| p25 / p50 / p75 | 28 / 44 / 63 |
| p95 / p99 | 92 / 111 |

The distribution is unimodal and roughly bell-shaped around a median
of 44, with a long right tail (max 155 ≈ 3.3× the mean). Practical
implication: MAE is the selected primary metric (DEC-027), so rare
extreme days influence evaluation far less than they would under RMSE.

---

## 4. Weekly (Weekday) Pattern

Mean daily sales by weekday:

| Day | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| Mean | 37.47 | 43.56 | 43.84 | 46.73 | 49.84 | 53.13 | 56.27 |

Demand builds steadily through the week: **Sundays sell ~50% more than
Mondays** (56.27 vs. 37.47, factor ≈ 1.50). Even simple weekday-aware
models have a strong, learnable signal.

---

## 5. Monthly (Within-Year) Pattern

Mean daily sales by month:

| Month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean | 32.17 | 35.53 | 42.74 | 49.90 | 53.50 | 56.92 | **60.66** | 53.48 | 49.88 | 46.37 | 49.91 | 35.66 |

Demand peaks in **July** (60.66) and bottoms in **January** (32.17) —
a spread of ~89% peak-over-trough. December (35.66) joins January as a
trough, contradicting a typical holiday-sales assumption: this source
data must be trusted over retail intuition.

---

## 6. Year-Over-Year Trend

| Year | Total | Daily Mean | Records |
|---|---|---|---|
| 2013 | 717,840 | 39.33 | 18,250 |
| 2014 | 826,786 | 45.30 | 18,250 |
| 2015 | 861,710 | 47.22 | 18,250 |
| 2016 | 937,493 | 51.23 | 18,300 (leap year) |
| 2017 | 971,774 | 53.25 | 18,250 |

Demand **grows every year** (2013 → 2017 daily mean +35%). The trend
is steady rather than explosive (+15.2%, +4.2%, +8.5%, +3.9%
year-over-year in daily means). Implication: models without a trend/level-adaptive
component (e.g., a plain historical mean over all five years) will
systematically under-forecast the present. Rolling windows and recent
lags adapt naturally.

---

## 7. Persistence (Lag Correlations)

Pearson correlation between sales and lagged sales, shifted within
each item's own series:

| Lag | Correlation |
|---|---|
| lag_1 (yesterday) | 0.852 |
| **lag_7 (same weekday last week)** | **0.908** |
| lag_30 (30 days ago) | 0.793 |

**Lag-7 is the strongest single predictor** — weekly seasonality
dominates day-level structure. This directly supports the proposed
feature set (`day_of_week`, `lag_7`, `rolling_mean_7`) and predicts
that a simple "same weekday last week" baseline will be strong.

---

## 8. Item-Level Variation

- Weakest items by mean daily demand: item 5 (16.6), item 47 (19.8), item 4 (20.0).
- Strongest items: item 15 (79.7), item 28 (79.6), item 18 (76.3).
- The mean demand ratio between strongest and weakest items is ~4.8×,
  so pooled-only evaluation can hide per-item weaknesses; per-item
  error reporting deserves attention at model evaluation time.

---

## 9. Data Limitations

1. **No zero-demand days in store 1.** Real operations include
   stockouts and dead days; the model sees an artificially "always
   selling" world. Forecasts for genuinely empty demand days may be
   optimistic. (Related open question 12: stockout identification —
   not decidable from this dataset.)
2. **No covariates.** No price, promotion, stockout, or holiday
   columns exist, so the model explains demand only from date/lag
   structure. Promo-driven spikes cannot be attributed.
3. **Synthetic-looking regularity.** The dataset (a Kaggle competition
   source) is smooth and regular; real operational data with gaps,
   stockouts, and imports will behave worse. baselines/models must be
   re-validated on operational `sales` data once those accumulate.
4. **One store only (DEC-015).** Findings do not transfer to other
   stores in the source file.
5. **Five years may hide regime changes** (e.g., 2020s-style
   disruption is absent from 2013–2017 records).

---

## 10. Implications for the Forecasting Phase

- Features `day_of_week`, `lag_7`, and `rolling_mean_7` are expected
  to carry most of the signal (§4, §7).
- A **trend-aware baseline** (e.g., trailing 30-day mean) is required;
  a full five-year mean would under-forecast (§6).
- Chronological splitting must keep the validation/test windows in the
  later years (the split-dates decision for TASK-029/030 will use this
  evidence, with per-item error reporting per §8).
- Recursion error accumulation (DEC-025) will compound faster across
  the July/January seasonal swings than in the flat periods.

## 11. Reproducing These Numbers

```python
from pathlib import Path
from smartstock.ml import exploration, preprocessing

frame, _ = preprocessing.preprocess_dataset(Path("data/raw/train.csv"), store_id=1)
report = exploration.summarize_series(frame)
```

`tests/test_ml_exploration.py::TestRealDataset` asserts the numbers in
this document directly from the code.

---

## 12. Related Documentation

- `data-preprocessing.md` — workflow that produces the explored frame
- `forecasting-strategy.md` — candidate models and DEC-025..027,028
- `../07-project-management/decisions.md` — decision authority
