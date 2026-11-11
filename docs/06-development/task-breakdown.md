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
- Status: Verified
- Dependencies: TASK-018

Description:

Display low-stock indicators based on approved thresholds.

Evidence:

- Indicators follow the configured rules.
- Missing thresholds are handled appropriately.

Completion record (2026-11-06): Delivered with TASK-016/TASK-018 and finalized in the same phase. Rules: BR-008 classification (Out of Stock at zero; Low Stock at/below the DEC-032 reorder point; In Stock above), computed in `domain/inventory.py` and surfaced by `inventory_service.get_stock_overview()`. Indicators on the listing: per-row status marker (🟢/🟠/🔴 with status text), a reorder-point column, and a summary banner naming every non-In-Stock product's SKU and name. Missing thresholds handled: products with no sales and zero safety stock get a reorder point of 0 (zero stock → Out of Stock, any stock → In Stock) without errors, verified by domain and service tests. Suite: 134 tests.

---

## 9. Sales Management

### TASK-020: Implement Manual Sales Entry

- Priority: P0
- Status: Verified
- Dependencies: TASK-015

Description:

Create the manual sales entry workflow.

Evidence:

- Valid sales can be recorded.
- Invalid quantities and product references are rejected.
- Approved inventory behavior is applied.

Completion record (2026-11-07): "Record sale" tab in the new `src/smartstock/pages/sales.py` (registered in `app.py` navigation as Sales Management; shared UI helpers extracted to `src/smartstock/pages/ui.py` — the session-flash pattern used by both pages). Form: active-product selectbox with live stock in labels (DEC-050), current-stock `st.metric`, quantity (min 1), and a sale-date input defaulting to UTC today so defaults always pass DEC-051 (test discovered Streamlit's date widget clamps beyond ~+10 years; the service rejection is exercised with a near-future date). Submission routes through `sales_service.record_sale` — the atomic DEC-035/BR-012 transaction: success flash states quantities and remaining stock; `InsufficientStockError` surfaces the requested/available message inline with no sale row and unchanged stock (verified at UI level); `ValueError`/`DatabaseError` show unchanged. Backdated entries flow through the service as approved. Tests: AppTest — empty state, valid sale persists + stock reduces + history row appears, insufficient stock rejected atomically, future date rejected, inactive product unsellable, backdated allowed.

### TASK-021: Implement Sales History

- Priority: P0
- Status: Verified
- Dependencies: TASK-020

Description:

Display stored sales records.

Evidence:

- Sales records are displayed correctly.
- Empty states are supported.
- Relevant filters work if included in the approved specification.

Completion record (2026-11-07): "Sales history" tab on the same page: table of product label (name + SKU), quantity, sale date, and record creation time; totals caption (sales count and units). Filters per the approved spec: product filter (includes deactivated products so preserved records stay reviewable — DEC-048) and date-range filter with an "All time" default toggle; an out-of-order range warns and aborts. Empty states differentiate "nothing recorded yet" versus "no matches for current filters". Tests: AppTest — all-time display with labels and totals, product filter, date-window filter, no-match state, deactivated product remains visible in history. Full suite: 147 tests.

---

## 10. CSV Import

### TASK-022: Implement CSV File Validation

- Priority: P0
- Status: Verified
- Dependencies: TASK-006, TASK-007

Description:

Validate CSV file structure and required columns.

Evidence:

- Valid files are accepted.
- Invalid files produce clear errors.
- Validation tests pass.

Completion record (2026-11-07): `src/smartstock/domain/csv_import.py` — pure validation logic, no DB or UI dependencies. `read_csv_file` parses with string dtypes so malformed values become explicit row-level problems (file-level errors: empty data, unreadable text, malformed CSV → `CsvFileError`); `validate_file_structure` requires exactly the `date,store,item,sales` columns (missing or extra columns → `CsvStructureError`, so file meaning is never guessed). `analyze_rows` produces a `RowAnalysis` report: rejected rows with per-row reasons (invalid/impossible dates via strict `%Y-%m-%d`, non-integer or negative stores/items, fractional/negative sales, missing values), out-of-scope rows for other stores counted per DEC-015 (skipped, not errors), within-file duplicate `(item, date)` pairs skipped keeping first occurrence, zero sales accepted (dataset's real observation), accepted rows normalized to storage types with date range. Row-level problems are a report rather than exceptions because DEC-054 validates the whole file before any write. Verified on real dataset rows: 5,000-row slice classified correctly (stores 2–3 out of scope, 1,826 valid store-1 rows, full 2013–2017 range); suite 171 tests.

### TASK-023: Implement CSV Preview

- Priority: P1
- Status: Verified
- Dependencies: TASK-022

Description:

Allow users to preview records before importing them.

Evidence:

- Preview data matches the uploaded file.
- Invalid rows are identifiable.

Completion record (2026-11-07): service `src/smartstock/services/import_service.py` (`preview_import`) builds a spec §8 preview: filename, byte size, and the SHA-256 fingerprint that persistence will verify (computed over raw bytes, so a renamed identical file has the same fingerprint — DEC-053); row-count metrics (total, valid for store 1, rejected invalid, other stores per DEC-015, in-scope), full rejected/duplicate totals with at most 5 example reasons each (spec §13 "summarize, don't dump everything" — truncation flagged), accepted-rows date range, and up to 5 sample rows. Uploaded streams are seek()-reset after reading so persistence can re-read the same file. Page `src/smartstock/pages/imports.py` (registered in `app.py` → Data → Data Import, unique `url_path`): file uploader restricted to `.csv`, metric row for the counts, date-range/duplicates caption, capped example expanders for rejected rows and within-file duplicates, sample table, and explicit empty states ("nothing to import" when no valid store-1 rows; file-level/column-level errors from TASK-022 surface as `st.error` without partial previews). Import confirmation and results arrive with TASK-024/025. Tests: service tests (summary fields, fingerprint determinism across renamed copies, example capping with full counts, stream re-readability) and AppTest page tests (empty state, metrics + sample, rejection reasons, both error layers, no-scope warning, fingerprint caption); suite 187 tests.

### TASK-024: Implement CSV Import Persistence

- Priority: P0
- Status: Verified
- Dependencies: TASK-012, TASK-022, TASK-023

Description:

Persist accepted historical sales records according to the approved import rules.

Evidence:

- Accepted records are stored correctly.
- Duplicate behavior follows the approved policy.
- Historical imports do not unexpectedly modify current stock.

Completion record (2026-11-07): schema adds two tables to `database/schema.sql` (+ `schema.py` verification lists): `import_batches` (per-run metadata with UNIQUE `file_sha256`, row-count audit fields, accepted date range) and `historical_sales` (dataset-keyed `item` > 0, `sale_date`, `quantity` CHECK ≥ 0 accepting the dataset's zero-sales observations, FK `import_batches`, UNIQUE (`item`, `sale_date`) — DEC-052/053). New `src/smartstock/repositories/historical_repository.py`: `create_import_batch` runs fingerprint check → skip rows already stored by other batches (counted) → batch insert → bulk row insert, one transaction, `commit` flag like the other repos; `DuplicateImportError(ValueError)` carries the original batch's id/filename/timestamp; plus `find_batch_by_fingerprint`, `get_import_batches`, `count_historical_rows`. Service `execute_import` re-parses and re-validates the file's current bytes right before writing (a stale preview can never be imported), calls `initialize_database` idempotently so pre-DEC-052 databases gain the tables in place, rejects zero-importable files (`ImportRejectedError`), and returns a spec §14-backed `ImportResult`. Page: labeled confirm button ("Import N record(s)") → success flash with batch id; duplicate upload surfaces the DEC-053 message; `DatabaseError` shows "failed and nothing was stored". Inventory and operational sales are never touched by import code paths (BR-014/DEC-016 — tests assert `count_historical_rows` but no sales/stock mutations exist in the module). Tests: 12 persistence tests — batch/rows stored, fingerprint rejection unchanged-DB, overlapping-file merge with skip counting, CHECK-violation rollback leaves zero rows, legacy-schema DB upgrade, service counts, page confirm/re-duplicate/no-button flows; suite 199 tests. Real `data/smartstock.db` re-initialized on boot: tables added, products data preserved (verified manually).

### TASK-025: Implement Import Summary

- Priority: P1
- Status: Verified
- Dependencies: TASK-024

Description:

Display import results and relevant validation information.

Evidence:

- Imported and rejected record counts are accurate.
- Errors are understandable.

Completion record (2026-11-07): `pages/imports.py` result panel per CSV Import Specification §14 — after the file's batch commits, it shows a success banner with batch id and UTC timestamp, outcome metrics ("Accepted and stored", "Rejected (invalid)", "Duplicates skipped", "Other stores"), and a caption with import type (historical, store), filename, total rows processed, accepted date range, and the stock-unchanged note; the confirm button is replaced for that file (same-session re-imports are impossible — uploading a different file restarts the flow; a fresh session re-uploading the same bytes hits the DEC-053 fingerprint rejection with the original-batch message, tested). "Previous imports" expander lists every batch newest-first (file, imported/duplicate/rejected/out-of-scope counts, date range, UTC timestamp) with the total stored-records caption and an empty state; service `get_import_summary` wraps the repository read (idempotent initialization first so pre-import databases don't break the page). Success reporting reflects actual database outcome only (spec: "must not claim records were imported if the transaction failed" — failures render the `DatabaseError` message instead). Tests: 6 summary tests (panel replaces button, timestamp/range notes, history table accuracy, new-file restart, empty history, service counts); suite 205 tests.

---

## 11. Forecasting and Machine Learning

### TASK-026: Perform Sales Data Exploration

- Priority: P0
- Status: Verified
- Dependencies: TASK-005, TASK-008

Description:

Explore historical sales trends, distributions, and time coverage.

Evidence:

- Relevant patterns are documented.
- Data limitations are identified.

Completion record (2026-11-09): `src/smartstock/ml/exploration.py` — pure pandas view functions (overview, distribution, weekday/monthly patterns, yearly totals, per-item lag correlations, item summary) returning JSON-serializable values, plus `summarize_series` composing the full report. Correlation lags shift within each item's series (no cross-item row-neighbor leakage). Findings recorded in the new `docs/04-machine-learning/data-exploration.md` with **measured** store-1 facts: complete coverage (50 items × 1,826 days, zero missing, zero zero-sales days — the dataset's single zero-sale row is in another store), pooled mean 47.27/std 24.01 with a right tail to 155, strong weekday ramp (Mon 37.47 → Sun 56.27, ≈ +50%), July peak / January trough (μ ≈ 89% spread), steady year-over-year growth (+15.2%, +4.2%, +8.5%, +3.9% in daily means; 2013→2017 +35%), and lag-7 dominance in correlations (0.908 vs. lag-1 0.852, lag-30 0.793). Limitations documented: no zero-demand days (stockouts invisible), no covariates (price/promos/holidays), competition-source regularity, single store per DEC-015. Implications for next tasks: lag-7/weekday/rolling-7 features carry the signal, trend-aware baselines needed (a five-year mean under-forecasts), chronological splits must live in later years. Tests: 17 exploration tests — synthetic frames with hand-computed expectations + `TestRealDataset` pinning every documented number to code (suite 222).

### TASK-027: Implement Baseline Forecasting

- Priority: P0
- Status: Verified
- Dependencies: TASK-008, TASK-026

Description:

Implement simple forecasting baselines.

Evidence:

- Baseline predictions are generated.
- Chronological validation is used.
- Results are documented.

Completion record (2026-11-09): `src/smartstock/ml/baselines.py` — `naive_forecast` (§3.1 repeat-latest) and `moving_average_forecast` (§3.2 trailing-window mean, forgiving of short histories), plus `_evaluate_one_step_ahead`: a leak-free walk-forward evaluator that for each (item, day) in the validation window predicts from actuals available strictly before that day, refuses incomplete day coverage or reversed windows or history-less items, and reports pooled MAE/RMSE + prediction count (`BaselineReport`). Chronological split fixed as **DEC-056** with the project owner (Train 2013–2015, Validation 2016, Test 2017 — test never touched in this task). Measured results (`docs/04-machine-learning/baseline-evaluation.md`, 2016 window, 18,300 predictions): naive MAE 10.270/RMSE 13.761; trailing-7 mean MAE **8.077**/RMSE 10.556 — beating the 30-day mean (8.298/10.915), which resolves the §3.2 window question in favor of 7 days, consistent with the lag-7 exploration finding. These are the DEC-027 floors for supervised candidates. Tests: 17 baseline tests (hand-computed ramp/flat errors, window-1-convenience equivalence-to-naive, explicit no-future-leakage spy, coverage/gap/history guards, multi-item pooling, real-window numbers pinned); suite 239.

### TASK-028: Implement Feature Engineering

- Priority: P0
- Status: Verified
- Dependencies: TASK-008, TASK-026

Description:

Implement the approved forecasting features.

Evidence:

- Date, lag, and rolling features are generated correctly.
- Target leakage checks pass.
- Feature tests pass.

Completion record (2026-11-09): `src/smartstock/ml/features.py` per feature-engineering.md §2–§9 — `build_features` over the preprocessed frame: calendar features (`day_of_week` 0=Monday via `Series.dt.day_of_week`, `month`, `day_of_month`), lags `lag_1`/`lag_7` shifted within each (store, item) series after chronological sort, and `rolling_mean_7`/`rolling_mean_30` computed on `sales.shift(1)` (min_periods = window) so the current target never enters its own features (§6/§10). `FEATURE_COLUMNS` fixed order `[day_of_week, month, day_of_month, lag_1, lag_7, rolling_mean_7, rolling_mean_30]` (§9); no arbitrary missing-value fills (§8) — `drop_rows_without_features` lets training explicitly keep complete rows only (a series needs 31 observed days: first complete row is observation index 30), and `feature_matrix` returns the (X, y) split with the target excluded. Real-dataset pin: 91,300 rows in, 89,800 complete training rows (50 items × 1,796), verified no-leakage property (2016-12-31's lag_1 equals every item's 2016-12-30 actual sales) and a hand-checked row (item 1, 2013-02-01: lag_1 = 01-31 sales, lag_7 = 01-25 sales, rolling_mean_7 = mean of 01-25..01-31). §14 open items remaining: identifiers-as-features (decided with model choice at TASK-031), extra calendar features, lag_14/lag_30, rolling std/median, final feature selection (may be evaluated at TASK-030/031 with DEC-027 evidence); minimum-history is now measured (31 days) and will be revisited for inference-time policy at TASK-033. Tests: 23 feature tests (synthetic hand-computed ramps, interleaved series cross-item-bug guards, outlier-target-exclusion proof, NaN-preserving comparisons, matrix shapes/order; real-dataset pins); suite 262.

### TASK-029: Implement Chronological Data Splitting

- Priority: P0
- Status: Verified
- Dependencies: TASK-026, TASK-028

Description:

Implement time-aware training and evaluation splits.

Evidence:

- Training data precedes validation and test data.
- No future observations leak into training features.

Completion record (2026-11-09): `src/smartstock/ml/splits.py` turns DEC-056 into reusable code — `chronological_split(frame)` with the calendar constants as module defaults (`TRAIN_*` 2013-01-01→2015-12-31, `VALIDATION_*` 2016, `TEST_*` 2017, inclusive bounds), returning chronologically sorted (train, validation, test) frames with fresh indexes while leaving the input untouched. Guards (`SplitError`): empty frames and missing columns; boundary tuples that do not strictly increase (so windows can never overlap or reverse); windows selecting no rows; and rows falling outside every window are refused rather than silently dropped. The chronological non-leakage property (train.max < validation.min < test bounds) is asserted inside the function and by tests on the real data. Real-dataset pins: train 54,750 rows (50 × 1,095 days), validation 18,300 (leap year), test 18,250, all 50 items present in each window, exact window edge dates (2015-12-31 / 2016-01-01 → 2016-12-31 / 2017-01-01 → 2017-12-31). Tests: 13 split tests (synthetic window selection incl. multi-item counts, fresh index/sorting, input-untouched check, and every guard; real DEC-056 row/window assertions); suite 275. TASK-030 candidates will consume these three frames — features built per frame (TASK-028) keep training-time transformations inside the training window only.

### TASK-030: Train Candidate Models

- Priority: P0
- Status: Verified
- Dependencies: TASK-027, TASK-028, TASK-029

Description:

Train and compare the proposed ML candidates.

Evidence:

- Candidate models train successfully.
- Training configuration is documented.
- Results are reproducible.

Completion record (2026-11-09): `src/smartstock/ml/training.py` — `default_candidates()` (Linear Regression; Random Forest n_estimators=200, min_samples_leaf=5, n_jobs=-1, random_state=2026 — conservative, no hyperparameter search per model-training §7/§8), `Candidate`/`CandidateReport`/`CandidateComparison` (to_dict reports, `candidates_beat_baselines()` DEC-027 gate), and `evaluate_candidates(frame)` with DEC-056 window defaults (custom bounds only for tests). **Protocol fix found and corrected during this task**: a first version built features inside each split part, which silently dropped January 2016 (rolling_mean_30 needs 30 past observations *within the part*) and scored only 16,800 predictions — unlike-for-like against the baselines' 18,300. Corrected to build features on the full chronology (per-row deterministic transforms, no fitted state → no leakage path; fitting uses training rows only; leakage protocol documented in the module and pinned by real-data tests). Measured results on validation 2016 (`docs/04-machine-learning/model-evaluation.md` §17): Linear Regression MAE 6.482/RMSE 8.387; Random Forest MAE 6.033/RMSE 7.785 — **both beat both baselines** (naive 10.270, MA-7 8.077). Worst item is 15 for both (9.914 / 9.349 MAE — the highest-mean-demand item). RF edges LR by ≈7.4% — beyond DEC-027's 5% simpler-preference band → RF favored on validation evidence; final selection (TASK-031) with the owner, weighing interpretability and DEC-025 recursive stability. Reproducibility pinned (fixed seed; parallel float summation ≈1e-15 tolerance). Tests: 16 training tests (synthetic learnable-series workflow, like-for-like baseline window counts, custom bound guards, no-candidates/outside-window rejection, seed reproducibility; real-dataset measured-number pins); suite 291.

### TASK-031: Evaluate and Select the Forecasting Model

- Priority: P0
- Status: Verified
- Dependencies: TASK-030

Description:

Evaluate candidate models using MAE and RMSE and compare them with the baseline.

Evidence:

- Evaluation results are recorded.
- Model selection has supporting evidence.
- Limitations are documented.

Completion record (2026-11-09): selection made by applying the pre-accepted DEC-027 rules to the measured TASK-030 evidence — **Random Forest selected as the final demand-forecasting model (DEC-057)**: lowest validation MAE (6.033 vs LR 6.482), both candidates beat both baselines (rule 2), RMSE agrees as tie-breaker would (rule 3 not needed), and rule 4's 5% simpler-preference band is NOT triggered (LR ≈7.4% worse). The once-untouched test window (2017) was then evaluated exactly once per DEC-056 — new `training.evaluate_on_test` fitting on all pre-2017 actuals and scoring 18,250 item-days: Random Forest MAE 6.088/RMSE 7.910 (LR 6.637/8.611; reference baselines naive 10.512, MA-7 8.378) — confirming the selection, changing nothing. Recorded: DEC-057 + summary table row; `model-evaluation.md` §18 (test confirmation, limitations cross-referenced: no-leakage protocol, single store, untested multi-step behavior — recursive-horizon error accumulation under DEC-025 is measured at TASK-033); forecasting-strategy open item "final forecasting model" closed (rounding policy and no-history handling remain, resolved at TASK-033 with user options). Interpretability trade-off documented: feature importances to be surfaced at TASK-032/033 for educational transparency. Tests: expanded training suite with `TestRealTestWindow` pins (23 training tests); suite 298. No decision requiring user approval: DEC-027 application was autonomous by design (user checkpoint reserved for a within-5% tie or baseline failure; neither occurred).

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

Completion record (2026-11-09): `src/smartstock/ml/model_artifacts.py` + `scripts/train_model.py` per model-training §11/§12/§14. `build_metadata` assembles the full §11 contract (model name/version, UTC training timestamp, dataset reference, enforced `FEATURE_COLUMNS` feature names with load-time verification against the feature pipeline, training configuration incl. row count, evaluation metrics, forecasting granularity incl. DEC-025 recursive flag and DEC-026 horizons 7/14/30 with default 7). `save_model_artifact` is atomic (§14): temp files → joblib dump → reload-and-verify (attrs + a sample predict) → `os.replace` — a failed run can never replace a previously valid artifact; stray temp files always cleaned. `load_model_artifact` validates the metadata contract and raises `ArtifactError` with clear guidance when absent ("run scripts/train_model.py"; artifacts are git-ignored runtime data). The training script runs the documented workflow: preprocess store 1 → evaluate candidates on DEC-056 validation (measured, matching the pinned numbers exactly) → one-time test-window confirmation (a training/retraining run is a checkpoint, not a tuning loop) → fit the production model on **all complete observed-history rows (89,800)** since inference forecasts the future → atomic save with printed report. Decision made autonomously (artifact fit scope): the shipped artifact trains on all observed actuals; the metadata keeps selection metrics from the DEC-056 protocol runs separate from the artifact's fit scope. Real artifact in place: 250MB `demand_model.joblib` (git-ignored by the existing `*.joblib` rule) + committed `model_metadata.json`. Tests: 16 artifact tests (metadata contract, atomic save/load roundtrip, §14 failure handling incl. corrupt files and previous-artifact preservation) + 2 real-artifact pins (skips when not generated); suite 314.

### TASK-033: Implement Forecast Inference

- Priority: P0
- Status: Verified
- Dependencies: TASK-032

Description:

Implement the forecasting service for supported products and forecast horizons.

Evidence:

- Predictions are generated correctly.
- Insufficient history is handled.
- Inference tests pass.
- Inventory remains unchanged.

Completion record (2026-11-10): `src/smartstock/ml/inference.py` implements the prediction-logic workflow as pure functions: `forecast_product(model, metadata, history, horizon_days, product_id)` validates the DEC-026 horizon (7/14/30), required history columns, numeric non-negative sales, and one-observation-per-day (duplicates rejected with multi-record-day guidance; input is sorted internally), then walks the §8 recursive loop — each day's prediction joins a per-call working history before the next day's features are recomputed (never touching operational sales records). **DEC-058 accepted with the owner**: ≥31 observed days → Random Forest path (calendar + lag_1/lag_7 + trailing 7/30 means computed observation-wise, exactly matching training feature math); 1→30 days → MA-7 fallback applied recursively with predictions in the trailing window (strongest measured baseline, MAE 8.077); 0 days → explicit "No suitable history exists" error (§13). Output: DataFrame per §9 (product_id, forecast_date, predicted_demand, model_used, model_version from artifact metadata, generated_at UTC). Policies per doc language: raw predictions preserved with clipping to ≥0 documented (§10; RF is structurally non-negative anyway) and no rounding in this layer (§11 — the business layer rounds at restocking). Model-path verification includes a manual §8-loop replica test (inference consumes its own predictions, hand-computed features) and a constant-series pin (forest trained on constant data predicts the constant exactly). Tests: 20 inference tests (validation guards incl. horizon/duplicates/negatives, output contract, DEC-058 path selection incl. 20-day real-history fallback, negative-clipping stub, non-finite rejection, determinism, real-artifact pins: item 1 forecasts 2018-01-01→07 with the model path post-training-history); suite 334. Inventory untouched by design (§12) — restocking integration is TASK-034+.

---

## 12. Restocking Recommendations

### TASK-034: Confirm Restocking Parameters

- Priority: P0
- Status: Verified
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

Completion record (2026-11-10): the parameter set is fully approved and every documentation status reconciled with the decision records. Confirmed with the project owner: **DEC-033 Recommended Order Quantity = max(0, Target Stock − Inventory Position)** (the only formula still formally Proposed — the clamp keeps a nonnegative actionable quantity and "0 = no need to order"; signed-difference and extra-buffer variants rejected, the latter because DEC-038's Target Stock already contains the lead-time and 7-day buffers). Resolution of DEC-038's "minimum required history": a recommendation needs **at least one observed day** of history for Average Daily Demand (mean over the most recent 30 available days); 0 days → unavailable with a clear explanation — consistent with DEC-058's shortfall policy. Status grammar reconciled in `business-rules.md`: BR-018 invalid predictions (non-finite → error, negatives clipped, TASK-033), BR-019 forecast availability (DEC-058), BR-020 reorder point (DEC-032), BR-023 order quantity (DEC-033), BR-025 advisory (DEC-031) — all now Accepted. Inputs: Lead Time (DEC-037, manual, default 3), Safety Stock (DEC-036, manual, default 0), Inventory Position = current stock (BR-022/DEC-031). No code changes: TASK-034 is the documentation-confirmation checkpoint; implementation is TASK-035. Suite unchanged at 334 (run to confirm).

### TASK-035: Implement Restocking Calculations

- Priority: P0
- Status: Verified
- Dependencies: TASK-014, TASK-033, TASK-034

Description:

Implement the recommendation service.

Evidence:

- Calculations follow approved business rules.
- Missing inputs are handled.
- Unit tests pass.
- No inventory mutation occurs.

Completion record (2026-11-10): **DEC-059 accepted with the owner** — Average Daily Demand is a calendar-window mean ending at the product's last recorded sale date, zeros filled, denominator min(30 days, history span); closes the DEC-038 ambiguity. Implementation across the 5 layers: `domain/inventory.py` re-anchored to DEC-059 (`calculate_average_daily_demand` without a today parameter, window = max(first sale, end − window_days + 1) … last sale with an inclusive zero-filled walk; `demand_window_days_used` reports the real denominator), plus the confirmed formulas `calculate_target_stock` (ceil(demand) × (lead + 7) + safety, DEC-038) and `calculate_recommended_order_quantity` (max(0, target − current), DEC-033) sharing a `_validated_demand_inputs` guard with `calculate_reorder_point` (identical error messages preserved); `domain/restocking.py` composes BR-020/022/023/024 into a `RestockRecommendation` dataclass with explicit `available`/`unavailable_reason` semantics (no sales history or missing stock level → unavailable with a plain explanation, known fields like current stock still shown — never silent zeros; explanations cite DEC-032/033/038/031 and DEC-059); `sales_repository.get_first_sale_date` (MIN(sale_date)) enables full-history fetches; `inventory_service.get_stock_overview` now fetches each product's full observed history (first sale date → UTC today) instead of a today-anchored pre-window — page contract unchanged (`average_daily_demand` rounded to 4, `reorder_point`, `stock_status`); new read-only `services/restock_service.py::get_restock_recommendations` follows the `_run`/repositories pattern, active products only, rounds demand in the display layer (prediction-logic §11), never mutates inventory (DEC-031). Tests: 41 domain tests (DEC-059 anchoring incl. lone-sale span-1, gap zero-fill, 30-day cap, edge inclusivity, zero-quantity-sale scenario proven impossible and removed; the 2 new formula classes incl. ceil-before-multiply and clamp behavior; composition class with all hand-computed values); 4 service tests (unavailable path, full formulas on a 20-stock product — ADD 2.4 → reorder 14/target 38/order 30, read-only double-call invariance, inactive exclusion); `test_services.py` overview pins repinned to DEC-059 (sale of 8 today → demand 8.0, reorder 42; lone backdated sale → demand 5.0, reorder 27, Low Stock — test renamed to `test_backdated_sale_anchors_the_demand_window`). Suite 361/361 passed (was 334).

### TASK-036: Implement Recommendation Display

- Priority: P1
- Status: Verified
- Dependencies: TASK-035

Description:

Display restocking recommendations in the appropriate application page.

Evidence:

- Recommendations are understandable.
- Supporting information is displayed.
- No automatic purchasing is triggered.

Completion record (2026-11-10): new `src/smartstock/pages/restock.py`, registered in `app.py` navigation under Inventory as "Restocking Recommendations" (unique url_path `restocking-recommendations`). The page calls `restock_service.get_restock_recommendations()` only — no SQL, no business rules, rendering only (`DatabaseError` displayed, never raised). Composition: three summary metrics (needing reorder / recommendations available / without enough data), a "🛒 Consider restocking" table with every supporting input per user-flows §11 (name, SKU, current stock, ADD with 2-decimal format, lead time, safety stock, reorder point, target stock, order quantity) — supported by adding `lead_time_days`/`safety_stock` to the `RestockRecommendation` dataclass — plus one expander per attention product carrying the formula walk-through explanation from the domain layer (DEC-032/033/038/059/031 references), felt as understandable plain text. Unavailable products get a dedicated "ℹ️ Not available yet" section showing the domain's plain-language reasons (no sales history / no stock level), never hidden rows. States: no active products → info with pointer to Products & Inventory; nothing needs reorder → success banner. Advisory-only enforced everywhere (DEC-031): no purchase action, no stock mutation — verified by a test that re-reads stock after rendering. Tests: 6 new AppTest tests (empty state, table values + metrics + subheader with hand-computed pins — stock 12 after a sale of 8 from 20, ADD 8.0, reorder 42, target 98, order 86 —, success state, unavailable reason, read-only side-effect check) + an app.py startup test proving the navigation registers all five page modules; suite 367/367 passed. Metric values surface as strings in AppTest (documented quirk in test comments).

---

## 13. Dashboard and Analytics

### TASK-037: Implement Dashboard Metrics

- Priority: P1
- Status: Verified
- Dependencies: TASK-013, TASK-014, TASK-015

Description:

Implement the approved dashboard metrics.

Evidence:

- Metrics use actual application data.
- Calculations are verified.
- Empty states are supported.

Completion record (2026-11-10/11): **DEC-061 accepted with the owner** — six metric groups: active products, total stock, products needing reorder (BR-022 via restocking recommendations; products without history not counted), recent sales (units + sale count, last 7 days ending today UTC), top 3 sellers of the last 30 days (fixed window), and a forecast-readiness line (linked dataset items per DEC-060 out of active products). The "live forecast highlights" candidate was deferred: N model predictions per dashboard visit for a summary line is poor value when the Demand Forecast page owns that workflow. Implementation: `sales_repository.get_sales_window_summary` (COUNT + SUM in one query) and `get_top_products` (GROUP BY … ORDER BY units DESC, LIMIT with product JOIN); `sales_service` wrappers (`get_sales_window_summary`, `get_top_sellers`, `get_daily_totals` merging per-product daily aggregates); new `services/dashboard_service.py::get_dashboard_data` composing the services only (no SQL, no rules; windows: week = today−6…today, month = today−29…today; top sellers stay on the 30-day window regardless of the trend selection); page `pages/dashboard.py` with two metric rows, trend chart, top-sellers table, low-stock overview (TASK-039), forecast-readiness line, and full empty states. Tests: 10 service tests (empty state, product-only state, window inclusivity hand-computed — today back to 6 days ago is the 7-day window — ranking, breach counting incl. the DEC-059 span-1 lesson, trend totals, fixed top-seller window under a 7-day trend, forecast readiness, trend_days validation) + 5 page AppTest tests. Suite 398/398.

### TASK-038: Implement Sales Trend Visualization

- Priority: P1
- Status: Verified
- Dependencies: TASK-015

Description:

Display sales trends using the selected charting approach.

Evidence:

- Aggregations are correct.
- Date filtering works where supported.

Completion record (2026-11-10/11): charting approach is **Streamlit's built-in `st.line_chart`** (no new dependency, consistent with the dependency rules); trend data comes from `sales_service.get_daily_totals(start, end)` (merged per-product daily aggregates, verified at repository level previously and service level now). The dashboard offers a 7/30-day radio selector — date filtering is exercised by a service test (29-days-ago sale present in the 30-day trend, absent from the 7-day trend) and the page keeps the radio functional (AppTest radio set_value run without exceptions). Days without sales are absent from the series (preprocessing policy); an empty window shows an info state. Chart element verified in AppTest as a `vega_lite_chart` element. Suite 398/398.

### TASK-039: Implement Low-Stock Overview

- Priority: P1
- Status: Verified
- Dependencies: TASK-019

Description:

Display products that meet the approved low-stock conditions.

Evidence:

- Displayed products match the business rules.

Completion record (2026-11-10/11): the dashboard's low-stock overview lists every active product whose BR-008 status is Out of Stock or Low Stock (current stock at or below the reorder point), sourced from the restocking recommendations (DEC-032 reorder points, DEC-059 demand) — no duplicated business rules in the page. Warning banner counts the breaches; the table shows stock, average daily demand, reorder point, and the advisory suggested order (DEC-033), with a DEC-031 advisory caption pointing to the Restocking Recommendations page. Verified by a service test (breach list matches hand-computed reorder points, safe product excluded) and a page test (breach appears, calm product absent). Suite 398/398.

### TASK-040: Implement Forecasting Interface

- Priority: P0
- Status: Verified
- Dependencies: TASK-033

Description:

Build the AI Forecasting interface.

Evidence:

- Users can request supported forecasts.
- Predictions are displayed correctly.
- Errors and insufficient data are explained.

Completion record (2026-11-10): **DEC-060 accepted with the owner** — products gain a nullable `dataset_item_id`; the Forecast page is product-driven and consumes the linked dataset item's imported `historical_sales` series only (operational sales not mixed in v1; in-span gaps zero-filled so the inference module sees one observation per day — DEC-058 "observed days" = calendar days of the item's span). Layers: `database/schema.sql` adds the column with a CHECK; `initialization.py` gains a guarded, idempotent `ALTER TABLE` migration for pre-DEC-060 databases (applied to the real dev DB non-destructively, rows verified intact; legacy-DB test added); `schema.py` EXPECTED_COLUMNS contract updated; `product_repository.create_product/update_product` support link/unlink via a sentinel (None = unlink, unset = unchanged; validation "positive integer or empty") with lifecycle + validation repository tests; `product_service.create_product` passes the link through; `historical_repository.get_daily_sales_for_item` (grouped per-day totals); new `services/forecast_service.py::get_forecast(product_id, horizon, db_path, model=None, metadata=None)` — link gate (`ProductNotLinkError`), no-history gate ("No suitable history exists", §13), artifact load (clear "run scripts/train_model.py" ArtifactError), zero-fill, inference call, display rounding to 3 decimals (§11), model stub hook for tests; new `pages/forecast.py` (product selectbox, 7/14/30 horizon radio, generate button → total/average/item metrics, forecast table, method caption distinguishing RF vs MA-7 fallback per DEC-058; unlinked → guidance info; no history → info; missing artifact → warning; ForecastError → info; read-only); registered in `app.py` navigation ("Forecasting" group, url_path `demand-forecast`). Tests: 9 service tests (gates, zero-fill recursion hand-math, stub model path, missing artifact, real-artifact/real-import pin: item 1 → 7 rows starting 2018-01-01, model path, 1,826 observed days), 4 page AppTest tests, 2 repository link tests, 1 migration test; suite 383/383 passed.

### TASK-041: Implement Sales Analytics Page

- Priority: P1
- Status: Verified
- Dependencies: TASK-038

Description:

Build the Sales Analytics page.

Evidence:

- Supported analytics are displayed.
- Calculations match source data.

Completion record (2026-11-10/11): new `pages/analytics.py` registered under Sales (url_path `sales-analytics`), quantity-based per F-006 v1 (no revenue analytics — the app stores no prices; caption states this). Inputs: date range (date inputs, end capped at UTC today, default last 30 days) and an optional product filter. Metrics: units sold, sale count, average units/day over **all** days in the range (zeros included, DEC-059's calendar-day view), and days with sales. Sections: daily units trend (`st.line_chart`), weekday pattern (`st.bar_chart`, average per weekday over the full range with zero days included), sales-by-product ranking with per-product share of units (best seller first), and monthly totals. Layers: `sales_repository.get_product_sales_summary` (per-product units + sale counts in one grouped query) with a `sales_service` wrapper; new `services/analytics_service.py::get_sales_analytics(start, end, product_id, db_path)` composing existing sales services with range validation (ISO dates, inverted range rejected) and zero-filled weekday averaging. Empty states: no products guidance, no sales in range. Tests: 9 service tests (totals/sale-count arithmetic hand-computed — 38 units in 4 sales, share 35/38, month split 33/5, mirrored weekday computation, product filter narrowing everything, inverted-range and date-format rejection, empty-range zeros) + 2 page AppTest tests (empty DB, full render with both charts, ranking and monthly tables; date widgets set via AppTest — the default 30-day range shows zeros for out-of-window data, which the test exercises deliberately). Suite 409/409.

### TASK-042: Implement Actual vs Predicted Visualization

- Priority: P2
- Status: Verified
- Dependencies: TASK-031, TASK-040

Description:

Compare actual historical sales with model predictions where meaningful evaluation data is available.

Evidence:

- Actual and predicted values are aligned correctly.
- The comparison does not mix training and evaluation results incorrectly.

Completion record (2026-11-11): **DEC-062 accepted with the owner** — the comparison is the stored, training-time evaluation metrics only (no new predictions; DEC-056's one-touch test window stays intact). Implementation: `model_artifacts.load_model_metadata` (metadata-only loader, contract-validated, now also type-checking `evaluation_metrics`); new `services/evaluation_service.py::get_evaluation_summary` formatting the stored windows (validation first, then the labeled test window) and baselines; new "📐 How accurate is the model?" section on `pages/forecast.py` (window MAE metrics with RMSE/prediction-count help text, baseline-context caption, model/version/training-date caption, missing-artifact guidance info; renders even with no products). The task's evidence is met by construction: the displayed numbers come from the recorded evaluation runs (validation 2016 / test 2017) and no training-window data is presented as evaluation — the DEC-056 labeling makes the window provenance explicit. Tests: 6 service tests (stored numbers surfaced faithfully, optional sections omitted, missing/unreadable/contract-invalid artifacts, real-artifact pin: validation MAE 6.033 < test MAE 6.088 < baselines 10.27/8.077 per DEC-027) + 3 page AppTest tests (stored metrics displayed incl. "MAE 6.088" and DEC-056 window labeling, missing-artifact notice, section renders without products). Suite 418/418.

### TASK-043: Implement Product Performance Analysis

- Priority: P2
- Status: Verified
- Dependencies: TASK-026, TASK-041

Description:

Implement additional product-level performance insights.

Evidence:

- Metrics are clearly defined.
- Results are based on available data.

Completion record (2026-11-11): new `analytics_service.get_product_performance(start, end, product_id, db_path)` with clearly defined, documented metrics per F-011: units sold, sale count, average units/day over the range's calendar days (zeros included, DEC-059 view), first/last sale dates in the range, and a **trend direction** comparing the two calendar halves of the range (odd extra day joins the second half; zeros count — quiet first half with second-half sales = "Rising (new)", sales only in the first half = "Falling (stopped)"; ratio ≥ 1.15 → Rising, ≤ 0.85 → Falling, else Steady; single-day range → Steady). Sales layer gained the `sales_service.get_daily_sales_by_product` wrapper. Page: "🔎 Product performance" section on the Sales Analytics page (respects the product filter), with an honest caption that stock-warning frequency is **not tracked in v1** — warnings are advisory snapshots, not logged events, so that F-011 indicator has no valid data source yet (the "interpretation must be based on valid data" requirement applied honestly). Highest/lowest-selling products are already covered by the ranking table above it. Tests: 6 new service tests (row arithmetic hand-computed: 35 units / 59 days, Rising 5× ratio, Falling 0.16 ratio, Steady 1.0, stopped/single-day cases, filter and absent-product behavior) + page test extended to the new table (trend labels, first/last sale dates). Suite 424/424.

---

## 14. Integration and Quality

### TASK-044: Integrate Application Pages and Services

- Priority: P0
- Status: Verified
- Dependencies: Core UI and service tasks

Description:

Connect all implemented pages to their corresponding application services.

Evidence:

- Core workflows work end to end.
- No major integration errors remain.

Completion record (2026-11-11): new `tests/integration/test_end_to_end.py` (the placeholder directory's first occupant) proves integration at two levels. (1) Real `app.py` startup via AppTest: all seven page modules import at module level, the `st.navigation` structure registers, and the default Dashboard page runs without exception (AppTest 1.66 does not expose the nav switcher as sidebar widgets, so the default-page assertion documents that limitation). (2) Two business workflows walked through the service layers on one temporary database — product → sales → inventory decrement → dashboard metrics → analytics totals → performance trend → restocking advice (reorder point + DEC-038 target-stock ROQ hand-computed) → CSV import → linked-item forecast (MA-7 path, 28.0 units over 7 days) → stored evaluation summary; plus a reorder-breach flow (span-1 demand → reorder point 24 breach, ROQ 78) appearing in both the restock service and the dashboard low-stock overview. Every page↔service pairing was already covered by its page's AppTest tests; this task adds the cross-layer connection proof. Suite 427/427.

### TASK-045: Implement Application Error Handling

- Priority: P0
- Status: Verified
- Dependencies: TASK-044

Description:

Review and improve error handling across the application.

Evidence:

- Expected errors are handled.
- Users receive understandable messages.
- Internal error details are not unnecessarily exposed.

Completion record (2026-11-11): audited every page's exception coverage. Already guarded (no changes needed): restock (DatabaseError), imports (CsvFileError/CsvStructureError/DuplicateImportError/ImportRejectedError/DatabaseError), all form submissions (ValueError/DatabaseError → inline messages), forecast (ProductNotLinkError/ArtifactError/ForecastError/DatabaseError/ValueError), dashboard and analytics service reads. Gaps found and fixed — top-level page reads that would have surfaced raw stack traces on a database failure: `product_service.list_products()` in analytics, forecast, sales (entry + history), and products (listing, edit, stock tabs); `sales_service.list_sales()` in the sales history; `inventory_service.get_stock_overview()` in the products listing; and the two `set_product_active` actions. All now follow the established pattern: catch the specific expected exception, show a short human message ("Could not load products: …"), and return cleanly. Exposure policy: messages include the service-level exception text (already user-safe, no SQL, no stack traces, no secrets) and never Python tracebacks; unexpected exceptions remain visible as Streamlit's own error display, which is honest for an educational project. Tests: 3 new AppTest degradation tests (analytics, forecast, sales history) that inject a failing service and assert a friendly `st.error` with no page exception. Suite 430/430.

### TASK-046: Run Automated Test Suite

- Priority: P0
- Status: Verified
- Dependencies: Implemented core services

Description:

Run all relevant automated tests.

Evidence:

- Test results are recorded.
- Failures are fixed or documented.
- No tests are reported as passing without execution.

Completion record (2026-11-11): formal verification run — **430 tests collected, 430 passed, 0 failed, 0 skipped, no warnings, ~110 seconds** (three consecutive clean runs during this checkpoint, plus every prior task ran the full suite before its commit; every "suite N/N" claim in this document corresponds to an actually executed `pytest` run). Suite shape: flat `tests/` layout organized by layer — repositories, database (incl. the DEC-060 legacy-migration test), domain (inventory/restocking formulas), ML (exploration, baselines, features, splits, training, artifacts, inference, with skip-guards for real-artifact pins), preprocessing/CSV import (M-001…M-006), services (products, sales, inventory, restock, forecast, dashboard, analytics, evaluation), page AppTest tests (products, sales, restock, dashboard, forecast, analytics, imports), and the TASK-044 integration tests (real `app.py` startup + end-to-end workflows; `tests/unit` and `tests/fixtures` remain empty placeholders — no separate unit layout needed at this scale). Coverage focus follows the testing strategy: inventory calculations, sales arithmetic, data validation, forecast feature generation, prediction output handling, restocking recommendations — every business rule named in the docs is pinned by at least one hand-computed test.

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