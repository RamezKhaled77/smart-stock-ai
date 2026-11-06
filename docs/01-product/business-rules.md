# SmartStock AI — Business Rules

## 1. Purpose

This document defines the business rules and calculations used by SmartStock AI.

These rules describe how the application should interpret inventory data, process sales, identify stock risks, and generate restocking recommendations.

Business rules must remain separate from the user interface and machine learning implementation.

Rules marked as Proposed must be reviewed before being treated as final implementation requirements.

---

## 2. Rule Status

Each rule may have one of the following statuses:

- Proposed
- Accepted
- Needs Research
- Open Question
- Rejected

The project decision log is the authority for formally accepted decisions.

---

# 3. Product Rules

## BR-001: Product Identification

Each product must have a unique identifier.

The identifier should be used when connecting sales and inventory records to products.

**Status:** Proposed

## BR-002: Product Name

A product must have a non-empty display name.

**Status:** Proposed

## BR-003: Product Stock

A product's current stock represents the recorded quantity currently available in inventory.

**Decided policy (DEC-047):** Current stock is stored directly as a maintained product field. Recorded sales and approved manual stock adjustments update it; no sales or operation is applied without updating this value. There is no transaction history in v1.

**Status:** Accepted

## BR-004: Product Removal

**Decided policy (DEC-048):** Product removal uses soft delete. "Deleting" a product sets an `is_active` flag to 0 instead of removing the row. Historical sales information is preserved automatically, and the action is reversible. Inactive products are excluded from listings, counts, and recommendations unless explicitly requested (BR-026).

**Status:** Accepted

---

# 4. Inventory Rules

## BR-005: Non-Negative Stock

Inventory quantities should not become negative under normal application operations.

If a sale exceeds available stock, the application should follow the approved insufficient-stock policy.

**Status:** Proposed

## BR-006: Inventory Changes

Inventory may change because of:

- Recorded sales.
- Stock receipts.
- Damaged or lost items.
- Manual adjustments.
- Other explicitly supported inventory operations.

Each operation should have a clear meaning.

**Status:** Proposed

## BR-007: Inventory Consistency

The system must preserve consistency between recorded inventory quantities and supported inventory transactions.

The exact transaction-history design requires further approval.

**Status:** Proposed

## BR-008: Stock Status

A product may have one of the following statuses:

- In Stock.
- Low Stock.
- Out of Stock.

Suggested initial classification:

- Out of Stock: Current Stock equals zero.
- Low Stock: Current Stock is greater than zero and less than or equal to Reorder Point.
- In Stock: Current Stock is greater than Reorder Point.

This classification was applied as documented (TASK-016) and is **Accepted**; the reorder point follows DEC-032.

**Status:** Accepted

---

# 5. Sales Rules

## BR-009: Valid Sales Quantity

A recorded sales quantity must be a positive numeric value.

Zero and negative quantities must not be accepted as normal sales.

**Status:** Accepted — enforced in the sales service and repository (values must be positive integers; `2.5`, `0`, and negatives are rejected).

## BR-010: Sales Product Reference

Every sales record must reference a valid product.

Historical records for inactive products may still be retained.

**Status:** Accepted — new sales only target existing, active products; recording a sale for a deactivated product is rejected (DEC-050). Historical sales of deactivated products are preserved (DEC-048).

## BR-011: Sales Date

A sales record must contain a valid date.

Future sales dates should be rejected unless the application explicitly supports scheduled transactions.

**Status:** Accepted — dates must be valid `YYYY-MM-DD`; future dates are rejected because the application does not support scheduled transactions (DEC-051). Backdated entries are allowed.

## BR-012: Inventory Deduction

When a sale is recorded, inventory should be reduced by the sold quantity.

The operation must be handled consistently so that a failed sale does not leave inventory incorrectly updated.

**Status:** Accepted — implemented as one transaction in the sales service (TASK-015): stock validation, sale insert, and stock decrement commit together or roll back together.

## BR-013: Insufficient Stock

If the requested sales quantity exceeds current stock, the system must not silently create negative inventory.

