# Task Breakdown

## 1. Purpose

This document breaks SmartStock AI implementation into manageable development tasks.

Each task has:

- A unique ID.
- A priority.
- Dependencies.
- An initial status.
- A description.
- Expected completion evidence.

This document is an execution checklist, not proof that any task has been completed.

All tasks start with the status:

`Not Started`

---

## 2. Task Statuses

Use the following statuses:

| Status | Meaning |
|---|---|
| Not Started | Work has not started. |
| In Progress | Work is currently being implemented. |
| Implemented | Code has been written. |
| Tested | Relevant automated tests have passed. |
| Verified | Functionality has been tested and accepted against its requirements. |
| Blocked | Work cannot continue because of a dependency or unresolved issue. |
| Deferred | Work is intentionally postponed. |
| Rejected | Work is no longer part of the approved scope. |

Do not skip verification by marking implemented code as complete.

---

## 3. Priority Levels

| Priority | Meaning |
|---|---|
| P0 | Essential for the core application. |
| P1 | Important for the expected project experience. |
| P2 | Optional enhancement. |
| P3 | Future improvement. |

---

## 4. Foundation and Setup

### TASK-001: Review Project Documentation

- Priority: P0
- Status: Verified
- Dependencies: None

Description:

Review the project documentation and identify conflicts, missing decisions, and implementation constraints.

Evidence:

- Documentation review completed.
- Blocking questions recorded.
- Architecture and scope understood.

Completion record (2026-11-04): All 38 documentation files reviewed. All 10 open decisions were closed with the project owner (DEC-015, DEC-025-028, DEC-034-038) and affected specifications updated. Identified conflict: task-breakdown.md uses an 8-status vocabulary while agent-workflow.md/progress.md use 5 statuses; not blocking (tracked as a minor documentation inconsistency).

### TASK-002: Initialize Development Environment

- Priority: P0
- Status: Verified
- Dependencies: TASK-001

Description:

Set up Python, the virtual environment, and required dependencies.

Evidence:

- Virtual environment created.
- Dependencies installed.
- Basic application starts successfully.

Completion record (2026-11-04): Python 3.12.3 (compatible with the approved 3.11 requirement), `.venv` validated, all 7 approved libraries installed (streamlit 1.66.1, pandas 3.1.1, numpy 2.5.4, scikit-learn 1.9.1, plotly 7.1.0, joblib 1.6.0, pytest 9.2.0) and import-verified. The misnamed empty `requirments.txt` was replaced by `requirements.txt` with minimum-version constraints.

### TASK-003: Initialize Project Structure

- Priority: P0
- Status: Verified
- Dependencies: TASK-001, TASK-002

Description:

Create the directories and initial files according to the approved project structure.

Evidence:

- Project structure exists.
- Imports work correctly.
- No unnecessary files or abstractions are introduced.

Completion record (2026-11-04): Directory layout created per `../02-architecture/project-structure.md` (`src/smartstock/*` subpackages with `__init__.py` files, `data/`, `models/artifacts/`, `scripts/`, `tests/`). Kaggle dataset files moved from the repository root into `data/raw/` (git-ignored) so large datasets are never committed. Empty leftover placeholder directories (`ml/`, `pages/`, `services/`, `utils/`) not present in the approved structure were removed. Minimal `app.py` and `config.py` created; verified by compile check and a headless Streamlit smoke test (HTTP 200, no errors).

### TASK-004: Configure Git and Ignore Rules

- Priority: P0
- Status: Verified
- Dependencies: TASK-003

Description:

Configure Git and `.gitignore`.

Evidence:

- Generated files and local environment files are excluded.
- Source code and required documentation remain tracked.

Completion record (2026-11-04): Git repository initialized on branch `main` with existing approved `.gitignore`. Verified by inspection: `.venv/`, `data/raw/*` datasets, local DB files, and model artifacts are excluded; docs, app, config, and project structure are tracked. Checkpoint commits made after each setup step.

---

## 5. Dataset and Data Preparation

### TASK-005: Obtain and Inspect the Dataset

- Priority: P0
- Status: Verified
- Dependencies: TASK-001

Description:

Obtain the selected historical sales dataset and inspect its actual structure.

Evidence:

- Dataset source recorded.
- Actual columns documented.
- Data coverage and quality inspected.
- Limitations documented.

