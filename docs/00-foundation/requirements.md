# SmartStock AI — Requirements Specification

## 1. Purpose

This document defines the functional and non-functional requirements of SmartStock AI.

It describes what the application should do and the quality standards it should satisfy.

These requirements will guide implementation, testing, and acceptance.

## 2. Requirement Classification

Requirements use the following categories:

- **FR:** Functional Requirement.
- **NFR:** Non-Functional Requirement.
- **DR:** Data Requirement.
- **MLR:** Machine Learning Requirement.

Each requirement has an identifier for reference.

### Priority Levels

| Priority | Meaning |
|---|---|
| Must Have | Required for the initial working application |
| Should Have | Important but may follow core implementation |
| Could Have | Optional improvement |
| Future | Outside the initial implementation scope |

### Status Values

- Proposed
- Accepted
- In Progress
- Implemented
- Verified
- Rejected
- Blocked

Requirements are not considered formally accepted merely because they appear in this document.

Their approval status should be tracked through project decisions.

## 3. Functional Requirements

### 3.1 Product Management

#### FR-001: Create Product

The system should allow the user to create a product.

A product may include:

- Product ID.
- Product name.
- Product description.
- Category.
- Current stock quantity.
- Reorder-related settings.
- Creation timestamp.

Exact fields will be finalized in the database schema.

Priority: Must Have

Status: Proposed

#### FR-002: View Products

The system should display the available products and their relevant inventory information.

Priority: Must Have

Status: Proposed

#### FR-003: Update Product

The system should allow the user to update product information.

Priority: Must Have

Status: Proposed

#### FR-004: Update Stock Quantity

The system should allow authorized inventory adjustments.

The application should validate the quantity before saving it.

Priority: Must Have

Status: Proposed

#### FR-005: Product Search and Filtering

The system should provide basic product search and filtering.

Priority: Should Have

Status: Proposed

### 3.2 Inventory Management

#### FR-006: Track Current Stock

The system should maintain the current stock quantity for each product.

Priority: Must Have

Status: Proposed

#### FR-007: Display Stock Status

The system should identify products that meet configured stock warning conditions.

Priority: Must Have

Status: Proposed

#### FR-008: Low-Stock Alerts

The system should highlight products that have reached or fallen below their configured reorder threshold.

Priority: Must Have

Status: Proposed

#### FR-009: Inventory Adjustments

The system should support stock adjustments.

The reason and behavior of inventory adjustments must be defined in the business rules.

Priority: Should Have

Status: Proposed

### 3.3 Sales Management

#### FR-010: Record Sales

The system should allow the user to record a sale.

A sale record should contain enough information to identify:

- Product.
- Quantity sold.
- Sale date.

Additional fields may include unit price and total amount if monetary analysis is included.

Priority: Must Have

Status: Proposed

#### FR-011: View Sales History

The system should display historical sales records.

Priority: Must Have

Status: Proposed

#### FR-012: Import Sales CSV

The system should allow the user to import historical sales data from CSV files.

Priority: Must Have

Status: Proposed

#### FR-013: Validate Imported Sales

The system should validate imported files before accepting their data.

Validation should include:

- Required columns.
- Valid dates.
- Valid product identifiers.
- Numeric sales quantities.
- Missing values.
- Invalid or negative quantities.
- Duplicate records where relevant.

Priority: Must Have

Status: Proposed

#### FR-014: Prevent Invalid Imports

The system should not silently accept invalid records.

It should provide understandable validation feedback.

Priority: Must Have

Status: Proposed

### 3.4 Dashboard and Analytics

#### FR-015: Dashboard Overview

The system should provide a dashboard summarizing important inventory and sales information.

Priority: Must Have

Status: Proposed

#### FR-016: Sales Summary

The system should display useful sales summaries over selected periods.

Priority: Should Have

Status: Proposed

#### FR-017: Inventory Summary

The system should display current inventory information and highlight products requiring attention.

Priority: Must Have

Status: Proposed

#### FR-018: Sales Trend Visualization

The system should visualize historical sales trends.

Priority: Should Have

Status: Proposed

### 3.5 Demand Forecasting

#### FR-019: Prepare Forecasting Data