**Decided policy (DEC-035):** Reject the sale when stock is insufficient. The sale is not recorded, inventory is left unchanged, and the user receives a clear validation message identifying the requested quantity and the available quantity.

If the user later explicitly requires backorder support, a new decision must supersede DEC-035.

**Status:** Accepted — implemented via `InsufficientStockError` in the sales service with the requested and available quantities in the message; delivered in one transaction (BR-012).

## BR-014: Historical Sales Import

Imported historical sales records may describe sales that occurred before the application started tracking inventory.

Historical imports must not automatically reduce current stock unless a specific stock-reconciliation operation is approved.

**Status:** Proposed

This rule prevents historical sales from accidentally changing today's inventory.

---

# 6. Demand and Forecasting Rules

## BR-015: Forecasting Target

The forecasting target should represent the quantity of a product sold or demanded during a defined future period.

The exact target definition must be documented in the ML strategy.

**Status:** Proposed

## BR-016: Sales and Demand Distinction

Observed sales must not automatically be treated as true customer demand when stock availability is unknown.

Stockout periods may cause observed sales to underestimate demand.

**Status:** Accepted as a project modeling principle.

## BR-017: Forecast Horizon

A forecast must clearly identify the future period it represents.

**Decided horizon (DEC-026):** The forecast horizon is user-selectable among 7, 14, or 30 future days, with 7 days as the default. The UI must display the forecast period clearly.

## BR-018: Invalid Predictions

Invalid predictions must not be used directly for inventory recommendations.

Examples include:

- Missing values.
- Infinite values.
- Unexpected output shapes.
- Negative predicted quantities where negative demand is not meaningful.

If a regression model produces a negative demand estimate, the application may apply an approved non-negative output policy.

The exact handling must be documented.

## BR-019: Forecast Availability

A product should only receive a model-based forecast when sufficient valid historical data is available.

The minimum data requirement must be established through experimentation.

**Status:** Proposed

---

# 7. Inventory Planning Rules

## BR-020: Reorder Point

The proposed reorder point formula is:

`Reorder Point = Average Daily Demand × Lead Time + Safety Stock`

Where:

- Average Daily Demand is the estimated average daily product demand.
- Lead Time is the expected number of days required to receive replenishment.
- Safety Stock is the additional inventory buffer.

**Status:** Proposed

## BR-021: Safety Stock

**Decided policy (DEC-036):** Safety stock is manually configured per product. It is an optional product field (nonnegative integer, default 0).

This keeps the value transparent and understandable, and works regardless of how much sales history a product has. A variability-based statistical calculation may be introduced later only if justified and explicitly re-decided.

## BR-022: Reorder Decision

A product should be considered for replenishment when its relevant inventory position reaches or falls below its reorder point.

`Current Stock <= Reorder Point`

Since the initial application does not support automatic purchasing or incoming-stock tracking (DEC-031), the inventory position equals the current stock in version 1. If incoming-stock support is approved later, this rule must be updated to account for it.

## BR-023: Recommended Order Quantity

A proposed simplified formula is:

`Recommended Order Quantity = max(0, Target Stock - Inventory Position)`

Where:

- Target Stock represents the desired inventory level after replenishment.
- Inventory Position represents the quantity available or expected to be available according to approved rules.

If incoming stock is not supported, the calculation may use current stock only.

**Status:** Proposed

## BR-024: Target Stock

**Decided formula (DEC-038):**

`Target Stock = Average Daily Demand × (Lead Time + 7 days) + Safety Stock`

where Average Daily Demand is the mean of the product's daily sales over the most recent 30 days of available history, rounded up to a whole unit in the business logic layer.

The (Lead Time + 7 days) factor covers expected demand during replenishment plus a 7-day buffer after restock. Using the historical average keeps restocking logic independent of the forecasting model (consistent with DEC-030). If the product lacks the minimum required history, the recommendation is unavailable with a clear explanation. Lead Time and Safety Stock follow DEC-037 and DEC-036.

## BR-025: Advisory Recommendations

Recommendations must be presented as suggestions.

The user must make the final replenishment decision.

