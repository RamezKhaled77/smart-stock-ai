# Changelog

All notable changes to SmartStock AI are documented in this file.

This changelog records meaningful changes to the project, including:

- New features.
- Improvements.
- Bug fixes.
- Breaking changes.
- Important technical changes.
- Documentation changes.

The format is inspired by Keep a Changelog.

---

## 1. Changelog Principles

### 1.1 Accuracy

Only changes that have actually been made should be recorded.

Planned features must not appear as completed changes.

A task being documented does not mean that its implementation exists.

### 1.2 Clarity

Each entry should briefly explain:

- What changed.
- Why the change matters.
- Which area of the project is affected.

Entries should be understandable without requiring the reader to inspect every code change.

### 1.3 Consistency

Use the same categories and formatting throughout the changelog.

Avoid recording insignificant changes such as:

- Minor whitespace adjustments.
- Temporary debugging changes.
- Unrelated local environment modifications.
- Every individual test execution.
- Changes that do not meaningfully affect the project.

### 1.4 Traceability

When possible, reference related identifiers:

- Task IDs, such as `TASK-001`.
- Decision IDs, such as `DEC-001`.
- Acceptance criteria, such as `AC-001`.

References should only be included when they are relevant and accurate.

---

## 2. Entry Categories

Use the following categories.

### Added

For new functionality, modules, features, or capabilities.

Examples:

- Added product management functionality.
- Added sales CSV import.
- Added demand forecasting.

### Changed

For modifications to existing functionality or behavior.

Examples:

- Improved dashboard metrics.
- Changed inventory validation behavior.
- Updated forecasting feature generation.

### Fixed

For bug fixes.

Examples:

- Fixed incorrect stock calculations.
- Fixed CSV date parsing.
- Fixed invalid forecast output handling.

### Removed

For functionality, dependencies, or files that have been intentionally removed.

Examples:

- Removed an unused dependency.
- Removed a deprecated implementation.

### Security

For changes that address security-related issues.

Examples:

- Improved input validation.
- Prevented sensitive configuration values from being exposed.

### Technical

For important internal changes that affect architecture, infrastructure, or maintainability.

Examples:

- Introduced a repository layer.
- Separated forecasting from inventory recommendation logic.
- Updated database initialization.

### Documentation

For meaningful documentation changes.

Examples:

- Added the agent workflow.
- Updated the implementation plan.
- Documented deployment requirements.

---

## 3. Status and Release Rules

### 3.1 Unreleased Section

The `Unreleased` section contains meaningful changes that have been implemented but have not yet been assigned to a formal release.

It may include:

- Added functionality.
- Changed behavior.
- Bug fixes.
- Technical improvements.
- Documentation updates.

Do not use this section for planned or unimplemented work.

### 3.2 Versioned Releases

When the project adopts formal versioning, changes may be grouped under version headings.

Example:

`## [1.0.0] - YYYY-MM-DD`

The version number and release date must reflect an actual release.

Do not invent release dates or version numbers.

### 3.3 Versioning Strategy

Semantic Versioning may be adopted when the project begins publishing formal releases.

The general format is:

`MAJOR.MINOR.PATCH`

- `MAJOR`: Incompatible changes.
- `MINOR`: New backward-compatible functionality.
- `PATCH`: Backward-compatible bug fixes.

This strategy is proposed and does not require the project to create versioned releases during early development.

### 3.4 Verification and Release

A changelog entry does not automatically mean the associated functionality is verified or released.

The agent must distinguish between:

- Implemented changes.
- Verified changes.
- Published releases.

Release information should only be recorded when the corresponding release actually exists.

---

## 4. Writing Changelog Entries

Use short, descriptive bullet points.

### Recommended Format

```text
- [TASK-001] Added product creation and validation.
```

For larger changes, additional context may be included.

Example:

```
- [TASK-015] Added demand forecasting using a trained
  regression model. Predictions are generated without
  modifying inventory records.
```

### Rules

- Use past tense.
    
- Describe actual changes.
    
- Avoid vague descriptions.
    
- Include relevant task identifiers when available.
    
- Avoid duplicating the same change in multiple categories.
    
- Do not include sensitive information.
    
- Do not include secrets, credentials, or private data.
    
- Do not claim performance improvements without evidence.
    

## 5. Initial Project History

This section records the initial project preparation and documentation work.

It does not imply that the application itself has been implemented.

## [Unreleased]

### Documentation

- Defined the initial SmartStock AI project overview.
    
- Documented the inventory management problem and proposed solution.
    
- Defined project goals, scope, and requirements.
    
- Documented proposed product features and user flows.
    
- Documented proposed business rules and acceptance criteria.
    
- Documented the initial system architecture and technical stack.
    