Completion record (2026-11-04): The Kaggle Store Item Demand dataset was already downloaded to `data/raw/train.csv` (913,000 rows) and was inspected programmatically (`/tmp/opencode/inspect_dataset.py`). Verified: expected columns exactly (`date,store,item,sales`), date range 2013-01-01 → 2017-12-31 (1,826 days), 10 stores × 50 items with a complete daily sequence for every store-item combination, zero missing values, zero duplicate keys, zero negative or fractional sales, one zero-sales record. Store 1 subset (DEC-015 target) holds 91,300 rows across all 50 items. Verified characteristics recorded in `../03-data/dataset-overview.md`. Limitation: `test.csv` is the competition's unlabeled 90-day future set (date, store, item only) — it cannot be used for evaluation; all evaluation must use chronological splits of `train.csv`.

### TASK-006: Implement Dataset Loader

- Priority: P0
- Status: Verified
- Dependencies: TASK-005

Description:

Implement reusable functions for loading the selected dataset.

Evidence:

- Valid files load successfully.
- Missing or unreadable files produce clear errors.
- Loader tests pass.

Completion record (2026-11-04): `load_historical_dataset()` implemented in `src/smartstock/ml/preprocessing.py` with a dedicated `DatasetError` type and checks for missing file, unreadable file, empty file, and missing required columns (error messages name the file and columns). Tests: 6 loader tests in `tests/test_preprocessing.py`, all passing. Real-dataset check: `data/raw/train.csv` loads (913,000 rows).

### TASK-007: Implement Data Validation

- Priority: P0
- Status: Verified
- Dependencies: TASK-006

Description:

Validate required columns, data types, dates, and sales values.

Evidence:

- Valid data is accepted.
- Invalid data is handled safely.
- Validation tests pass.

Completion record (2026-11-04): `validate_and_parse_dataset()` implemented — rejects missing required values, nonnumeric or noninteger identifiers, nonnumeric sales, negative sales, unparseable dates, and duplicate (date, store, item) keys with clear errors; parses `date` to datetime and identifiers to integers; returns a copy (input never mutated). Rejection policies documented in `../03-data/data-preprocessing.md` section 19 based on TASK-005 evidence. Tests: 11 validation tests passing (two initial test bugs were in the test fixtures themselves — a misplaced empty field and a wrong dtype expectation — and were fixed; validation code unchanged). Real-dataset check: all 913,000 rows validate in ~0.6 s.

### TASK-008: Implement Data Preprocessing

- Priority: P0
- Status: Verified
- Dependencies: TASK-007

Description:

Implement the preprocessing rules defined in the data documentation.

Evidence:

- Preprocessing functions are reusable.
- Data quality issues are handled according to approved rules.
- Tests pass.

Completion record (2026-11-04): Implemented in `src/smartstock/ml/preprocessing.py`: `filter_store()` (DEC-015 store filtering with unknown-store rejection), `sort_chronologically()` (store, item, date), `detect_date_gaps()` (daily-sequence completeness per store-item series), `preprocess_dataset()` (full workflow returning a prepared DataFrame and the section-17 report). `scripts/prepare_dataset.py` writes the cleaned subset to git-ignored `data/processed/store_1_cleaned_sales.csv`. Real-dataset run report: source 913,000 records → store 1: 91,300 records, 50 products, date range 2013-01-01 → 2017-12-31, 0 zero-sales records, 50 series checked, 0 with gaps, 0 missing dates. Tests: 7 preprocessing tests passing (plus TASK-006/007 tests, 24 total).

---

## 6. Database and Persistence

### TASK-009: Confirm Initial Database Schema

- Priority: P0
- Status: Verified
- Dependencies: TASK-001

Description:

Review the logical database schema and resolve decisions necessary for the initial implementation.

Evidence:

- Initial schema documented.
- Required entities and relationships identified.
- Open decisions recorded.

Completion record (2026-11-04): Three remaining schema decisions closed with the project owner and recorded as DEC-047 (direct `current_stock` column; Inventory Movements entity not built in v1), DEC-048 (soft delete via `is_active` flag), and DEC-049 (no returns in v1; recorded sales immutable). `database-schema.md` updated accordingly (§4 decision notes with exact column constraints incl. CHECK `current_stock >= 0`, §6 decided Option A, §8 v1 relationships Products→Sales only, §11 deletion policy, §14 open-decision table). `business-rules.md` BR-003/BR-004 updated to Accepted and §12 Open Questions updated. Only the CSV import duplicate-handling decision remains open, which is gated on the import feature (§12).

