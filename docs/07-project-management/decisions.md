# Project Decisions

## 1. Purpose

This document records important project decisions and their current status.

It helps maintain consistency across:

- Product requirements.
- Architecture.
- Data processing.
- Machine learning.
- Business logic.
- User interface.
- Development workflow.

The AI Agent must consult this document before making changes that affect established project decisions.

---

## 2. Decision Statuses

| Status | Meaning |
|---|---|
| Accepted | Explicitly agreed upon and should be followed. |
| Proposed | Suggested but not necessarily approved. |
| Open | Requires clarification or a decision. |
| Rejected | Considered and intentionally not selected. |
| Superseded | Replaced by a newer decision. |

A proposed decision must not be treated as accepted.

---

## 3. Project Direction

### DEC-001: Project Identity

- Status: Accepted
- Decision: The project name is SmartStock AI.
- Context: The project is an AI and Python college project focused on inventory management and demand forecasting.

### DEC-002: Main Project Concept

- Status: Accepted
- Decision: Build a small-store inventory management application that uses historical sales data to forecast demand and provide restocking recommendations.
- Context: The project should demonstrate both practical application development and the use of AI/ML libraries in Python.

### DEC-003: Development Approach

- Status: Accepted
- Decision: The user is implementing the project individually.
- Context: The original team-based plan changed to an individual implementation.

### DEC-004: Project Scope Philosophy

- Status: Accepted
- Decision: Prioritize a functional, understandable core application over unnecessary advanced features.
- Context: The project must remain achievable within the available time and hardware constraints.

---

## 4. Technology Decisions

### DEC-005: Main Programming Language

- Status: Accepted
- Decision: Python is the main implementation language.
- Context: The project belongs to an AI and Python course.

### DEC-006: User Interface Framework

- Status: Proposed
- Decision: Use Streamlit for the initial web interface.
- Context: Streamlit reduces frontend development effort and allows the project to focus on Python, data processing, and ML.
- Confirmation Required: Verify against the final technology stack.

### DEC-007: Data Processing Libraries

- Status: Proposed
- Decision: Use Pandas and NumPy for data processing.
- Context: They provide suitable tools for tabular data and numerical operations.

### DEC-008: Machine Learning Library

- Status: Proposed
- Decision: Use Scikit-learn for the initial forecasting implementation.
- Context: It provides CPU-friendly regression models and evaluation utilities.

### DEC-009: Database

- Status: Proposed
- Decision: Use SQLite for operational application data.
- Context: SQLite is lightweight and does not require a separate database server.

### DEC-010: Visualization

- Status: Proposed
- Decision: Use Plotly for interactive charts where appropriate.
- Context: The application needs sales and forecasting visualizations.

### DEC-011: Model Persistence

- Status: Proposed
- Decision: Use Joblib to save and load trained model artifacts.
- Context: Normal application usage should not require retraining the model.

### DEC-012: Testing Framework

- Status: Proposed
- Decision: Use pytest for automated tests.
- Context: Business logic, data processing, and ML components should be tested independently.

---

## 5. Data Decisions

### DEC-013: Historical Dataset

- Status: Proposed
- Decision: Use the Kaggle Store Item Demand Forecasting Competition dataset as the initial historical sales dataset.
- Source: https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data
- Context: It contains historical daily sales for multiple stores and products.
- Confirmation Required: Inspect the actual downloaded files and verify suitability.

### DEC-014: Operational Data Separation

- Status: Accepted
- Decision: Historical training data and operational application data have separate responsibilities.
- Context:
  - Historical sales data supports demand forecasting.
  - SQLite stores operational application data.
  - The full historical dataset does not automatically need to be stored in SQLite.

### DEC-015: Dataset-to-Product Mapping

- Status: Accepted
- Decision: Map dataset entities to application products by selecting exactly one store from the Kaggle dataset (store 1 by default) and treating each `item` value as one application product.
- Context:
  - The initial application follows a single-store workflow (DEC-041).
  - Selecting one store provides approximately 45,600 daily records (1 store × 50 items × 5 years), which is sufficient for forecasting experiments and CPU-friendly.
  - The `item` → product mapping must be documented in the data preparation documentation.
- Important: This does not introduce multi-branch support. The `store` column is used only to filter the dataset during preprocessing, not kept as an operational concept.
- Decided: 2026-11-04.

### DEC-016: Historical Import and Current Stock

