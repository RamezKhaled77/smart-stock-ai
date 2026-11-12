# Manual Application Test Plan (TASK-047)

Manual verification of the main user flows through the real Streamlit
interface. The automated suite (430 tests, TASK-046) already proves the
logic; this plan covers what only a human can confirm — layout, wording,
interaction feel, and end-to-end click-through.

## Status

- **2026-11-11 — machine part done:** the real `app.py` was launched with
  `streamlit run app.py` and every registered route answered HTTP 200
  with a clean boot (`/`, `dashboard`, `products-and-inventory`,
  `restocking-recommendations`, `sales-management`, `sales-analytics`,
  `demand-forecast`, `data-import`).
- **Human pass: pending** — the checklist below is ready to walk through.

## How to run

```bash
.venv/bin/python -m streamlit run app.py
```

Then walk the checklist and tick items. Report any failure as an issue
in `docs/07-project-management/progress.md`.

## Checklist

### 1. Startup & navigation

- [ ] App opens on the Dashboard without errors.
- [ ] Sidebar shows five groups: Overview (Dashboard), Inventory
      (Products & Inventory, Restocking Recommendations), Sales
      (Sales Management, Sales Analytics), Forecasting (Demand
      Forecast), Data (Data Import).
- [ ] Switching between all seven pages never shows an exception box.

### 2. Products & Inventory

- [ ] Add product: required-field validation messages appear inline
      (empty name, empty SKU).
- [ ] Add product with opening stock → appears in the listing with the
      correct stock status.
- [ ] Edit product: change lead time / safety stock / linked dataset
      item → saved, flash message shown.
- [ ] Duplicate SKU rejected with a clear message.
- [ ] Stock tab: add units → stock increases; remove too many →
      negative-stock rejection message (DEC-034).
- [ ] Set exact stock → stock overwritten (correction).
- [ ] Deactivate product (with confirmation tick) → disappears from
      listings; reactivate → returns.

### 3. Sales Management

- [ ] Record sale: positive quantity, today's date → stock decreases,
      success flash, sale appears in history.
- [ ] Sale exceeding stock → rejected atomically (stock unchanged).
- [ ] Future date rejected; backdated date accepted (DEC-050/051).
- [ ] Inactive product not selectable for new sales but still visible
      in history (DEC-048).

### 4. Dashboard

- [ ] Metrics show real data after the steps above (products, stock,
      needing reorder, last-7-days units/sales, top seller).
- [ ] Sales trend chart renders; 7/30-day selector changes the chart.
- [ ] Low-stock overview lists breaching products only.
- [ ] Forecast-readiness line shows the linked-product count.

### 5. Sales Analytics

- [ ] Default range (last 30 days) shows zeros for old data; setting
      the range over recorded sales fills metrics/tables.
- [ ] Product filter narrows everything to that product.
- [ ] Daily trend chart, weekday pattern chart render.
- [ ] Product performance table shows units, avg/day, first/last sale,
      trend labels.
- [ ] The three "Export … (CSV)" buttons download files matching the
      displayed tables (DEC-063).

### 6. Restocking Recommendations

- [ ] Advice matches the Dashboard's "needing reorder" count.
- [ ] Per-product explanations cite the formula inputs (demand, lead
      time, safety stock, DEC-033 order quantity).
- [ ] Products without enough history show "not available yet" with a
      reason, never crash.
- [ ] "Export recommendations (CSV)" downloads a file matching the
      displayed advice (DEC-063).

### 7. Data Import

- [ ] Upload a CSV with the required columns → preview appears, nothing
      stored until confirm.
- [ ] Re-uploading the same file → SHA-256 duplicate rejection
      (DEC-053).
- [ ] Malformed file → clear structure error, nothing stored
      (DEC-054 all-or-nothing).

### 8. Demand Forecast

- [ ] Unlinked product → guidance info (DEC-060).
- [ ] Linked product with ≥ 31 imported days → Random Forest forecast
      with method caption.
- [ ] Linked product with < 31 days → MA-7 fallback caption (DEC-058).
- [ ] Linked product with no imported history → "No suitable history
      exists" info, no crash.
- [ ] Horizons 7/14/30 change the table length.
- [ ] "How accurate is the model?" section shows the measured
      validation/test MAE and baseline context (DEC-062).

## Discovered issues

(None yet — record findings here during the human pass.)