The system should prepare historical sales data for forecasting.

Priority: Must Have

Status: Proposed

#### FR-020: Generate Demand Features

The forecasting pipeline should generate appropriate time-based and historical sales features.

Priority: Must Have

Status: Proposed

#### FR-021: Train Forecasting Models

The project should support training and comparing suitable forecasting models.

Priority: Must Have

Status: Proposed

#### FR-022: Evaluate Models

The project should evaluate forecasting performance using suitable metrics and time-aware validation.

Priority: Must Have

Status: Proposed

#### FR-023: Generate Demand Predictions

The system should generate future demand predictions for supported products and forecast periods.

Priority: Must Have

Status: Proposed

#### FR-024: Display Forecast Results

The application should display predictions in an understandable format.

Priority: Must Have

Status: Proposed

#### FR-025: Display Actual vs. Predicted Results

The system should support comparing actual and predicted demand when actual observations are available.

Priority: Should Have

Status: Proposed

### 3.6 Restocking Recommendations

#### FR-026: Calculate Reorder Point

The system should calculate a reorder point using approved inventory rules and available product information.

Priority: Must Have

Status: Proposed

#### FR-027: Generate Restocking Recommendations

The system should recommend restocking quantities based on predicted demand and inventory information.

Priority: Must Have

Status: Proposed

#### FR-028: Explain Recommendations

The system should display the main reasons behind a restocking recommendation.

Possible reasons include:

- Low current stock.
- High expected demand.
- Reaching the reorder point.
- Long replenishment lead time.

Priority: Should Have

Status: Proposed

#### FR-029: Review Recommendations

The user should be able to review recommendations before taking any purchasing action.

Priority: Must Have

Status: Proposed

## 4. Non-Functional Requirements

### 4.1 Usability

#### NFR-001: Simple Interface

The interface should be understandable to users with basic computer skills.

Priority: Must Have

Status: Proposed

#### NFR-002: Clear Feedback

The application should provide clear success, warning, and error messages.

Priority: Must Have

Status: Proposed

#### NFR-003: Consistent Interface

Navigation, labels, and interaction patterns should remain consistent across application pages.

Priority: Should Have

Status: Proposed

### 4.2 Performance

#### NFR-004: Lightweight Execution

The application should be suitable for local execution on modest hardware.

Priority: Must Have

Status: Proposed

#### NFR-005: Reasonable Response Time

Common application operations should complete within a reasonable time for the expected dataset size.

Exact performance targets should be established after implementation testing.

Priority: Should Have

Status: Proposed

### 4.3 Reliability

#### NFR-006: Input Validation

The system should validate user input and imported data.

Priority: Must Have

Status: Proposed

#### NFR-007: Error Handling

The application should handle expected errors without crashing unnecessarily.

Priority: Must Have

Status: Proposed

#### NFR-008: Data Consistency

Inventory and sales operations should preserve valid and consistent data.

Priority: Must Have

Status: Proposed

### 4.4 Maintainability

#### NFR-009: Modular Architecture

The application should separate UI, business logic, database operations, and ML functionality.

Priority: Must Have

Status: Proposed

#### NFR-010: Clear Code Structure

The codebase should use understandable names and consistent coding standards.

Priority: Must Have

Status: Proposed

#### NFR-011: Documentation

Important setup, architecture, and implementation details should be documented.

Priority: Must Have

Status: Proposed

### 4.5 Portability

#### NFR-012: Local Development

The application should be runnable in a documented local development environment.

Priority: Must Have

Status: Proposed

#### NFR-013: Reproducible Dependencies

The project should document its Python dependencies.

Priority: Must Have

Status: Proposed

### 4.6 Security

#### NFR-014: Safe Data Handling

The application should avoid unsafe database operations and validate external input.

Priority: Must Have

Status: Proposed

#### NFR-015: Secret Protection

Credentials and private configuration must not be committed to the repository.

Priority: Must Have

Status: Proposed

## 5. Data Requirements

### DR-001: Product Data

The system must maintain identifiable product records.

### DR-002: Sales Data

Sales records must contain a product reference, date, and quantity.

### DR-003: Inventory Data

The system must maintain current inventory quantities.

### DR-004: Historical Data

