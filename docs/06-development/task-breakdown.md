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
- Status: Not Started
- Dependencies: TASK-005

Description:

Implement reusable functions for loading the selected dataset.

Evidence:

- Valid files load successfully.
- Missing or unreadable files produce clear errors.
- Loader tests pass.

### TASK-007: Implement Data Validation

- Priority: P0
- Status: Not Started
- Dependencies: TASK-006

Description:

Validate required columns, data types, dates, and sales values.

Evidence:

- Valid data is accepted.
- Invalid data is handled safely.
- Validation tests pass.

### TASK-008: Implement Data Preprocessing

- Priority: P0
- Status: Not Started
- Dependencies: TASK-007

Description:

Implement the preprocessing rules defined in the data documentation.

Evidence:

- Preprocessing functions are reusable.
- Data quality issues are handled according to approved rules.
- Tests pass.

---

## 6. Database and Persistence

### TASK-009: Confirm Initial Database Schema

- Priority: P0
- Status: Not Started
- Dependencies: TASK-001

Description:

Review the logical database schema and resolve decisions necessary for the initial implementation.

Evidence:

- Initial schema documented.
- Required entities and relationships identified.
- Open decisions recorded.

### TASK-010: Implement SQLite Initialization

- Priority: P0
- Status: Not Started
- Dependencies: TASK-009

Description:

Create the SQLite database initialization process.

Evidence:

- Database initializes successfully.
- Required tables exist.
- Initialization can be repeated safely.

### TASK-011: Implement Database Connection Management

- Priority: P0
- Status: Not Started
- Dependencies: TASK-010

Description:

Implement reusable database connection handling.

Evidence:

- Connections are managed safely.
- Errors are handled appropriately.
- Relevant tests pass.

### TASK-012: Implement Repositories

- Priority: P0
- Status: Not Started
- Dependencies: TASK-011

Description:

Implement database access functions for the confirmed entities.

Evidence:

- Required CRUD operations work.
- SQL queries are parameterized.
- Repository tests pass.

---

## 7. Domain and Application Services

### TASK-013: Implement Product Services

- Priority: P0
- Status: Not Started
- Dependencies: TASK-012

Description:

Implement product creation, retrieval, updating, and the approved removal behavior.

Evidence:

- Product operations work independently of Streamlit.
- Validation is enforced.
- Unit tests pass.

### TASK-014: Implement Inventory Services

- Priority: P0
- Status: Not Started
- Dependencies: TASK-012, TASK-013

Description:

Implement current stock retrieval and approved inventory adjustment behavior.

Evidence:

- Inventory calculations are correct.
- Invalid adjustments are handled.
- Relevant tests pass.

### TASK-015: Implement Sales Services

- Priority: P0
- Status: Not Started
- Dependencies: TASK-012, TASK-013, TASK-014

Description:

Implement sales recording and retrieval.

Evidence:

- Sales are stored correctly.
- Approved inventory interactions work.
- Relevant tests pass.

---

## 8. Product and Inventory Interface

### TASK-016: Implement Product Listing

- Priority: P0
- Status: Not Started
- Dependencies: TASK-013

Description:

Create the Products and Inventory page with a product listing.

Evidence:

- Products are loaded from the database.
- Empty states are handled.
- Displayed values are correct.

### TASK-017: Implement Product Forms

- Priority: P0
- Status: Not Started
- Dependencies: TASK-016

Description:

Implement product creation and editing forms.

Evidence:

- Valid products can be saved.
- Invalid input is rejected.
- Updated values appear correctly.

### TASK-018: Implement Inventory Display and Adjustments

- Priority: P0
- Status: Not Started
- Dependencies: TASK-014, TASK-016

Description:

Display stock levels and implement approved inventory adjustments.

Evidence:

- Stock levels match persisted data.
- Adjustment behavior follows business rules.
- Relevant tests pass.

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