### TASK-010: Implement SQLite Initialization

- Priority: P0
- Status: Verified
- Dependencies: TASK-009

Description:

Create the SQLite database initialization process.

Evidence:

- Database initializes successfully.
- Required tables exist.
- Initialization can be repeated safely.

Completion record (2026-11-04): Approved schema lives in `database/schema.sql` (single authoritative DDL file): `products` (with `current_stock`, `lead_time_days` default 3, `safety_stock` default 0, `is_active` flag, CHECK constraints for DEC-034/DEC-048 and defaults for DEC-036/DEC-037) and `sales` (positive-quantity CHECK, product FK per DEC-035 context), plus an index on (product_id, sale_date); ISO 8601 TEXT dates/timestamps throughout. `src/smartstock/database/schema.py` declares required tables and expected columns as the verification source. `src/smartstock/database/initialization.py` provides `initialize_database()` (creates parent directories, applies schema with foreign keys enabled, commits) and `verify_tables()` (missing-file, missing-table, and missing-column checks with clear `DatabaseError` messages). Idempotent by construction (`CREATE TABLE IF NOT EXISTS`; repeated initialization preserves data). Tests: 11 in `tests/test_database.py` covering creation, idempotency, missing database, empty database, CHECK constraints (negative stock, bad `is_active`, negative lead time, duplicate SKU, nonpositive sale quantity) and FK enforcement — all passing. Smoke check: initialized the real configured path `data/smartstock.db` (git-ignored).

### TASK-011: Implement Database Connection Management

- Priority: P0
- Status: Verified
- Dependencies: TASK-010

Description:

Implement reusable database connection handling.

Evidence:

- Connections are managed safely.
- Errors are handled appropriately.
- Relevant tests pass.

Completion record (2026-11-04): `src/smartstock/database/connection.py` provides `connect()` (opens with `PRAGMA foreign_keys = ON`, `sqlite3.Row` factory, auto-initializes a missing database file, wraps sqlite errors in a clear `DatabaseError`) and `session()` (context manager that commits on success, rolls back on exception, and always closes). Note: the PRAGMA is per-connection in SQLite, so every connection opened through these helpers is consistently configured; tests that open raw connections set the pragma themselves. Tests: 7 in `tests/test_connection.py` (row factory + pragma, auto-initialize, open-failure wrapping via monkeypatch, commit on success, rollback on error, close behavior) — all passing. Full suite at this point: 42 tests.

### TASK-012: Implement Repositories

- Priority: P0
- Status: Verified
- Dependencies: TASK-011

Description:

Implement database access functions for the confirmed entities.

Evidence:

- Required CRUD operations work.
- SQL queries are parameterized.
- Repository tests pass.

Completion record (2026-11-04): Three repositories under `src/smartstock/repositories/`, all requiring a connection from the connection module and returning plain dictionaries via parameterized SQL only: `product_repository.py` (create with approved defaults; get by id/SKU; list with active-only filter per DEC-048/BR-026; partial-field update with refreshed `updated_at` where stock is intentionally excluded; `set_product_active()` for soft delete; SKU conflicts surface as clear `ValueError`s), `inventory_repository.py` (sole owner of stock changes per DEC-047: `get_current_stock`, `adjust_stock` with signed delta rejecting zero/non-integer changes and negative results per DEC-034, `set_stock_level` for explicit corrections only, `updated_at` refreshed on every change), and `sales_repository.py` (`record_sale` with positive-quantity and `YYYY-MM-DD` validation; `list_sales` with optional product/date-range filters; `get_daily_sales` per-day aggregation returning absent days as missing per the preprocessing policy; no update/delete — sales rows immutable per DEC-049). Shared helpers in `src/smartstock/utils/dates.py` (`utc_now_iso`). Tests: 23 in `tests/test_repositories.py` (create/read/update/list, SKU conflicts, soft-delete preservation, stock guards, sale filters and aggregation, error wrapping for unknown products) — all passing. End-to-end smoke against the real configured database succeeded (create product → adjust stock → record sale → read back). Full suite at this point: 65 tests.

---

## 7. Domain and Application Services

### TASK-013: Implement Product Services

- Priority: P0
- Status: Verified
- Dependencies: TASK-012

Description:

Implement product creation, retrieval, updating, and the approved removal behavior.

Evidence:

- Product operations work independently of Streamlit.
- Validation is enforced.
- Unit tests pass.

