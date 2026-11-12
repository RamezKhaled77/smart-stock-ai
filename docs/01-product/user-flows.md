# SmartStock AI — User Flows

## 1. Purpose

This document describes the main user journeys in SmartStock AI.

It explains how users interact with the application to manage products, record sales, import data, review forecasts, and make restocking decisions.

These flows describe the intended behavior, not the final UI design.

Detailed page layouts are documented in:

`../05-interface/pages-specification.md`

---

## 2. Primary User

The initial application assumes one primary user:

**Business Owner / Inventory Manager**

The user is responsible for:

- Managing products.
- Recording sales.
- Maintaining inventory quantities.
- Reviewing sales information.
- Understanding future demand.
- Reviewing restocking recommendations.

Multiple roles and permission levels are outside the initial scope.

---

# 3. Application Entry Flow

## Goal

Allow the user to open the application and reach the main dashboard.

### Flow

1. User starts the application.
2. System initializes the required services.
3. System checks database availability.
4. System loads required application information.
5. Dashboard is displayed.

### Possible Outcomes

**Success:**

- Dashboard loads successfully.
- Main navigation is available.

**Failure:**

- Database is unavailable.
- Required data cannot be loaded.
- Application configuration is invalid.

The application should display an understandable error instead of failing silently.

---

# 4. Product Creation Flow

## Goal

Allow the user to add a new product.

### Flow

1. User opens Product Management.
2. User selects Add Product.
3. System displays the product form.
4. User enters product information.
5. User submits the form.
6. System validates the information.
7. System checks product identifier uniqueness.
8. System saves the product.
9. System displays a success message.
10. The product appears in the product list.

### Validation Cases

- Missing required fields.
- Invalid numeric values.
- Negative stock quantity.
- Duplicate product identifier.

### Expected Result

A valid product is created and becomes available to inventory and sales modules.

---

# 5. Product Update Flow

## Goal

Allow the user to edit product information.

### Flow

1. User opens Product Management.
2. User selects a product.
3. System displays current product information.
4. User edits one or more fields.
5. User submits changes.
6. System validates the new values.
7. System saves the changes.
8. System displays the updated product.

### Expected Result

The product information is updated without affecting unrelated records.

---

# 6. Inventory Adjustment Flow

## Goal

Allow the user to update current inventory quantities.

### Flow

1. User opens Inventory Management.
2. User selects a product.
3. System displays current stock.
4. User chooses an adjustment action.
5. User enters the adjustment quantity.
6. User provides a reason if required.
7. System validates the adjustment.
8. System updates inventory.
9. System displays the new stock quantity.

### Important Notes

The system must distinguish between:

- Stock received.
- Stock removed.
- Damaged or lost stock.
- Manual correction.

The final adjustment types and history requirements are still open for approval.

---

# 7. Manual Sales Recording Flow

## Goal

Allow the user to record a new sale.

### Flow

1. User opens Sales Management.
2. User selects Record Sale.
3. System displays the sales form.
4. User selects a product.
5. User enters the quantity sold.
6. User enters or confirms the sale date.
7. User submits the form.
8. System validates the transaction.
9. System checks inventory availability according to approved rules.
10. System records the sale.
11. System updates inventory according to the approved stock policy.
12. System displays confirmation.

### Validation Cases

- Unknown product.
- Missing quantity.
- Invalid date.
- Zero or negative quantity.
- Insufficient stock.

### Expected Result

The sale is recorded and inventory remains consistent.

---

# 8. CSV Import Flow

## Goal

Allow the user to import historical sales information.

### Flow

1. User opens Sales Management.
2. User selects Import CSV.
3. User uploads a CSV file.
4. System reads the file.
5. System inspects available columns.
6. System checks required columns.
7. System validates each row.
8. System identifies invalid records.
9. System identifies duplicates where possible.
10. System displays an import preview.
11. User reviews the validation summary.
12. User confirms the import.
13. System imports valid records according to the approved import policy.
14. System displays the import result.

### Possible Outcomes

**Valid File:**

- Import succeeds.
- Imported records become available for analysis.

**Partially Valid File:**

- The user sees valid and invalid row counts.
- The user follows the approved partial-import policy.

**Invalid File:**

- Import is rejected.
- The user receives understandable validation errors.

