# SmartStock AI — Product Features

## 1. Purpose

This document describes the product features planned for SmartStock AI.

It defines the main application modules, their responsibilities, priorities, dependencies, and expected behavior.

This document should be used as the primary reference when planning and implementing product functionality.

Detailed business calculations are defined in `business-rules.md`.

User journeys are described in `user-flows.md`.

Feature completion conditions are defined in `acceptance-criteria.md`.

---

## 2. Feature Classification

Features are divided into three categories.

### Core

Features required to deliver the initial working application.

### Advanced

Features that improve the application after the core functionality is stable.

### Future

Features that may be considered in later versions.

### Feature Status

Each feature has one of the following statuses:

- Proposed
- Accepted
- In Progress
- Implemented
- Verified
- Blocked
- Rejected

Unless explicitly approved in the project decision log, features in this document are considered Proposed.

---

# 3. Core Features

## F-001: Dashboard

**Priority:** Core

**Status:** Accepted (TASK-037/038/039, 2026-11-10/11 — DEC-061 metric set)

**Priority:** Core

**Status:** Proposed

### Description

The Dashboard provides a summarized view of the business's inventory and sales activity.

It should help users understand the current business situation without opening every application module.

### Expected Information

Potential dashboard indicators:

- Total number of products.
- Total current stock quantity.
- Number of low-stock products.
- Number of products requiring restocking.
- Recent sales activity.
- Sales trends.
- Products with the highest sales.
- Demand forecasting highlights.

The exact metrics must be finalized during UI and business-rule design.

### Main Capabilities

- Display summary metrics.
- Display inventory alerts.
- Display sales charts.
- Highlight important products.
- Provide navigation to related modules.

### Dependencies

- Product Management.
- Inventory Management.
- Sales Management.
- Restocking Recommendations.

---

## F-002: Product Management

**Priority:** Core

**Status:** Proposed

### Description

Allows users to manage the products sold by their business.

### Main Capabilities

- Add a new product.
- View product details.
- Edit product information.
- Search products.
- Filter products.
- View current stock.
- Configure inventory-related settings.

### Potential Product Information

| Field | Description |
|---|---|
| Product ID | Unique product identifier |
| Product Name | Product display name |
| Description | Optional product description |
| Category | Product category |
| Current Stock | Current recorded inventory quantity |
| Reorder Point | Inventory threshold for replenishment |
| Lead Time | Expected replenishment time |
| Safety Stock | Additional stock buffer |
| Unit Price | Optional selling price |
| Cost Price | Optional product purchase cost |

The final product schema is not yet approved.

See `../02-architecture/database-schema.md`.

### Validation

- Product names must not be empty.
- Product identifiers must be unique.
- Stock quantities must be valid.
- Numeric fields must contain valid numeric values.
- Optional values must be handled consistently.

### Dependencies

- Database Layer.
- Inventory Management.

---

## F-003: Inventory Management

**Priority:** Core

**Status:** Proposed

### Description

Tracks the quantity of each product available in the business.

### Main Capabilities

- Display current stock.
- Update stock quantities.
- Identify low-stock products.
- Display inventory status.
- Track inventory adjustments when supported.

### Possible Inventory Statuses

- In Stock
- Low Stock
- Out of Stock

Exact status rules must follow the approved business logic.

### Important Notes

Inventory changes should not happen silently.

The system should maintain consistency between:

- Recorded sales.
- Current stock.
- Manual adjustments.
- Incoming stock, if supported.

### Dependencies

- Product Management.
- Sales Management.
- Database Layer.

---

## F-004: Sales Management

**Priority:** Core

**Status:** Proposed

### Description

Allows users to record and review sales information.

Sales records provide the historical information required for reporting and demand forecasting.

### Main Capabilities

- Record product sales.
- View sales history.
- Filter sales by date.
- Filter sales by product.
- Review daily sales.
- Import historical sales records from CSV.

### Potential Sales Fields

| Field | Description |
|---|---|
| Sales ID | Unique sales record identifier |
| Product ID | Related product |
| Sales Date | Date of the sale |
| Quantity Sold | Number of units sold |
| Unit Price | Optional selling price |
| Total Amount | Optional calculated sales amount |

The final sales data model remains open for review.

### Important Notes

The system must distinguish between:

- Individual sales transactions.
- Aggregated daily sales quantities.

The final storage approach must support the forecasting requirements.

### Dependencies

- Product Management.
- Database Layer.
- Data Validation.

---

## F-005: CSV Import

**Priority:** Core

**Status:** Proposed

### Description

Allows users to import historical sales information from CSV files.

This feature is important because historical data may already exist outside the application.

### Main Capabilities

- Upload CSV files.
- Inspect file columns.
- Validate required fields.
- Detect invalid records.
- Detect duplicate records where possible.
- Display import summaries.
- Import valid data according to approved import rules.

### Validation Examples

- Missing required columns.
- Invalid dates.
- Invalid numeric values.
- Negative sales quantities.
- Unknown product identifiers.
- Empty product identifiers.
- Duplicate records.

### Expected Feedback

The user should receive:

- Total rows detected.
- Valid rows.
- Invalid rows.
- Duplicate rows.
- Clear validation errors.

### Important Notes

The system must not silently import invalid data.

The import process should avoid partially updating important records when an import fails unexpectedly.

### Dependencies

- Sales Management.
- Data Validation.
- Database Layer.

---

## F-006: Sales Analytics

**Priority:** Core / Advanced

**Status:** Accepted (TASK-041, 2026-11-10/11 — quantity-based Sales Analytics page; v1 scope, no revenue analytics)

### Description

Analyzes historical sales information to provide useful business insights.

Basic summaries are part of the initial dashboard.

More detailed analysis may be implemented as an advanced feature.

