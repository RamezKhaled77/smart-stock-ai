# Baseline Evaluation (TASK-027)

## 1. Purpose

This document records the measured validation results of the approved
baseline forecasting candidates. Per DEC-027, any supervised model
(TASK-030+) must **beat both baselines below** on the same validation
window to be eligible for selection.

All numbers are produced by `src/smartstock/ml/baselines.py` and pinned
by `tests/test_ml_baselines.py::TestRealValidationWindow`, so the report
stays reproducible.

---

## 2. Setup (DEC-056)

- Data: store-1 series (50 items × 1,826 days, `data/raw/train.csv`
  preprocessed via `smartstock.ml.preprocessing`).
- Training history: 2013-01-01 → 2015-12-31.
- Validation window: **2016-01-01 → 2016-12-31** (full year, all items).
- Test window: 2017 (not touched in this task).
- Evaluation: **walk-forward, one-step-ahead** — for every (item, day)
  the prediction uses only actuals from before that day; validation
  actuals become history only after their own prediction. No future
  information enters any prediction (forecasting-strategy §10).

---

## 3. Results (Validation 2016)

| Baseline | MAE | RMSE | Predictions |
|---|---|---|---|
| Naive Forecast (repeat latest) | 10.270 | 13.761 | 18,300 |
| Historical Average, trailing 7 days | **8.077** | **10.556** | 18,300 |
| Historical Average, trailing 30 days | 8.298 | 10.915 | 18,300 |

### Finding 1 — the Historical Average window is 7 days

The §3.2 window question ("7 or 30 days") was answered by
measurement: the trailing **7-day** mean beats the 30-day mean on both
MAE (8.077 vs. 8.298) and RMSE (10.556 vs. 10.915). This matches the
exploration finding that lag-7 is the dominant correlation (0.908) and
that a level-shifts-trend exists — longer windows adapt more slowly.

### Finding 2 — naive is a weak but honest floor

Repeating the latest observation loses badly to weekly averaging on
this dataset (10.270 vs. 8.077 MAE): demand here is weekday-driven, not
random-walk. Both numbers are the **beatable floor** for candidate
models.

---

## 4. Interpretation Notes

- The walk-forward uses each validation day's *actual* as history for
  the next day, which is the standard honest one-step-ahead protocol
  (decision-time information). It is **not** a 30-day recursive-horizon
  test: multi-step error accumulation (DEC-025) is evaluated separately
  when the inference path is implemented (TASK-033).
- Errors are pooled over item-days (18,300 = 50 items × 366 days).
- These baselines use no calendar features; supervised candidates
  (linear regression, random forest per §3.3/3.4) carry the weekday
  and trend signals in feature form (feature-engineering doc).

---

## 5. Related Documentation

- `data-exploration.md` — evidence behind the lag-7 finding
- `forecasting-strategy.md` — DEC-025..028, DEC-027 selection rules
- `../07-project-management/decisions.md` — DEC-056 split authority