### Important Notes

The import operation must protect data consistency.

The system should avoid unexpected partial updates.

The exact duplicate-handling and partial-import policies must be defined before implementation.

---

# 9. Sales Analysis Flow

## Goal

Allow the user to understand historical sales activity.

### Flow

1. User opens Dashboard or Sales Analytics.
2. User selects a date range.
3. User optionally filters by product.
4. System retrieves matching sales information.
5. System calculates approved metrics.
6. System displays summaries and charts.
7. User reviews the results.

### Possible Insights

- Daily sales quantities.
- Weekly sales patterns.
- Monthly sales patterns.
- Top-selling products.
- Changes in product demand.

Monetary insights require approved price data.

---

# 10. Demand Forecasting Flow

## Goal

Allow the user to view future demand predictions.

### Flow

1. User opens Forecasting.
2. User selects a product or forecasting scope.
3. User selects an available forecast horizon, if supported.
4. System checks whether sufficient historical data exists.
5. System loads the required forecasting model.
6. System prepares prediction features.
7. System generates predictions.
8. System validates prediction outputs.
9. System displays the results.

**Implementation notes (v1):** forecasting is product-driven — the
product must be linked to a dataset item (DEC-060) and predictions are
computed from that item's imported history only. Items with fewer than
31 observed days use the documented MA-7 fallback path (DEC-058), shown
in the method caption; items with no history get an explicit
explanation instead of a forecast. The page also displays the stored
training-time evaluation metrics (DEC-062).

### Possible Outcomes

**Successful Forecast:**

- Predictions are displayed.
- Forecast metadata is available.

**Insufficient Data:**

- The system explains why forecasting cannot be performed.

**Model Unavailable:**

- The system displays an appropriate error.
- It must not present fabricated predictions.

### Expected Result

The user can understand estimated demand for the selected product and period.

---

# 11. Restocking Recommendation Flow

## Goal

Help the user decide which products need replenishment and how much stock may be required.

### Flow

1. User opens Restocking Recommendations.
2. System retrieves current inventory information.
3. System retrieves relevant demand forecasts.
4. System retrieves approved inventory parameters.
5. System calculates reorder status.
6. System calculates recommended order quantities.
7. System identifies products requiring attention.
8. System displays recommendation details.
9. User reviews the results.
10. User decides whether to take action.

### Recommendation Information

Each recommendation may include:

- Product name.
- Current stock.
- Forecast demand.
- Lead time.
- Safety stock.
- Reorder point.
- Recommended order quantity.
- Reason for recommendation.

### Important Notes

The system provides advisory recommendations.

It does not automatically purchase or order products.

---

# 12. Dashboard Review Flow

## Goal

Allow the user to understand the overall inventory situation.

### Flow

1. User opens the Dashboard.
2. System retrieves summary information.
3. System calculates approved metrics.
4. System displays inventory indicators.
5. System displays sales summaries.
6. System highlights low-stock products.
7. System highlights important forecast information.
8. User navigates to detailed modules when necessary.

---

# 13. Error and Recovery Flows

The application should handle common errors clearly.

## Database Error

- Detect the database operation failure.
- Avoid reporting false success.
- Display an understandable message.
- Preserve data consistency.

## Invalid User Input

- Reject invalid input.
- Explain which fields need correction.
- Preserve other valid form values when practical.

## CSV Validation Error

- Display the problematic row or field.
- Explain the validation failure.
- Do not silently discard information.

## Forecasting Error

- Identify whether the issue is insufficient data, unavailable model, or invalid input.
- Do not display invalid or fabricated predictions.

## Missing Product

- Display a clear not-found message.
- Avoid modifying unrelated records.

---

# 14. User Flow Design Principles

All user flows should follow these principles:

1. Keep common operations short.
2. Validate input before saving.
3. Provide clear feedback after important actions.
4. Avoid unexpected inventory changes.
5. Make errors understandable.
6. Allow users to review recommendations before acting.
7. Never present a forecast as a guaranteed result.
8. Avoid destructive actions without clear confirmation.

---

# 15. Related Documentation

- `features.md`
- `business-rules.md`
- `acceptance-criteria.md`
- `../05-interface/ui-overview.md`
- `../05-interface/pages-specification.md`
- `../06-development/testing-strategy.md`