Completion record (2026-11-04): `src/smartstock/services/product_service.py` — Streamlit-independent functions that open managed sessions against `config.DATABASE_PATH` (overridable via `db_path` for tests): `create_product` (initial stock written with the product row so a product never exists without defined stock; defaults per DEC-036/037/048), `get_product`, `get_product_by_sku`, `list_products` (active-only per BR-026), `update_product` (editable fields only; explicitly rejects `current_stock` with a pointer to the inventory service), and `set_product_active` (soft delete/reactivation per DEC-048). Data-layer `ValueError`/`DatabaseError` messages propagate unchanged for the UI to display. Tests: covered by `tests/test_services.py` (9 product-service tests: defaults, duplicate SKU, retrieval, list exclusion, field updates, stock-change rejection, soft delete round trip).

### TASK-014: Implement Inventory Services

- Priority: P0
- Status: Verified
- Dependencies: TASK-012, TASK-013

Description:

Implement current stock retrieval and approved inventory adjustment behavior.

Evidence:

- Inventory calculations are correct.
- Invalid adjustments are handled.
- Relevant tests pass.

Completion record (2026-11-04): `src/smartstock/services/inventory_service.py` — `get_current_stock`, `adjust_stock` (signed change; zero/non-integer rejected; negative results rejected per DEC-034 with current stock in the message), and `set_stock_level` (explicit corrections only, documented as not for sales). Integer arithmetic verified; all adjustment interactions tested including the rejected paths (6 inventory-service tests).

### TASK-015: Implement Sales Services

- Priority: P0
- Status: Verified
- Dependencies: TASK-012, TASK-013, TASK-014

Description:

Implement sales recording and retrieval.

Evidence:

- Sales are stored correctly.
- Approved inventory interactions work.
- Relevant tests pass.