- Status: Accepted
- Decision: Historical sales imports must not automatically reduce current stock.
- Context: Historical sales records describe past demand, not necessarily the current inventory position.
- Exception: A separate stock-reconciliation workflow may be introduced if explicitly approved.

### DEC-052: Historical Import Storage

- Status: Accepted
- Decision: Imported historical sales are stored in a dedicated `historical_sales` table in the operational SQLite database, keyed by the dataset's `item` number — not by `product_id`. No products are created implicitly by an import. A separate `import_batches` table stores one metadata row per import run (source filename, SHA-256 fingerprint, row counts). The operational `sales` table continues to receive only application-recorded sales.
- Context: Closes business rules §12 open questions 8–9 and Database Schema §14 "historical import storage". DEC-015 maps each `item` value to one product conceptually, but operational products are created by users; forcing dataset items into the product catalog (and its `CHECK quantity > 0`/stock semantics) would either require implicit product creation — forbidden by the CSV Import Specification §4 — or mix source semantics into operational data. A separate table preserves the dataset's meaning (including the single zero-sales observation) and keeps the operational `sales` → `products` FK domain clean. 91,300 store-1 rows are well within SQLite's comfort zone.
- Method: Chosen with the project owner from documented options (2026-11-07, CSV import phase).

### DEC-053: Duplicate Import Handling

- Status: Accepted
- Decision: Every import records a SHA-256 fingerprint of the uploaded file in `import_batches`. Re-uploading a file whose fingerprint is already recorded is rejected outright with a clear message. As the hard database-level guarantee, `historical_sales` carries a unique constraint on (`item`, `sale_date`); overlapping-but-not-identical files are imported with already-present rows skipped and counted, never silently re-imported.
- Context: Closes business rules §12 open question 9 and Database Schema §14 "duplicate CSV import handling". The fingerprint gives a friendly, cheap exact-match rejection (CSV Import Specification §12 lists "file fingerprint" and "store import metadata" among candidate approaches; a filename comparison alone was explicitly deemed insufficient, hence content hashing). The row-level unique constraint covers the case a fingerprint cannot — two different files sharing rows.
- Method: Chosen with the project owner from documented options (2026-11-07, CSV import phase).

### DEC-054: Import Atomicity

- Status: Accepted
- Decision: Imports are all-or-nothing. The complete file is validated before any write; accepted records are then inserted in a single transaction that commits only if every insertion succeeds. No partial imports are stored, and no manual rollback feature is built.
- Context: Closes CSV Import Specification §16 "partial import support" and "import rollback behavior", following §11's preferred approach ("validate the complete file before writing records"). The transaction pattern mirrors the DEC-035 sale transaction already in the codebase. With DEC-053's per-row duplicate skipping, a run's outcome is deterministic: accepted rows commit as one unit or not at all.
- Method: Chosen with the project owner from documented options (2026-11-07, CSV import phase).

### DEC-055: Import Scope in Version 1

- Status: Accepted
- Decision: The v1 CSV import covers the historical dataset format only (`date,store,item,sales`). The operational sales import (`sale_date,sku,quantity` creating stock-reducing sales) is not built in v1.
- Context: The historical import is what the forecasting phase needs (TASK-022–025). An operational import would first require its own decisions — whether it reduces stock, whether insufficient stock blocks the file, record immutability limits, source identification — per CSV Import Specification §10; deferring avoids inventing that policy now. It may be re-proposed later with a superseding decision.
- Method: Chosen with the project owner from documented options (2026-11-07, CSV import phase).

### DEC-061: Dashboard Metric Set

- Status: Accepted
- Decision: The v1 Dashboard shows six metric groups over actual application data: (1) total active products, (2) total current stock, (3) products needing reorder (BR-022: current stock ≤ reorder point, advisory data from the restocking calculations), (4) recent sales activity (units sold and number of sales in the last 7 days ending today, UTC), (5) the top 3 selling products over the last 30 days (by units), and (6) a forecast-readiness line (how many active products are linked to a dataset item per DEC-060, out of the total).
- Context: features.md lists eight candidate indicators and leaves finalization to UI/business-rule design. The forecast "highlights" candidate (running a live forecast per product on every dashboard visit) is deferred: each visit would trigger N model predictions and artifact loads for a summary line — the Forecast page already owns that workflow, and the readiness metric tells users what is forecastable. Sales trends (TASK-038) and the low-stock overview (TASK-039) are their own dashboard sections/tasks; all windows end at the current UTC date and align with DEC-059's calendar-day view.
- Method: Chosen with the project owner from documented options (2026-11-10/11, TASK-037): six-metric set (chosen) vs. inventory-only vs. all eight candidates.