### Potential Analytics

- Total units sold.
- Sales by product.
- Daily sales trends.
- Weekly sales trends.
- Monthly sales trends.
- Top-selling products.
- Products with declining sales.
- Product demand patterns.

### Important Notes

Sales quantity and monetary revenue are different metrics.

Monetary analytics require reliable price information.

### Dependencies

- Sales Management.
- Validated Historical Data.
- Visualization Layer.

---

## F-007: Demand Forecasting

**Priority:** Core

**Status:** Accepted (TASK-040, 2026-11-10 — product-driven Demand Forecast page over the DEC-057 model; see prediction-logic §18)

### Description

Uses historical sales information to estimate future product demand.

This is the primary AI capability of SmartStock AI.

### Main Capabilities

- Prepare historical sales data.
- Generate time-based features.
- Generate historical sales features.
- Train forecasting models.
- Evaluate forecasting performance.
- Generate future predictions.
- Display prediction results.

### Candidate Features

Potential model inputs include:

- Day of the week.
- Month.
- Day of the month.
- Previous day's sales.
- Sales seven days ago.
- Seven-day rolling mean.
- Thirty-day rolling mean.

The final feature set must be validated experimentally.

### Candidate Models

- Naive forecasting baseline.
- Historical average baseline.
- Linear Regression.
- Random Forest Regressor.

These are candidates, not final model selections.

### Expected Outputs

- Product identifier.
- Forecast date or period.
- Predicted demand.
- Model or forecasting method used.
- Relevant forecast metadata.

### Dependencies

- Historical Sales Data.
- Data Preprocessing.
- Feature Engineering.
- Model Training.
- Model Evaluation.

---

## F-008: Low-Stock Alerts

**Priority:** Core

**Status:** Proposed

### Description

Identifies products whose current inventory reaches a configured warning threshold.

### Main Capabilities

- Check current stock.
- Compare stock with the approved threshold.
- Display warning status.
- Highlight products requiring attention.

### Possible Statuses

- Normal.
- Low Stock.
- Out of Stock.

The exact rules must be defined in `business-rules.md`.

### Dependencies

- Product Management.
- Inventory Management.

---

## F-009: Restocking Recommendations

**Priority:** Core

**Status:** Accepted (restocking calculations implemented and approved; see DEC-032/033/036/037/038/058/059)

### Description

Uses demand forecasts and inventory information to suggest replenishment actions.

### Main Capabilities

- Read current stock.
- Read future demand forecasts.
- Consider lead time.
- Consider safety stock.
- Consider incoming stock if supported.
- Calculate reorder status.
- Recommend order quantities.
- Explain recommendation reasons.

### Example Output

A recommendation may contain:

- Product name.
- Current stock.
- Expected demand.
- Reorder point.
- Recommended quantity.
- Recommendation reason.

### Important Notes

The forecasting model predicts demand.

The recommendation engine calculates suggested inventory actions.

These responsibilities must remain separate.

### Dependencies

- Product Management.
- Inventory Management.
- Demand Forecasting.
- Business Rules.

---

# 4. Advanced Features

## F-010: Actual vs. Predicted Comparison

**Priority:** Advanced

**Status:** Accepted (TASK-042, 2026-11-11 — DEC-062: stored evaluation metrics display, no new predictions)

Compare previous forecasts with actual observed sales.

This feature helps users understand how well the forecasting model performs.

It may include:

- Actual sales.
- Predicted demand.
- Prediction error.
- Model performance charts.

Actual and predicted values must refer to the same product and time period.

---

## F-011: Product Performance Analysis

**Priority:** Advanced

**Status:** Proposed

Provides additional product-level insights.

Potential indicators:

- Highest-selling products.
- Lowest-selling products.
- Products with increasing demand.
- Products with decreasing demand.
- Products with frequent stock warnings.

Interpretation must be based on valid data.

---

## F-012: Export Reports

**Priority:** Advanced

**Status:** Proposed

Allows users to export selected information.

Potential export formats:

- CSV.
- PDF.

Exact report types and formats require further planning.

---

# 5. Future Features

The following capabilities are outside the initial implementation scope.

| ID | Feature | Description |
|---|---|---|
| F-013 | Supplier Management | Maintain supplier information |
| F-014 | Multi-Branch Support | Manage multiple business locations |
| F-015 | Purchase Orders | Create and track purchase orders |
| F-016 | POS Integration | Import sales from external POS systems |
| F-017 | AI Assistant | Answer questions about inventory and sales |
| F-018 | Advanced User Roles | Support multiple permission levels |
| F-019 | Automated Reordering | Automatically initiate replenishment workflows |

These features require explicit scope approval.

---

# 6. Feature Dependencies

The main dependency flow is:

Product Management
    ↓
Inventory Management

Sales Management
    ↓
Data Validation
    ↓
Historical Sales Dataset
    ↓
Demand Forecasting
    ↓
Prediction Results
    ↓
Restocking Recommendations

Dashboard
    ↓
Consumes information from the main modules

The agent should implement features in an order that respects these dependencies.

---

# 7. Product Design Principles

All features should follow these principles:

1. Keep the interface simple.
2. Display useful information instead of unnecessary metrics.
3. Separate business logic from interface code.
4. Separate forecasting from inventory calculations.
5. Provide understandable feedback.
6. Avoid silent data changes.
7. Explain important recommendations.
8. Avoid unnecessary complexity.
9. Keep features consistent with the approved project scope.

---

# 8. Related Documentation

- `user-flows.md`
- `business-rules.md`
- `acceptance-criteria.md`
- `../00-foundation/requirements.md`
- `../02-architecture/system-architecture.md`
- `../04-machine-learning/forecasting-strategy.md`
- `../05-interface/pages-specification.md`