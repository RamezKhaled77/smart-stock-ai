# Pages Specification

## 1. Purpose

This document defines the responsibilities, content, and expected interactions of the main SmartStock AI application pages.

Each page should have a clear purpose and should use application services for business operations.

Streamlit pages must not contain duplicated business logic or direct database implementation details.

---

## 2. Navigation Structure

The application pages are, grouped into five sidebar sections of
`st.navigation` (see `ui-overview.md` §4):

1. Dashboard (Overview group)
2. Products & Inventory (Inventory group)
3. Restocking Recommendations (Inventory group)
4. Sales Management (Sales group)
5. Sales Analytics (Sales group)
6. Demand Forecast (Forecasting group)
7. Data Import (Data group)

Each page should be accessible through the application's main navigation.

---

## 3. Dashboard

**Purpose:** Provide a quick overview of the current inventory and business activity.

### Main Content

Potential metrics:

- Total products.
- Total current stock.
- Low-stock products.
- Recent sales.
- Estimated demand, when forecasts are available.

### Sections

- Inventory summary.
- Recent sales.
- Low-stock alerts.
- Sales trends.
- Restocking overview.

### Main Interactions

- Navigate to products.
- Review low-stock products.
- Open sales analytics.
- Access forecasting.

Detailed requirements are defined in `dashboard-specification.md`.

---

## 4. Products & Inventory

**Purpose:** Manage products and their inventory information.

### Main Content

A product table may display:

- Product name.
- SKU.
- Category.
- Current stock.
- Lead time.
- Safety stock.
- Stock status.

### Main Actions

- Add a product.
- View product details.
- Edit product information.
- Adjust stock.
- Search products.
- Filter products.

### Product Form

Potential fields:

- Product name.
- SKU.
- Category.
- Initial stock.
- Lead time.
- Safety stock.

The exact fields depend on the approved database and business rules.

### Validation

- Product name must not be empty.
- SKU uniqueness must be enforced if SKU is adopted.
- Numeric values must be validated.
- Stock changes must follow the approved inventory policy.

### Important Constraints

- Product deletion must follow the approved historical record policy.
- Inventory adjustments must follow approved business rules.
- Product changes must be saved through application services.

---

## 5. Sales Management

**Purpose:** Record and review operational sales.

### Main Content

A sales table may display:

- Product.
- Quantity sold.
- Sale date.
- Record creation date.

### Main Actions

- Record a sale.
- View sales history.
- Filter sales by product.
- Filter sales by date.

### Sale Form

Potential fields:

- Product.
- Quantity.
- Sale date.

### Validation

- Product must exist.
- Quantity must follow the approved sales policy.
- Date must be valid.
- Insufficient stock behavior must follow the approved business rules.

### Important Constraints

Recording an operational sale may affect inventory.

The exact behavior must be implemented according to the approved inventory and sales policies.

Historical dataset imports must not be treated as operational sales automatically.

---

## 6. Sales Analytics

**Purpose:** Help users understand historical sales performance.

### Main Content

Potential visualizations:

- Daily sales trends.
- Monthly sales trends.
- Top-selling products.
- Product-level sales comparisons.
- Sales distribution by product.

### Main Filters

- Date range.
- Product.
- Category, if supported.

### Main Interactions

- Select a date range.
- Filter by product.
- Review sales trends.
- Compare product performance.

### Data Requirements

Analytics should use valid sales records.

The application must distinguish between operational sales and historical training data when their sources or meanings differ.

---

## 7. AI Forecasting

**Purpose:** Generate and display future demand predictions.

### Main Content

- Product selection.
- Forecasting horizon.
- Historical demand chart.
- Predicted demand chart.
- Forecast summary.
- Model information when available.

### Main Actions

- Select a product.
- Select a forecast period.
- Generate a forecast.
- Review prediction results.

### Expected Output

A forecast table may display:

- Forecast date.
- Predicted demand.

A chart should distinguish:

- Historical actual demand.
- Future predicted demand.

### Validation

The system should check:

- Product selection.
- Forecasting horizon.
- Model availability.
- Historical data availability.
- Minimum required history.

### Error States

Examples:

- Model not trained.
- Model artifact missing.
- Insufficient historical data.
- Invalid forecasting input.
- Prediction failure.

### Important Constraints

Generating a forecast must not modify operational inventory.

Forecasting and restocking recommendations are separate responsibilities.

---

## 8. CSV Import

**Purpose:** Allow users to import supported CSV files.

### Main Content

- Import type selection.
- File uploader.
- Expected format information.
- Validation summary.
- Data preview.
- Import confirmation.
- Import result.

### Main Actions

- Select import type.
- Upload a file.
- Validate file contents.
- Review validation errors.
- Confirm import.

### Validation

The application should check:

- Required columns.
- File readability.
- Data types.
- Missing values.
- Duplicate records.
- Invalid dates.
- Invalid quantities.

### Important Constraints

Historical imports must not automatically modify current stock.

Operational imports must follow their separately approved behavior.

---

## 9. Cross-Page Navigation

Pages should provide useful navigation between related workflows.

Examples:

- Dashboard to Products & Inventory.
- Low-stock alert to the relevant product.
- Sales Analytics to AI Forecasting.
- Forecasting to Restocking Recommendations when available.
- CSV Import to Sales Analytics after a successful import.

Navigation should reduce unnecessary steps.

---

## 10. Shared UI Components

Reusable UI components may include:

- Page headers.
- Metric cards.
- Status indicators.
- Confirmation messages.
- Empty-state messages.
- Validation summaries.
- Reusable data tables.
- Chart helpers.

Reusable components should be introduced when they reduce duplication.

Avoid building a complex component system before it is needed.

---

## 11. Page-Level Error Handling

Each page should handle its own presentation-level errors.

However, validation and business rules should remain in their appropriate application or domain layers.

The UI should display useful messages without duplicating business logic.

---

## 12. Page Completion Criteria

A page should not be considered complete merely because it renders.

It should:

- Display the required information.
- Support its documented interactions.
- Validate user input.
- Handle empty states.
- Handle expected errors.
- Use the correct application services.
- Follow the approved business rules.
- Pass relevant tests.

---

## 13. Open Decisions

- Exact page layout.
- Final filters for each page.
- Product detail view requirements.
- Whether analytics includes historical training data.
- Whether forecasting and recommendations share one page.
- Whether import history is displayed.
- Exact shared component list.

---

## 14. Related Documentation

- [UI Overview](ui-overview.md)
- [Dashboard Specification](dashboard-specification.md)
- [Features](../01-product/features.md)
- [User Flows](../01-product/user-flows.md)
- [Business Rules](../01-product/business-rules.md)
- [Acceptance Criteria](../01-product/acceptance-criteria.md)