### DEC-060: Product ↔ Dataset-Item Forecast Mapping

- Status: Accepted
- Decision: Products gain a nullable **`dataset_item_id`** field (positive integer or NULL). The Forecast page is product-driven: the user selects an operational product; products linked to a dataset item are forecast from that item's imported `historical_sales` series; unlinked products receive a clear "no dataset item linked" message instead of a forecast.
- Context:
  - Closes prediction-logic §18's leftover: §3's "User Selects Product" flow requires the connection between the operational product universe (SKUs, restocking) and the historical dataset universe (items 1–50, what the model was trained on, DEC-052 kept them separate).
  - A product field makes the link explicit, persistent, user-controlled, and reviewable in the existing product forms; SKU-pattern inference was rejected (fabricates a convention, silently mis-forecasts) and item-only forecasting was rejected (leaves the two app halves permanently disconnected).
  - The forecast consumes **the linked item's imported history only** — operational sales are not mixed in v1: they are a different series (different time span, recorded quantities vs dataset observations) and mixing would change what the DEC-057 model was validated on. Revisit with a new decision if a combined-history forecast is ever wanted.
  - `historical_sales.gaps` inside an item's observed span are zero-filled calendar days before prediction: the model's world is a continuous daily series, and the dataset's zero-sales days are real observations (the table allows quantity 0, unlike operational `sales`). Consequence: DEC-058 "observed days" = calendar days in the item's span, after zero-fill.
  - Schema change is additive (nullable column), no data migration, soft-delete and all existing rules unaffected.
- Method: Chosen with the project owner from documented options (2026-11-10, Forecast page task).

### DEC-059: Average Daily Demand Window Anchoring

- Status: Accepted
- Decision: Average Daily Demand (the demand input for BR-020/DEC-032 and BR-024/DEC-038) is computed as the mean of the product's daily sold quantity over a **calendar window ending at the product's last recorded sale date**, covering `min(30 days, history span)` calendar days, with days inside the window that have no sale counted as zero demand. A lone single-day history therefore yields the sale itself as the demand (span 1), not the sale divided by 30.
- Context:
  - Deciding anchor and denominator closes the ambiguity in DEC-038's "most recent 30 days of available history" (three variants considered; see Method).
  - Ending at the last recorded sale (not today) treats an old backdated sale as "this is the most recent demand we know about" and never manufactures zero-demand days the business layer has no evidence for; gaps *between* recorded sales still count as zero because they are in-history non-sale days.
  - Denominating by calendar days (zeros filled) treats "no sale" as "zero demand" — intermittent sellers get fair, lower demand estimates, which matters for fair reorder points and consistent with the project goal of forecasting *demand* rather than sale-day volume.
  - The cap `min(30, span)` avoids diluting short histories with a fixed 30 denominator, so a new product's early demand is not understated purely because data is young; recommendation availability from the first observed day follows DEC-033 (2026-11-10 confirmation).
  - Note the deliberate difference from the ML feature windows (features are observation-based per feature-engineering): restocking formulas are calendar-day based by this decision — both documented, serving different purposes (DEC-030 keeps them separate components).
- Method: Chosen with the project owner from documented options (2026-11-10, TASK-035): calendar days with zeros filled (chosen) vs. sale-day-records-only vs. calendar window ending today.

### DEC-058: Insufficient-History Forecasting Policy

- Status: Accepted
- Decision: Product forecasting eligibility thresholds, applied at inference time:
  - **≥ 31 observed days of history** → the full Random Forest model (DEC-057) with recursive features (DEC-025). 31 is the measured minimum for the feature set (TASK-028: `rolling_mean_30` plus the one-step shift).
  - **1 → 30 observed days** → fall back to the trailing-7-day moving average forecast (baseline `moving_average_7`, validation MAE 8.077), applied recursively over the horizon with predictions included in the trailing window. No product is blocked from forecasting by short history.
  - **0 observed days** → forecasting is refused with an explicit "no suitable history exists" error (prediction-logic §13).