- Documented the proposed database structure and coding standards.
    
- Documented dataset characteristics and data processing requirements.
    
- Documented the initial machine learning strategy.
    
- Documented the forecasting and model evaluation approach.
    
- Documented the proposed application interface and page specifications.
    
- Documented the implementation plan and task breakdown.
    
- Documented the testing strategy and development setup.
    
- Established the initial project decisions and progress tracking.
    
- Documented known project limitations.
    
- Defined the autonomous-with-guardrails AI agent workflow.
    
- Documented platform-independent deployment requirements.
    

### Changed

- [TASK-001] Closed all 10 previously open decisions with the project owner (DEC-015, DEC-025, DEC-026, DEC-027, DEC-028, DEC-034, DEC-035, DEC-036, DEC-037, DEC-038) and updated the affected specifications (business rules, forecasting strategy, prediction logic, requirements, dataset overview, database schema, testing strategy).

### Added

- [TASK-002] Approved dependencies documented in `requirements.txt` (streamlit, pandas, numpy, scikit-learn, plotly, joblib, pytest) with minimum-version constraints.
- [TASK-005] Verified dataset characteristics recorded in `../03-data/dataset-overview.md` (913,000 rows, complete daily sequence, no quality issues).
- [TASK-006] Dataset loader `load_historical_dataset()` with clear `DatasetError` reporting, plus preprocessing functions (`filter_store`, `sort_chronologically`, `detect_date_gaps`, `preprocess_dataset`) and `scripts/prepare_dataset.py` (TASK-008).
- [TASK-007] Dataset validation (`validate_and_parse_dataset`) with rejection policies documented in `../03-data/data-preprocessing.md` section 19.
- [TASK-009 - TASK-012] Database and persistence layer: approved `database/schema.sql` (Products + Sales only, DEC-047/DEC-048/DEC-049 applied), idempotent initialization (`initialize_database`, `verify_tables`), connection management (`connect`, `session` with commit/rollback/close), and three repositories (product, inventory, sales) with parameterized SQL and plain-dictionary returns.

### Technical

- [TASK-005] Dataset inspection executed programmatically (dataset overview updated; competition `test.csv` recorded as unusable for evaluation).
- Established a documentation-first development workflow.
    
- Defined the separation between forecasting, inventory calculations, and restocking recommendations.
    
- Established initial development and verification guidelines.
    