The initial system must not automatically purchase or order products.

**Status:** Proposed

---

# 8. Dashboard Rules

## BR-026: Product Count

The total product count should follow the approved active-product policy.

Inactive or deleted products should not be included unless explicitly requested.

## BR-027: Low-Stock Count

The dashboard low-stock count should use the same stock-status calculation used by the inventory module.

## BR-028: Sales Metrics

Sales summaries must identify the selected date range and whether values represent quantities or monetary amounts.

## BR-029: Forecast Metrics

Forecast summaries must identify the forecast period and must not mix incompatible time ranges.

All dashboard rules are currently Proposed.

---

# 9. CSV Import Rules

## BR-030: Required Columns

The import process must define and validate the required columns before accepting a file.

The initial candidate schema is:

- Date.
- Product identifier or product reference.
- Sales quantity.

Exact column names and mappings must be documented in the data import specification.

## BR-031: Invalid Records

Invalid rows must be reported to the user.

The system must not silently transform invalid values into valid records.

## BR-032: Duplicate Records

The system should identify possible duplicate imports.

The duplicate detection key depends on the final sales data model.

## BR-033: Import Atomicity

The system should avoid leaving the database in an inconsistent state if an import fails.

The final policy for partially valid files must be approved before implementation.

---

# 10. Data and Metric Rules

## BR-034: Sales Quantity vs. Revenue

Sales quantity represents the number of units sold.

Revenue represents the monetary value of sales.

Revenue requires valid price information.

The application must not calculate or display revenue using assumed prices.

## BR-035: Missing Historical Dates

Missing dates in a time series must be handled according to an explicit data-preprocessing policy.

A missing date does not automatically mean zero demand.

The meaning of missing dates must be investigated.

## BR-036: Negative Sales

Negative sales values should not be accepted as ordinary sales quantities.

Returns and corrections require an explicit policy.

---

# 11. Separation of Responsibilities

The system must maintain the following separation.

## Forecasting Layer

Responsible for:

- Preparing model features.
- Loading forecasting models.
- Generating predictions.
- Returning forecast results.

It must not directly modify inventory quantities.

## Inventory Layer

Responsible for:

- Reading current stock.
- Updating inventory.
- Validating stock adjustments.
- Maintaining inventory consistency.

## Recommendation Layer

Responsible for:

- Reading forecast results.
- Reading inventory information.
- Applying approved inventory formulas.
- Generating recommendation outputs.

## UI Layer

Responsible for:

- Collecting user input.
- Displaying information.
- Triggering application operations.
- Showing validation and error messages.

The UI must not contain duplicated business calculations.

---

# 12. Open Questions

Most decisions have been resolved (see `../07-project-management/decisions.md`). Resolved answers:

1. Reject sales when stock is insufficient — **Yes (DEC-035)**.
2. Store inventory adjustments as a transaction history — **No (DEC-047)**: direct stock column, no history in v1.
3. Product deletion via soft deletion — **Yes (DEC-048)**.
4. Incoming stock — **No in v1 (DEC-031)**; inventory position equals current stock (BR-022).
5. Safety stock — manually configured per product, default 0 (DEC-036).
6. Target stock — `Avg Daily Demand × (Lead Time + 7) + Safety Stock` (DEC-038).
7. Default forecast horizon — 7 days, user-selectable (DEC-026).
10. Product returns — not handled in v1 (DEC-049).

Still open (needed during import/analysis implementation):

8. How will historical sales imports interact with existing records? (Related: Database Schema §12)
9. How will duplicate imports be detected? (Related: Database Schema §12)
11. How will days with zero sales be represented? (Related: data preprocessing — observed policy recorded in `../03-data/data-preprocessing.md` §19)
12. How will stockout periods be identified in historical data? (Related: ML evaluation phases)

---

# 13. Related Documentation

- `features.md`
- `user-flows.md`
- `acceptance-criteria.md`
- `../03-data/data-preprocessing.md`
- `../04-machine-learning/forecasting-strategy.md`
- `../02-architecture/database-schema.md`
- `../05-interface/pages-specification.md`