The forecasting pipeline must have access to valid historical demand observations.

### DR-005: Data Validation

Imported data must be checked before it is used by the application or ML pipeline.

### DR-006: Data Traceability

The system should maintain enough information to understand where imported and processed data originated.

All data requirements are currently Proposed.

## 6. Machine Learning Requirements

### MLR-001: Forecasting Target

The target variable must represent future product demand.

### MLR-002: Baseline

At least one simple baseline must be established before selecting a more complex model.

### MLR-003: Time-Aware Validation

Chronological data splitting or another justified time-aware validation method must be used.

### MLR-004: Leakage Prevention

Features must not contain information that would be unavailable at prediction time.

### MLR-005: Model Evaluation

Forecasting models must be evaluated using appropriate quantitative metrics.

### MLR-006: Model Persistence

A trained model should be saved and loaded without requiring retraining for every prediction.

### MLR-007: Prediction Validation

Predictions should be checked for invalid outputs and handled appropriately.

### MLR-008: Reproducibility

The training process should document its data, features, configuration, and evaluation results.

All ML requirements are currently Proposed.

## 7. Requirement Dependencies

Some requirements depend on earlier decisions.

| Requirement | Dependency |
|---|---|
| FR-010 | Product and sales data model |
| FR-012 | CSV schema and validation rules |
| FR-019 | Dataset investigation |
| FR-020 | Forecasting strategy |
| FR-021 | ML model selection |
| FR-022 | Evaluation strategy |
| FR-023 | Trained model and prediction pipeline |
| FR-026 | Inventory business rules |
| FR-027 | Forecasting output and inventory rules |
| FR-028 | Recommendation explanation logic |

The agent must respect these dependencies when planning implementation.

## 8. Open Questions

Resolved on 2026-11-04 (see `../07-project-management/decisions.md`):

4. ~~Will users be able to configure lead time per product?~~ → Yes, manual per-product field (DEC-037, default 3 days).
5. ~~How will safety stock be calculated?~~ → Manually configured per product, optional, default 0 (DEC-036).
6. ~~What is the default forecast horizon?~~ → User-selectable 7/14/30 days, default 7 (DEC-026).

Resolved on 2026-11-12 (documentation sync — each was already settled by an implemented, tested choice; recorded here so the list tells the truth):

1. ~~Will product prices be included?~~ → No in v1: products carry no monetary fields, so revenue metrics are out of scope (features.md F-006 limitation).
2. ~~Will sales records store individual transactions or daily aggregated quantities?~~ → Individual transactions: each sale records its own quantity and date, and sales are immutable (DEC-049).
3. ~~Will inventory adjustments have a history log?~~ → No log in v1: stock changes are direct updates; low-stock warnings are advisory snapshots, not logged events (features.md F-011).
7. ~~Will the system forecast every product or only products with sufficient historical data?~~ → Per DEC-058: Random Forest needs ≥31 observed days, a 7-day moving-average fallback covers 1–30 days, and 0 days yields an explicit "no suitable history" message.
8. ~~Will authentication be required?~~ → No in v1: the application is a local, single-user Streamlit app.
9. ~~Will the initial version support only one currency?~~ → Not applicable in v1: with no prices (item 1) there are no monetary fields to denominate.
10. ~~Will restocking recommendations include incoming stock?~~ → No in v1: inventory position equals current stock, per DEC-031 and BR-022.

Still open:

None. Any new question is recorded as a decision (or open decision) in `../07-project-management/decisions.md` when it arises.

## 9. Requirement Change Management

When a requirement changes:

1. Update this document.
2. Update the related product specification.
3. Check affected business rules.
4. Check architecture and data dependencies.
5. Update acceptance criteria.
6. Record significant changes in `../07-project-management/decisions.md`.

Do not silently change approved requirements.

## 10. Related Documentation

- [Project Overview](project-overview.md)
- [Goals and Scope](goals-and-scope.md)
- [Features](../01-product/features.md)
- [Business Rules](../01-product/business-rules.md)
- [Acceptance Criteria](../01-product/acceptance-criteria.md)
- [Database Schema](../02-architecture/database-schema.md)
- [Testing Strategy](../06-development/testing-strategy.md)