- [TASK-002] Development environment initialized: `.venv` on Python 3.12.3 with all approved libraries installed and import-verified.
- [TASK-003] Project structure created per the approved `../02-architecture/project-structure.md` (`src/smartstock/` package layout, `data/`, `models/artifacts/`, `scripts/`, `tests/`); Kaggle dataset files relocated to git-ignored `data/raw/`.
- [TASK-004] Git repository initialized on branch `main` with the approved `.gitignore`; checkpoint commits recorded.
- [TASK-003] Minimal Streamlit entry point (`app.py`) and centralized configuration (`config.py`) added; verified by a headless smoke test (HTTP 200, no errors) and `py_compile`.
- [TASK-006] Test suite started: `tests/test_preprocessing.py` covers loading, validation, and preprocessing (24 passing tests, TASK-006 … TASK-008).
- [TASK-009] Schema decisions DEC-047 (direct stock column), DEC-048 (soft delete), DEC-049 (no returns in v1) recorded and applied across `database-schema.md` and `business-rules.md`.
- [TASK-010] Database tests (`tests/test_database.py`): initialization idempotency, table/column verification, CHECK constraints, FK enforcement; real-path smoke test on `data/smartstock.db` (git-ignored).
- [TASK-011] Connection tests (`tests/test_connection.py`): commit/rollback/close behavior of `session()`, consistent connection settings, error wrapping.
- [TASK-012] Repository tests (`tests/test_repositories.py`): product CRUD and soft delete, stock adjustment guards (DEC-034), sales recording/filter/aggregation (DEC-049), error handling; full suite at 65 passing tests.
- [TASK-013 - TASK-015] Application services (`product_service`, `inventory_service`, `sales_service`) with the atomic DEC-035/BR-012 sale transaction; sales-service tests (`tests/test_services.py`) prove rejected sales leave inventory untouched; suite at 84 passing tests.
- [TASK-016] First Streamlit page: Products & Inventory listing with search/filters and BR-008 stock status backed by the new `domain/inventory.py` calculations (DEC-032 reordered point rendered); `app.py` navigation; documented `streamlit run app.py`; suite at 119 passing tests.
- [TASK-017 - TASK-018] Product add/edit forms with soft-delete removal (confirmation + reactivation) and stock adjustment/correction panel with clear DEC-034 rejections; session-flash feedback; suite at 134 passing tests.
- [TASK-019] Low-stock indicators: per-product status markers, reorder-point column, and a restocking banner naming affected SKUs (BR-008 + DEC-032 rules); suites unchanged at 134 passing tests.
- [TASK-020 - TASK-021] Sales Management page: manual record-sale form exercising the atomic DEC-035/BR-012 transaction (insufficient-stock rejections proven at UI level), sales history with product/date filters and both empty states; suite at 147 passing tests.
- [DEC-052..055] CSV import decisions closed with the project owner: dedicated `historical_sales`/`import_batches` tables keyed by dataset `item`, SHA-256 fingerprint + `UNIQUE (item, sale_date)` duplicate handling, all-or-nothing imports, historical-only scope in v1.
- [TASK-022 - TASK-023] Historical CSV import validation and preview: strict structure/row validation with per-row reasons, DEC-015 store filter, within-file duplicate skipping; preview service + Data Import page with metrics, date range, capped examples, sample rows, and fingerprint caption; suite at 187 passing tests.
- [TASK-024] Historical import persistence: `import_batches`/`historical_sales` schema (DEC-052/053), all-or-nothing one-transaction repository with fingerprint rejection and existing-row skipping, service `execute_import` re-validating current bytes and upgrading legacy databases, page confirm flow; suite at 199 passing tests.
- [TASK-026] Sales data exploration for the forecasting phase: tested exploration module + `data-exploration.md` with measured store-1 findings (complete coverage, weekday ramp Mon→Sun +50%, July peak/January trough, steady annual growth +35% over 5 years, lag-7 correlation 0.908 strongest) and documented limitations (no zero-demand days, no covariates, competition regularity); suite at 222 passing tests.
- [DEC-056] Chronological split accepted: Train 2013–2015, Validation 2016, Test 2017 (calendar years).
- [TASK-027] Baseline forecasting: naive + trailing-window averages over the DEC-056 validation window with leak-free walk-forward evaluation; measured naive MAE 10.270, trailing-7 MAE 8.077 (window question resolved to 7 days); suite at 239 passing tests.
- [TASK-028] Feature engineering pipeline: calendar + per-series lag + shifted rolling-mean features with fixed FEATURE_COLUMNS order, explicit NaN-preserving row dropping, and (X, y) split helper; leakage-verified on the real dataset (89,800 complete training rows; 31-observation minimum history); suite at 262 passing tests.
- [TASK-029] Chronological splitting helper: DEC-056 calendar-year constants as executable code with strict boundary/coverage guards; real-dataset pins (train 54,750 / validation 18,300 / test 18,250); suite at 275 passing tests.
- [TASK-030] Candidate model training/evaluation: Linear Regression (MAE 6.482) and Random Forest (MAE 6.033) both beat both baselines (MA-7 8.077, naive 10.270) on validation 2016 in a like-for-like one-step-ahead protocol; measured results in model-evaluation §17; suite at 291 passing tests.
- [DEC-057] Final forecasting model selected: Random Forest (validation MAE 6.033; Linear Regression ≈7.4% worse → DEC-027 5% band not triggered).
- [TASK-031] Model selection completed: one-time test-window confirmation (2017: RF MAE 6.088, beats MA-7 reference 8.378); model-evaluation §18; suite at 298 passing tests.
- [TASK-032] Model artifact pipeline: atomic save/verify/replace persistence with metadata contract, scripts/train_model.py training workflow, production artifact fit on all observed history (89,800 rows) with committed metadata; suite at 314 passing tests.
- [DEC-058] Short-history forecasting policy: ≥31 days → Random Forest; 1–30 days → MA-7 recursive fallback; 0 days → explicit error.
- [TASK-033] Forecast inference: validated recursive §8 loop with per-call working history, all DEC-026 horizons, DEC-058 path selection, and §9 output contract; suite at 334 passing tests.
- [DEC-033 confirmed] Recommended Order Quantity = max(0, Target Stock − Inventory Position); recommendation availability from ≥1 observed day.
- [TASK-034] Restocking parameters confirmed: all formulas and inputs approved, business-rules statuses reconciled to Accepted; ready for the recommendation service implementation.
- [DEC-059] Average Daily Demand window: calendar window ends at the last recorded sale, zeros filled, denominator min(30 days, history span).
- [TASK-035] Restocking calculations: DEC-059 demand anchoring, target stock (DEC-038) and order quantity (DEC-033) formulas, RestockRecommendation composition with explicit unavailable states, read-only restock service; suite at 361 passing tests.
- [TASK-036] Restocking Recommendations page: advisory display with summary metrics, supporting inputs, per-product explanations and unavailable reasons; navigation registered; suite at 367 passing tests.
- [DEC-060] Product ↔ dataset-item mapping: nullable products.dataset_item_id; forecasts consume the linked item's imported history only; guarded schema migration.
- [TASK-040] Demand Forecast page: product-driven forecasts (7/14/30 days) over the DEC-057 model with DEC-058 path labels, forecast service, zero-filled linked history, clear unlinked/no-history/artifact-missing states; suite at 383 passing tests.
- [DEC-061] Dashboard metric set: six groups (products, stock, needing-reorder, 7-day sales activity, top-3 sellers, forecast readiness).
- [TASK-037/038/039] Dashboard implemented: metrics from verified services, built-in line-chart sales trend with 7/30-day selector, low-stock overview per BR-008; suite at 398 passing tests.
- [TASK-041] Sales Analytics page: date-range and product-filtered quantity analytics (totals, daily trend, weekday pattern, product ranking with shares, monthly totals); suite at 409 passing tests.
- [DEC-062] Actual-vs-predicted display: stored training-time evaluation metrics only; no new predictions (test window one-touch per DEC-056).
- [TASK-042] "How accurate is the model?" section on the Demand Forecast page with measured window MAE/RMSE and baseline context; suite at 418 passing tests.
- [M-004/M-005/M-006 Completed] Product & inventory (TASK-016…019), sales management (TASK-020/021), and CSV import (TASK-022…025) milestones marked Completed in progress.md §6; CSV import summary per spec §14 (result panel, batch history) at 205 passing tests. Next: forecasting/ML phase (TASK-026…), with the train/validation/test split dates to be decided during implementation.