Completion record (2026-11-04): `src/smartstock/services/sales_service.py` — `record_sale` realizes DEC-035 + BR-012 atomically: one session/transaction performs stock validation, sale insert, and stock decrement (repositories gained an optional `commit` flag so the caller's session manager commits once; any failure rolls the whole transaction back). Rejects insufficient stock with a dedicated `InsufficientStockError(ValueError)` carrying `requested`/`available` for a clear UI message; verified that a rejected sale records no row and leaves stock unchanged. Additional validations finalized as DEC-050 (sales on inactive products rejected) and DEC-051 (future sale dates rejected; backdated allowed) — recorded in `decisions.md`, business rules BR-009…BR-013 statuses updated to Accepted. Read paths delegate to the repository: `list_sales` (filters) and `get_daily_sales` (per-day aggregation). Tests: 10 sales-service tests including an atomicity suite and a no-write smoke check against the real configured database (rejection leaves stock and rows untouched). Full suite at this point: 84 tests.

---

## 8. Product and Inventory Interface

### TASK-016: Implement Product Listing

- Priority: P0
- Status: Verified
- Dependencies: TASK-013

Description:

Create the Products and Inventory page with a product listing.

Evidence:

- Products are loaded from the database.
- Empty states are handled.
- Displayed values are correct.

Completion record (2026-11-06): Two commits. Groundwork (`85942a8`): `src/smartstock/domain/inventory.py` — pure calculations for the 30-day average daily demand (DEC-038; missing days count as zero), reorder point `demand × lead time + safety stock` rounded up (DEC-032, applied as documented), and the BR-008 classification (Out of Stock at zero, Low Stock at/below the reorder point, In Stock above); `sales_repository.get_daily_sales_by_product` (single grouped query to avoid a query per product); `inventory_service.get_stock_overview()` returning each active product plus `average_daily_demand`, `reorder_point`, and `stock_status`. Page (`src/smartstock/pages/products.py`): title, product table (name, SKU, category, stock, lead time, safety stock, reorder point, average demand, status with color markers), search by name/SKU (case-insensitive), category and status filters, count caption, low-stock summary banner, and both empty states (no products; no matches). `app.py` converted to `st.navigation` with a Dashboard placeholder ("use Products & Inventory today") and the Products & Inventory page; documented reliable dev command `streamlit run app.py` (app.py adds `src/` to `sys.path`). Tests: 23 new — domain parameter tests (window edges, ceiling, classifications), repo bulk-aggregation tests, service overview tests (new product, real sale effects, window exclusion of old sales, inactive exclusion), plus 11 Streamlit AppTest page tests (empty state, all displayed values per product, search, filters, no-match warning, low-stock banner, live stock updates) and app startup tests. Not excluded: BR-008 classification and DEC-032 formula applied as documented; both noted in business rules/decisions. Full suite: 119 tests passing.

### TASK-017: Implement Product Forms

- Priority: P0
- Status: Verified
- Dependencies: TASK-016

Description:

Implement product creation and editing forms.

Evidence:

- Valid products can be saved.
- Invalid input is rejected.
- Updated values appear correctly.

Completion record (2026-11-06): Add and edit forms on the Products & Inventory page (tabs "Add product" and "Edit product"), both submitting through the product service (no page-side SQL or duplication). Add form: name/SKU required, category optional, initial stock (≥0), lead time (default 3, DEC-037), safety stock (default 0, DEC-036). Edit form prefills the selected product (widget keys include the product id so switching selection resets state), updates exactly the editable fields, and never touches stock. Removal implemented as approved soft delete: deactivation behind an explicit confirmation checkbox (DEC-048), plus reactivation for inactive products; the inactive product disappears from the listing (BR-026) is verified in tests. Validation errors from the services (`ValueError`: empty name, duplicate SKU) and the database layer (`DatabaseError`) are surfaced inline via st.error without changes; successes route through a session-state "flash" message that survives the post-action rerun. Tests: Streamlit AppTest — creation persists with defaults and appears in the listing, duplicate-SKU and empty-name rejections with no partial writes, prefill, field updates (stock untouched), SKU conflict, deactivate confirmation gating, deactivate + listing exclusion, reactivate.

### TASK-018: Implement Inventory Display and Adjustments

- Priority: P0
- Status: Verified
- Dependencies: TASK-014, TASK-016

Description:

Display stock levels and implement approved inventory adjustments.

Evidence:

- Stock levels match persisted data.
- Adjustment behavior follows business rules.
- Relevant tests pass.

Completion record (2026-11-06): Stock levels shown in the listing (TASK-016) and in the "Adjust stock" tab with a `st.metric` current-stock display for the selected product. Two approved operations, exactly per DEC-047 ownership: "Add or remove units" (signed adjustment through `inventory_service.adjust_stock`; DEC-034 rejections — zero change, non-integer, negative result — surface as clear inline errors and leave stock unchanged) and "Set exact stock (correction)" with a warning that corrections overwrite the stored value (uses `set_stock_level`, documented for corrections only). The listing table in the same run reflects the new stock immediately. Tests: AppTest — add/remove units persist and display, over-removal rejected with the negative-stock message and unchanged stock, zero change rejected, exact-level correction works, metric shows current stock. See TASK-017/018 commit `14fad85`; full suite: 134 tests.

### TASK-019: Implement Low-Stock Indicators

- Priority: P1
- Status: Not Started
- Dependencies: TASK-018

Description:

Display low-stock indicators based on approved thresholds.

Evidence:

- Indicators follow the configured rules.
- Missing thresholds are handled appropriately.

---

## 9. Sales Management

### TASK-020: Implement Manual Sales Entry

- Priority: P0
- Status: Not Started
- Dependencies: TASK-015

Description:

Create the manual sales entry workflow.

Evidence:

- Valid sales can be recorded.
- Invalid quantities and product references are rejected.
- Approved inventory behavior is applied.

### TASK-021: Implement Sales History

- Priority: P0
- Status: Not Started
- Dependencies: TASK-020

Description:

Display stored sales records.

Evidence:

- Sales records are displayed correctly.
- Empty states are supported.
- Relevant filters work if included in the approved specification.

---

## 10. CSV Import

### TASK-022: Implement CSV File Validation

- Priority: P0
- Status: Not Started
- Dependencies: TASK-006, TASK-007

Description:

Validate CSV file structure and required columns.

Evidence:

- Valid files are accepted.
- Invalid files produce clear errors.
- Validation tests pass.

### TASK-023: Implement CSV Preview

- Priority: P1
- Status: Not Started
- Dependencies: TASK-022

Description:

Allow users to preview records before importing them.

Evidence:

- Preview data matches the uploaded file.
- Invalid rows are identifiable.

### TASK-024: Implement CSV Import Persistence

- Priority: P0
- Status: Not Started
- Dependencies: TASK-012, TASK-022, TASK-023

Description:

Persist accepted historical sales records according to the approved import rules.

Evidence:

- Accepted records are stored correctly.
- Duplicate behavior follows the approved policy.
- Historical imports do not unexpectedly modify current stock.

### TASK-025: Implement Import Summary

- Priority: P1
- Status: Not Started
- Dependencies: TASK-024

Description:

Display import results and relevant validation information.

Evidence:

- Imported and rejected record counts are accurate.
- Errors are understandable.

---

## 11. Forecasting and Machine Learning

### TASK-026: Perform Sales Data Exploration

- Priority: P0
- Status: Not Started
- Dependencies: TASK-005, TASK-008

Description:

Explore historical sales trends, distributions, and time coverage.

Evidence:

- Relevant patterns are documented.
- Data limitations are identified.

### TASK-027: Implement Baseline Forecasting

- Priority: P0
- Status: Not Started
- Dependencies: TASK-008, TASK-026

Description:

Implement simple forecasting baselines.

Evidence:

- Baseline predictions are generated.
- Chronological validation is used.
- Results are documented.

### TASK-028: Implement Feature Engineering

- Priority: P0
- Status: Not Started
- Dependencies: TASK-008, TASK-026

Description:

Implement the approved forecasting features.

Evidence:

- Date, lag, and rolling features are generated correctly.
- Target leakage checks pass.
- Feature tests pass.

### TASK-029: Implement Chronological Data Splitting

- Priority: P0
- Status: Not Started
- Dependencies: TASK-026, TASK-028

Description:

Implement time-aware training and evaluation splits.

Evidence:

- Training data precedes validation and test data.
- No future observations leak into training features.

### TASK-030: Train Candidate Models

- Priority: P0
- Status: Not Started
- Dependencies: TASK-027, TASK-028, TASK-029

Description:

Train and compare the proposed ML candidates.

Evidence:

- Candidate models train successfully.
- Training configuration is documented.
- Results are reproducible.

### TASK-031: Evaluate and Select the Forecasting Model

- Priority: P0
- Status: Not Started
- Dependencies: TASK-030

Description:

Evaluate candidate models using MAE and RMSE and compare them with the baseline.

Evidence:

- Evaluation results are recorded.
- Model selection has supporting evidence.
- Limitations are documented.

### TASK-032: Save Model and Metadata

- Priority: P0
- Status: Not Started
- Dependencies: TASK-031

Description:

Save the selected model and the metadata required for inference.

Evidence:

- Model artifact can be loaded.
- Metadata matches the trained model.
- Artifact version or training information is available where required.

### TASK-033: Implement Forecast Inference

- Priority: P0
- Status: Not Started
- Dependencies: TASK-032

Description:

Implement the forecasting service for supported products and forecast horizons.

Evidence:

- Predictions are generated correctly.
- Insufficient history is handled.
- Inference tests pass.
- Inventory remains unchanged.

---

## 12. Restocking Recommendations

### TASK-034: Confirm Restocking Parameters

- Priority: P0
- Status: Not Started
- Dependencies: TASK-001

Description:

Resolve the business decisions required for restocking calculations.

Potential parameters:

- Lead time.
- Safety stock.
- Target stock.
- Inventory position.

Evidence:

- Required parameters and formulas are approved.
- Missing decisions are documented.

### TASK-035: Implement Restocking Calculations

- Priority: P0
- Status: Not Started
- Dependencies: TASK-014, TASK-033, TASK-034

Description:

Implement the recommendation service.

Evidence:

- Calculations follow approved business rules.
- Missing inputs are handled.
- Unit tests pass.
- No inventory mutation occurs.

### TASK-036: Implement Recommendation Display

- Priority: P1
- Status: Not Started
- Dependencies: TASK-035

Description:

Display restocking recommendations in the appropriate application page.

Evidence:

- Recommendations are understandable.
- Supporting information is displayed.
- No automatic purchasing is triggered.

---

## 13. Dashboard and Analytics

### TASK-037: Implement Dashboard Metrics

- Priority: P1
- Status: Not Started
- Dependencies: TASK-013, TASK-014, TASK-015

Description:

Implement the approved dashboard metrics.

Evidence:

- Metrics use actual application data.
- Calculations are verified.
- Empty states are supported.

### TASK-038: Implement Sales Trend Visualization

- Priority: P1
- Status: Not Started
- Dependencies: TASK-015

Description:

Display sales trends using the selected charting approach.

Evidence:

- Aggregations are correct.
- Date filtering works where supported.

### TASK-039: Implement Low-Stock Overview

- Priority: P1
- Status: Not Started
- Dependencies: TASK-019

Description:

Display products that meet the approved low-stock conditions.

Evidence:

- Displayed products match the business rules.

### TASK-040: Implement Forecasting Interface

- Priority: P0
- Status: Not Started
- Dependencies: TASK-033

Description:

Build the AI Forecasting interface.

Evidence:

- Users can request supported forecasts.
- Predictions are displayed correctly.
- Errors and insufficient data are explained.

### TASK-041: Implement Sales Analytics Page

- Priority: P1
- Status: Not Started
- Dependencies: TASK-038

Description:

Build the Sales Analytics page.

Evidence:

- Supported analytics are displayed.
- Calculations match source data.

### TASK-042: Implement Actual vs Predicted Visualization

- Priority: P2
- Status: Not Started
- Dependencies: TASK-031, TASK-040

Description:

Compare actual historical sales with model predictions where meaningful evaluation data is available.

Evidence:

- Actual and predicted values are aligned correctly.
- The comparison does not mix training and evaluation results incorrectly.

### TASK-043: Implement Product Performance Analysis

- Priority: P2
- Status: Not Started
- Dependencies: TASK-026, TASK-041

Description:

Implement additional product-level performance insights.

Evidence:

- Metrics are clearly defined.
- Results are based on available data.

---

## 14. Integration and Quality

### TASK-044: Integrate Application Pages and Services

- Priority: P0
- Status: Not Started
- Dependencies: Core UI and service tasks

Description:

Connect all implemented pages to their corresponding application services.

Evidence:

- Core workflows work end to end.
- No major integration errors remain.

### TASK-045: Implement Application Error Handling

- Priority: P0
- Status: Not Started
- Dependencies: TASK-044

Description:

Review and improve error handling across the application.

Evidence:

- Expected errors are handled.
- Users receive understandable messages.
- Internal error details are not unnecessarily exposed.

### TASK-046: Run Automated Test Suite

- Priority: P0
- Status: Not Started
- Dependencies: Implemented core services

Description:

Run all relevant automated tests.

Evidence:

- Test results are recorded.
- Failures are fixed or documented.
- No tests are reported as passing without execution.

### TASK-047: Perform Manual Application Testing

- Priority: P0
- Status: Not Started
- Dependencies: TASK-044

Description:

Test the main user flows through the actual Streamlit interface.

Evidence:

- Core workflows are manually verified.
- Screens or notes are recorded where useful.
- Discovered issues are tracked.

### TASK-048: Review Documentation Consistency

- Priority: P0
- Status: Not Started
- Dependencies: Core implementation

Description:

Review documentation against actual implementation.

Evidence:

- Outdated instructions are corrected.
- Implemented behavior is documented.
- Open decisions and limitations remain visible.

---

## 15. Optional and Future Tasks

These tasks are not required for the initial core implementation.

### TASK-049: Export Reports

- Priority: P2
- Status: Not Started
- Dependencies: Relevant analytics features

Description:

Allow users to export selected reports.

### TASK-050: Supplier Management

- Priority: P3
- Status: Not Started
- Dependencies: Future scope approval

Description:

Introduce supplier information and related workflows.

### TASK-051: Multi-Branch Support

- Priority: P3
- Status: Not Started
- Dependencies: Future scope approval

Description:

Support multiple store locations.

### TASK-052: Purchase Order Management

- Priority: P3
- Status: Not Started
- Dependencies: Supplier management and future scope approval

Description:

Introduce purchase order workflows.

### TASK-053: Automated Reordering

- Priority: P3
- Status: Not Started
- Dependencies: Future scope approval

Description:

Explore automated purchasing workflows.

This task requires explicit approval and additional safety and business rules.

---

## 16. Task Management Rules

The AI Agent must:

1. Read a task's dependencies before starting it.
2. Avoid starting blocked tasks.
3. Update the task status when work progresses.
4. Record implementation evidence.
5. Run relevant tests before marking a task Tested.
6. Verify behavior against acceptance criteria before marking it Verified.
7. Record blockers instead of silently skipping them.
8. Avoid marking optional tasks as required.
9. Update this document when the task breakdown changes.

Do not mark tasks as completed simply because code has been generated.

---

## 17. Current Task Tracking

All tasks begin as:

`Not Started`

The actual status should be updated during implementation.

This document does not claim that any task has already been completed.