- Context: prediction-logic §13 requires an explicit insufficient-history behavior and feature-engineering §8 sanctions "use a simpler forecasting approach for products with limited history". The MA-7 choice is evidence-based (it is the strongest baseline measured at TASK-027 and beats MA-30's 8.298) and keeps every policy-facing forecast available from day one of sales. Consistent with §6, model-path features are computed exactly as in training (observation-based, leakage-free).
- Method: Chosen with the project owner from documented options (2026-11-10, TASK-033). Companion policies decided autonomously per existing doc language: predictions stay raw for evaluation (rounding happens in business logic, prediction-logic §11) and negative predictions are clipped to zero and documented (prediction-logic §10; the Random Forest structurally cannot emit negatives since leaf values are averages of non-negative sales).

### DEC-057: Final Forecasting Model Selection

- Status: Accepted
- Decision: The **Random Forest Regressor** (n_estimators=200, min_samples_leaf=5, random_state=2026) is the selected demand-forecasting model, using `FEATURE_COLUMNS = [day_of_week, month, day_of_month, lag_1, lag_7, rolling_mean_7, rolling_mean_30]`. Linear Regression is retained in documentation as the runners-up evidence trail, not the production model.
- Evidence (measured, per DEC-027 rules applied to validation 2016 — `model-evaluation.md` §17/§18):
  - Rule 2 (beat both baselines): both candidates pass — Random Forest MAE 6.033 and Linear Regression 6.482 vs. MA-7 8.077 and Naive 10.270.
  - Rule 1 (primary metric, lowest validation MAE): Random Forest 6.033 < Linear Regression 6.482.
  - Rule 4 (prefer simpler if within 5%): **not triggered** — Linear Regression is ≈7.4% worse; the gap is outside the band.
  - Rule 3 (RMSE tie-breaker): not needed (MAE is decisive), RMSE agrees (7.785 vs 8.387).
  - One-time test-window confirmation (2017, DEC-056 single touch): Random Forest MAE 6.088/RMSE 7.910 — beats both test baselines (MA-7 8.378) and stays ahead of Linear Regression (6.637/8.611).
- Context: The candidates were defined at DEC-020/forecasting-strategy §3.3–3.4 and the selection rules pre-accepted at DEC-027; applying them required no new methodology decision, so the selection was made autonomously per the project's guardrails (a user checkpoint was only reserved for a within-5% tie or a baseline failure, neither of which occurred). Interpretability trade-off acknowledged: the forest is less transparent than a linear fit; its configuration (5 conservative parameters, fixed seed) and feature importances are documented at TASK-032/033. The validation protocol used features built from strictly past actuals (no leakage), so the margin reflects real one-step-ahead advantage.
- Method: decided by the agent autonomously applying DEC-027 to measured TASK-030 results (2026-11-09), recorded for review.

### DEC-056: Chronological Train/Validation/Test Split

- Status: Accepted
- Decision: The historical store-1 series (2013-01-01 → 2017-12-31) is split by calendar year: **Training 2013-01-01 → 2015-12-31** (3 full years, ≈60% of days), **Validation 2016-01-01 → 2016-12-31** (full year, ≈20%), **Test 2017-01-01 → 2017-12-31** (full year, ≈20%). All model selection uses validation MAE only (DEC-027); the test window is evaluated once, at final model selection (TASK-031), and never used to tune candidates.
- Context: Finalizes the "final chronological split dates" open item from forecasting-strategy §8/§13, gated on TASK-026 exploration evidence. Complete calendar-year windows give every bucket a full seasonal cycle (leap-year day included in 2016), avoiding partial-season bias; test is the most recent year, which best mirrors forecasting the then-unseen 2018+. Chosen over 2017-quarter splits (training richer but validation windows incomplete) and rolling weekly folds (more robust but higher compute/complexity — acceptable alternative if evaluation shows unlucky windows, would require a superseding decision).
- Method: Chosen with the project owner from documented options (2026-11-09, baseline phase unblocked by TASK-026).

---

## 6. Machine Learning Decisions

### DEC-017: Forecasting Problem

- Status: Accepted
- Decision: Treat demand forecasting as a supervised regression problem.
- Context: The model predicts numerical future sales demand using historical observations.

### DEC-018: Forecasting Granularity

- Status: Proposed
- Decision: Use daily demand forecasting per product.
- Context: The proposed historical dataset contains daily sales records.
- Confirmation Required: Confirm the final aggregation and entity mapping.

### DEC-019: Baseline Models

- Status: Proposed
- Decision: Implement simple baselines before evaluating more complex ML models.
- Candidates:
  - Naive forecasting.
  - Historical average.
- Context: Baselines provide a reference for measuring whether ML adds value.

### DEC-020: Candidate ML Models

- Status: Proposed
- Candidates:
  - Linear Regression.
  - RandomForestRegressor.
- Decision Rule: Select the final model based on evaluation results rather than assuming one candidate is best.

### DEC-021: Candidate Features

- Status: Proposed
- Features:
  - Day of week.
  - Month.
  - Day of month.
  - Lag 1.
  - Lag 7.
  - Rolling mean 7.
  - Rolling mean 30.
- Context: These features provide calendar and historical demand information.

### DEC-022: Rolling Feature Leakage Prevention

- Status: Accepted
- Decision: Rolling features must use historical observations only and exclude the current target.
- Context: Including the current target in a feature would introduce data leakage.

### DEC-023: Evaluation Metrics

- Status: Proposed
- Decision: Use MAE and RMSE as the primary evaluation metrics.
- Context: They provide understandable measures of prediction error.

### DEC-024: Time-Aware Evaluation

- Status: Accepted
- Decision: Use chronological train, validation, and test splits for the primary forecasting evaluation.
- Context: Random splitting can leak future information into training.

### DEC-025: Recursive Multi-Step Forecasting

- Status: Accepted
- Decision: Use recursive multi-step forecasting as the inference strategy.
- Context:
  - A single one-step model is used: forecast day 1, append the predicted value to a temporary forecast history, recalculate lag and rolling features, forecast day 2, and repeat until the requested horizon is reached.
  - This reuses one model artifact, avoids training one model per forecast day, and supports any allowed horizon (7, 14, 30 days per DEC-026).
  - Known trade-off: prediction errors accumulate over longer horizons. This must remain documented as a limitation (LIM-008) and referenced in the interface.
- Important: Appended predictions must exist only in temporary forecast history. They must never be written to operational sales records (consistent with DEC-029 and the prediction-logic documentation).
- Decided: 2026-11-04.

### DEC-026: Forecast Horizon

- Status: Accepted
- Decision: The forecast horizon is user-selectable among 7, 14, or 30 future days, with 7 days as the default.
- Context:
  - 7 days matches weekly demand patterns and carries the lowest accumulated error.
  - 14 and 30 days accommodate longer supplier lead times, with explicitly higher uncertainty.
  - The UI must display the forecast period clearly (consistent with BR-017).
  - Evaluation should consider the multi-step behavior (DEC-025) when reporting metrics.
- Decided: 2026-11-04.

### DEC-027: Model Selection Criteria

- Status: Accepted
- Decision: Select the final forecasting model using the following rules, applied to measured validation results only:
  1. Primary metric: validation MAE.
  2. A candidate model must beat both baseline models (Naive Forecast and Historical Average) on validation MAE to be eligible for selection.
  3. RMSE is used as a tie-breaker when MAE values are effectively equal.
  4. If two candidates' validation MAE values are within 5% of each other, prefer the simpler, more understandable model.
- Context:
  - A model must never be selected solely because it is more complex (consistent with DEC-045 and the evaluation documentation).
  - If no candidate meaningfully beats the baselines, the situation must be documented and investigated rather than forcing a selection.
  - Actual selection still depends on measured evaluation results, which do not exist yet.
- Decided: 2026-11-04.

### DEC-028: Forecast Persistence

- Status: Accepted
- Decision: Forecasts are generated on demand and are not persisted in the initial application. The optional Forecast Results entity is not built in version 1.
- Context:
  - Generation on demand keeps the database schema and application simple while forecast history is not an approved requirement.
  - Forecast-versus-actual visualization can be computed by comparing generated forecasts against actual recorded sales history.
  - If forecast history, tracking, or reporting over time becomes an approved requirement later, a new decision must supersede this one and the Forecast Results entity may then be introduced.
- Decided: 2026-11-04.

---

## 7. Business Logic Decisions

### DEC-029: Forecasting and Inventory Separation

- Status: Accepted
- Decision: The forecasting model predicts demand but does not directly modify inventory.
- Context: Forecasting and operational inventory management have separate responsibilities.

### DEC-030: Restocking Recommendation Separation

- Status: Accepted
- Decision: Restocking calculations belong to a separate business logic component.
- Context: The recommendation engine consumes forecast and inventory information.

### DEC-031: Restocking Recommendations Are Advisory

- Status: Accepted
- Decision: Recommendations are informational and do not automatically purchase products or modify inventory.
- Context: The initial application does not implement automated purchasing.

### DEC-032: Reorder Point Formula

- Status: Accepted
- Formula:

  `Reorder Point = Average Daily Demand * Lead Time + Safety Stock`

- Context: This is a candidate formula for determining when restocking should be considered.
- Input sources now defined: Average Daily Demand = mean of the product's daily sales over the most recent 30 available days (per DEC-038); Lead Time = manual per-product field (DEC-037); Safety Stock = manual per-product field (DEC-036).
- Method: Applied as documented during TASK-016 (2026-11-06) — the inputs were all closed previously and the formula was already referenced by the stock-status rule (BR-008). Implemented in `src/smartstock/domain/inventory.py` with upward rounding to whole units so rounding can never hide a shortage. If the project owner revises the formula later, the change is isolated to the domain module.

### DEC-033: Recommended Order Quantity

- Status: Accepted
- Formula:

  `Recommended Order Quantity = max(0, Target Stock - Inventory Position)`

- Context: This is a candidate formula for estimating the quantity required to reach the target stock.
- Inputs now defined: Target Stock per DEC-038; Inventory Position = current stock (no incoming-stock tracking in v1, consistent with DEC-031 and BR-022).
- Confirmation: Confirmed by the project owner on 2026-11-10 during TASK-034, choosing the clamped form from documented options — the max(0, …) clamp keeps a command "recommendation quantity" a nonnegative actionable number; if stock already meets or exceeds target, the recommendation is 0 ("no need to order") rather than a negative surplus value, which also keeps the reorder framing (Current Stock ≤ Reorder Point) consistent with the quantity framing. Signed-difference and extra-buffer variants were considered and rejected (the Target Stock formula already contains the lead-time and 7-day buffers, so adding buffers would double-count; surplus display has no operational benefit in v1).
- Recommendation availability: a recommendation requires at least one observed day of history for Average Daily Demand (the "minimum required history" of DEC-038 resolves to the DEC-058 shortfall policy: recommendations are available from the first observed day; 0 days → unavailable with a clear explanation).

### DEC-034: Negative Stock Policy

- Status: Accepted
- Decision: Negative stock is prohibited. No operation (sale recording, stock adjustment, movement, or import) may drive a product's current stock below zero.
- Context:
  - Negative quantities create ambiguous, unreliable inventory data and complicate every downstream calculation.
  - If insufficient stock is encountered during a sale, the insufficient-stock policy (DEC-035) applies.
  - Validation and error handling must enforce this invariant consistently across all inventory-affecting operations.
- Decided: 2026-11-04.

### DEC-035: Insufficient Stock During Sales

- Status: Accepted
- Decision: A sale that would exceed available stock is rejected. The sale is not recorded and inventory is left unchanged.
- Context:
  - The user receives a clear validation message identifying the attempted quantity and the available quantity (for example: "insufficient stock: 3 available, 5 requested").
  - This keeps recorded sales consistent with inventory and avoids silently representing unfulfilled demand as sold units (consistent with DEC-016 and the sales/demand distinction, BR-016).
  - If the user later explicitly requires backorder support, a new decision must supersede this one.
- Decided: 2026-11-04.

### DEC-036: Safety Stock Calculation

- Status: Accepted
- Decision: Safety Stock is manually configured per product. It is an optional product field with a default of 0.
- Context:
  - A manual value is transparent and understandable for the user, and it works immediately regardless of how much sales history a product has.
  - Statistical calculation from demand variability (for example, a z-score × standard deviation × √lead-time formula) requires substantial per-product history and more assumptions; it may be introduced later only if justified and explicitly re-decided.
  - The product schema includes `safety_stock` as a nonnegative integer.
- Decided: 2026-11-04.

### DEC-037: Lead Time Source

- Status: Accepted
- Decision: Lead Time is a manually configured per-product field (`lead_time_days`, a nonnegative integer, optional with a default of 3 days).
- Context:
  - The historical dataset contains no supplier, purchasing, or lead-time information, so lead time cannot be derived from data.
  - Per-product configuration matches real usage, since suppliers and delivery times commonly differ by product.
  - The Restocking Recommendation Service reads this field directly; recommendations explain the lead time used.
- Decided: 2026-11-04.

### DEC-038: Target Stock Calculation

- Status: Accepted
- Decision: Target Stock is calculated using:

  `Target Stock = Average Daily Demand × (Lead Time + 7 days) + Safety Stock`

  where Average Daily Demand is the mean of the product's daily sales over the most recent 30 days of available history.
- Context:
  - The (Lead Time + 7 days) factor covers expected demand during replenishment plus a 7-day buffer after restock, replacing a separate review-period concept with something simple and explainable.
  - Using historical average demand keeps restocking logic independent of the forecasting model, so recommendations can be explained and tested standalone (consistent with DEC-030).
  - If the product lacks the minimum required history, the recommendation is unavailable with a clear explanation (consistent with LIM-010 and BR-019); the minimum requirement follows the approved minimum-history policy.
  - Average Daily Demand is rounded up to a whole unit in the business logic layer, per the approved rounding policy.
- Decided: 2026-11-04.

---

## 8. User Interface Decisions

### DEC-039: Interface Style

- Status: Proposed
- Decision: Use a simple dashboard-style interface.
- Context: The application should prioritize readability and ease of use.

### DEC-040: Initial Navigation

- Status: Proposed
- Proposed pages:
  - Dashboard.
  - Products & Inventory.
  - Sales Management.
  - Sales Analytics.
  - AI Forecasting.
  - CSV Import.
- Confirmation Required: Finalize navigation after reviewing implementation needs.

### DEC-041: Initial Store Workflow

- Status: Proposed
- Decision: Prioritize a single-store workflow.
- Context: The initial project should avoid unnecessary multi-branch complexity.

---

## 9. Development Workflow Decisions

### DEC-042: AI Agent Execution Mode

- Status: Accepted
- Decision: Use Autonomous with Guardrails.
- Context: The AI Agent should execute clearly defined implementation tasks independently while respecting project decisions and safety boundaries.

### DEC-043: Documentation Detail

- Status: Accepted
- Decision: Maintain comprehensive project documentation.
- Context: Documentation should be detailed enough to support implementation and future maintenance.

### DEC-044: Development Workflow

- Status: Accepted
- Decision: Implement the project incrementally using small, testable tasks.
- Context: Each meaningful implementation step should be verified before dependent work continues.

### DEC-045: No Unsupported Claims

- Status: Accepted
- Decision: The AI Agent must not invent requirements, test results, dataset properties, or implementation status.
- Context: Project documentation and progress reports must reflect actual evidence.

### DEC-046: Destructive Operations

- Status: Accepted
- Decision: Destructive or difficult-to-reverse operations require explicit user approval.
- Examples:
  - Deleting operational data.
  - Replacing important database contents.
  - Removing significant project files.
  - Performing irreversible migrations.

---

### DEC-047: Inventory Stock Storage Model

- Status: Accepted
- Decision: Store current stock directly as a maintained column in the products table (Option A in Database Schema §6). The Inventory Movements entity is not built in version 1.
- Context: The schema document presented two inventory models. Option A (direct column) fits the small single-store v1 application: sales and manual adjustments update the column atomically, stock checks for the DEC-035 insufficient-stock rule are a simple read, and no write path must keep a movement log in sync. No v1 requirement demands stock-change history or an audit trail. If movement tracking is approved later, it becomes a new entity plus reconciliation logic (a schema change requiring its own decision).
- Method: Chosen with the project owner from documented options (2026-11-04).

### DEC-048: Product Deletion Policy

- Status: Accepted
- Decision: Soft delete. Products receive an `is_active` flag; the "remove" action deactivates a product instead of deleting the row. Sales and other related records remain intact.
- Context: Protects historical records per BR-004 and DEC-046, keeps the topology simple (no orphaned rows), and is reversible. Counts and listings exclude inactive products (BR-026). The status values follow BR-008 vocabulary.
- Method: Chosen with the project owner from documented options (2026-11-04).

### DEC-049: Sales Returns in Version 1

- Status: Accepted
- Decision: Returns (and cancelled sales) are not supported in version 1. Recorded sales are immutable in v1; corrections happen through explicitly recorded manual adjustments only.
- Context: No v1 requirement demands returns. Deferring keeps the schema minimal (Products + Sales only, per DEC-047/DEC-028) and avoids complicating the negative-stock and insufficient-stock validation (DEC-034/DEC-035) with negative sale quantities. If returns become a requirement later, a return operation must be designed with its own stock and validation rules.
- Method: Chosen with the project owner from documented options (2026-11-04).

### DEC-050: Sales on Inactive Products

- Status: Accepted
- Decision: Recording a sale for a deactivated (soft-deleted) product is rejected. New sales target only existing, active products; historical sales of deactivated products remain intact.
- Context: Finalizes BR-010 ("sales must reference a valid product") together with the DEC-048 soft-delete semantics: an inactive product is removed from operations, so accepting new sales for it would contradict BR-026's exclusion of inactive products from operational counts.
- Method: Agent implementation decision within guardrails (2026-11-04, TASK-015), applying documented rules; reversible if the project owner prefers sellable-inactive behavior.

### DEC-051: Future Sale Dates

- Status: Accepted
- Decision: Sale dates must be valid `YYYY-MM-DD` dates and must not be in the future. Backdated entries (e.g., recording yesterday's counter sales) are allowed; dates are still validated against current stock at recording time.
- Context: Finalizes BR-011, whose documented intent is to reject future dates unless the application explicitly supports scheduled transactions — which it does not.
- Method: Agent implementation decision within guardrails (2026-11-04, TASK-015), applying documented rules.

---

## 10. Open Decisions Summary

All open decisions have been closed, most recently on 2026-11-07 (CSV import phase):

| Decision ID | Topic | Resolved Decision |
|---|---|---|
| DEC-015 | Dataset-to-product mapping | One selected store; each `item` maps to one product |
| DEC-025 | Multi-step forecasting strategy | Recursive forecasting |
| DEC-026 | Forecast horizon | User-selectable: 7 (default), 14, or 30 days |
| DEC-027 | Model selection criteria | Lowest validation MAE; must beat both baselines; RMSE tie-breaker; prefer simpler within 5% |
| DEC-028 | Forecast persistence | Generate on demand; no persistence in v1 |
| DEC-034 | Negative stock policy | Negative stock never allowed |
| DEC-035 | Insufficient stock behavior | Sale rejected; inventory unchanged |
| DEC-036 | Safety stock | Manually configured per product (optional, default 0) |
| DEC-037 | Lead time source | Manual per-product field (optional, default 3 days) |
| DEC-038 | Target stock | `Avg Daily Demand × (Lead Time + 7) + Safety Stock`, demand = 30-day mean |
| DEC-033 | Order quantity (confirmed) | `max(0, Target Stock − Inventory Position)`; recommendation needs ≥1 observed day (DEC-058) |
| DEC-047 | Stock storage model | Direct `current_stock` column on products; movements entity not built in v1 |
| DEC-048 | Product deletion | Soft delete via `is_active` flag |
| DEC-049 | Returns | Not supported in v1; recorded sales immutable |
| DEC-050 | Sales on inactive products | Rejected; sales target existing, active products only |
| DEC-051 | Future sale dates | Rejected; backdated entries allowed |
| DEC-052 | Historical import storage | Dedicated `historical_sales` table keyed by dataset `item`; `import_batches` metadata; operational `sales` untouched |
| DEC-053 | Duplicate import handling | SHA-256 file fingerprint rejection + unique (`item`, `sale_date`) constraint; duplicates skipped and counted |
| DEC-054 | Import atomicity | All-or-nothing; full-file validation then single transaction; no partial imports or manual rollback |
| DEC-055 | Import scope in v1 | Historical dataset import only; operational sales import not built in v1 |
| DEC-056 | Chronological split | Train 2013–2015, Validation 2016, Test 2017; test touched once (DEC-027) |
| DEC-057 | Final model | Random Forest (seed 2026); RULES: lowest validation MAE 6.033, LR ≈7.4% worse → 5% band not triggered |
| DEC-058 | Short-history policy | ≥31 days → RF; 1–30 days → MA-7 recursive fallback; 0 days → explicit error |
| DEC-059 | Demand window anchoring | Calendar window ends at last sale; zeros filled; denominator min(30, span) |
| DEC-060 | Product ↔ dataset-item mapping | Nullable products.dataset_item_id; forecast from the linked item's imported history only |
| DEC-061 | Dashboard metrics | Six groups: products, stock, needing-reorder, 7-day sales, top-3 sellers (30 d), forecast readiness |

---

## 11. Decision Management Rules

When a new important decision is made:

1. Assign a unique decision ID.
2. Record the decision.
3. Explain its context.
4. Set its status.
5. Identify affected documentation.
6. Update related requirements or specifications.
7. Mark replaced decisions as Superseded rather than silently deleting them.

The AI Agent must not change an Accepted decision without explicit authorization.

When a decision is unclear, record the question and continue with independent work where possible.