## 6. Future Entry Template

Use the following template when adding new changes.

### Unreleased

#### Added

- [TASK-ID] Describe the implemented functionality.

#### Changed

- [TASK-ID] Describe the modification.

#### Fixed

- [TASK-ID] Describe the bug fix.

#### Removed

- [TASK-ID] Describe the removed functionality.

#### Security

- [TASK-ID] Describe the security improvement.

#### Technical

- [TASK-ID] Describe the technical change.

#### Documentation

- [TASK-ID] Describe the documentation update.

Only include categories that contain actual changes.

Remove empty categories when updating the changelog.

## 7. AI Agent Responsibilities

The AI agent is responsible for maintaining this changelog whenever it makes meaningful project changes.

### 7.1 Before Adding an Entry

The agent must verify:

1. The change was actually implemented.
    
2. The change is meaningful enough to record.
    
3. The description accurately reflects the implementation.
    
4. The task identifier is correct, if included.
    
5. The entry does not duplicate an existing record.
    

### 7.2 During Development

The agent should keep track of meaningful changes made during the session.

It does not need to update the changelog after every small edit.

It should update the file when a task or meaningful group of changes is completed.

### 7.3 After Verification

When a change has been verified, the agent may record its verified status in the relevant task documentation.

The changelog should remain focused on what changed rather than becoming a detailed testing log.

### 7.4 Incomplete Work

Do not record incomplete functionality as a completed feature.

If a partially implemented feature introduces a meaningful technical change, describe its current state clearly.

For example:

- [TASK-020] Added the initial forecasting service structure; prediction integration remains incomplete.

### 7.5 Documentation-Only Sessions

Documentation changes may be recorded even when no application code has been modified.

However, documentation must not claim that planned application functionality has been implemented.

## 8. Relationship with Other Project Documents

The changelog works alongside the following documents:

|Document|Responsibility|
|---|---|
|`task-breakdown.md`|Tracks implementation tasks and their statuses.|
|`progress.md`|Tracks overall project progress.|
|`decisions.md`|Records important project decisions.|
|`known-limitations.md`|Records known constraints and limitations.|
|`implementation-plan.md`|Defines the planned implementation sequence.|
|`acceptance-criteria.md`|Defines feature completion requirements.|

These documents serve different purposes and should not replace one another.

For example:

- A task may be marked `Completed` in the task breakdown.
    
- The overall project progress may still show the implementation phase as ongoing.
    
- The changelog may contain the implemented feature.
    
- The acceptance criteria may still require additional verification.
    

This is expected and should not be treated as an inconsistency.

## 9. Current Changelog Status

At the time this document was created:

- Project documentation has been prepared across the initial documentation structure.
    
- The agent workflow has been documented.
    
- Deployment preparation requirements have been documented.
    
- Application implementation has not been confirmed by this changelog.
    
- No production deployment has been confirmed.
    
- No formal application release has been recorded.
    

Future entries must reflect verified repository changes rather than assumptions based on planning documents.

## 10. Core Principle

The changelog is a historical record of what actually happened to SmartStock AI.

It must remain accurate, concise, and traceable.

It should never become a list of planned features presented as completed work.