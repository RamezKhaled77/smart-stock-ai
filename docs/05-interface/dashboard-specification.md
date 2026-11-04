# Dashboard Specification

## 1. Purpose

The Dashboard is the main overview page of SmartStock AI.

Its purpose is to help users quickly understand the current inventory situation and recent business activity.

The dashboard should highlight important information and provide shortcuts to common workflows.

It should not attempt to display every available detail.

---

## 2. Dashboard Objectives

The dashboard should help users answer these questions:

1. How many products are currently managed?
2. How much stock is available?
3. Which products need attention?
4. What has been sold recently?
5. How are sales changing over time?
6. Which products may need restocking?

Some information depends on the availability of operational data and trained forecasting models.

---

## 3. Dashboard Layout

The proposed layout is:

```text
+------------------------------------------------------+
| Dashboard                                            |
| Overview of your inventory and sales activity        |
+------------------------------------------------------+
| Total Products | Current Stock | Low Stock | Sales   |
+------------------------------------------------------+
|                                                      |
|              Sales Trend Chart                      |
|                                                      |
+------------------------------------------------------+
|                                                      |
| Low-Stock Products          Recent Sales             |
|                                                      |
+------------------------------------------------------+
|                                                      |
| Restocking Overview                                  |
|                                                      |
+------------------------------------------------------+
```

This is a conceptual layout.

The exact Streamlit layout may use columns, containers, or tabs depending on usability.

## 4. Summary Metrics

The dashboard may display the following metrics.

### 4.1 Total Products

Represents the number of active products managed by the application.

### 4.2 Current Stock

Represents the total current stock quantity across applicable products.

The exact calculation must follow the approved inventory model.

### 4.3 Low-Stock Products

Represents the number of products currently classified as low stock.

The classification must follow the approved low-stock or reorder-point rules.

### 4.4 Recent Sales

Represents sales activity during a clearly defined recent period.

The selected period should be displayed to avoid ambiguity.

Metrics must use real operational data.

The application must not display fabricated values when no records exist.

## 5. Sales Trend

A line chart may display sales quantities over time.

### Suggested Information

- Date.
    
- Sales quantity.
    
- Selected date range.
    

### Possible Filters

- Last 7 days.
    
- Last 30 days.
    
- Last 90 days.
    
- Custom date range.
    

The available filters depend on the amount of operational sales data.

The chart should clearly distinguish zero sales from missing observations.

If no sales data is available, display an appropriate empty state.

## 6. Low-Stock Alerts

The dashboard should highlight products that need inventory attention.

### Suggested Table Columns

|Column|Description|
|---|---|
|Product|Product name|
|SKU|Product identifier|
|Current Stock|Available stock|
|Reorder Point|Calculated threshold|
|Status|Inventory status|

### Expected Behavior

- Display relevant low-stock products.
    
- Highlight critical statuses.
    
- Allow navigation to product details or inventory management.
    
- Avoid showing products as low stock without a valid calculation.
    

The exact alert threshold must follow approved business rules.

## 7. Recent Sales

A small table may display recent operational sales.

Suggested columns:

- Product.
    
- Quantity.
    
- Sale date.
    

The table should show a limited number of recent records.

A link or navigation action may open the full Sales Management page.

## 8. Restocking Overview

The dashboard may display a summary of current restocking recommendations.

Potential information:

- Number of products requiring restocking.
    
- Products with the highest suggested quantities.
    
- Products with urgent inventory needs.
    

This section depends on the availability of:

- Valid forecasts.
    
- Current inventory information.
    
- Lead time.
    
- Safety stock or other approved inventory parameters.
    

If recommendations are unavailable, the dashboard should explain why.

The dashboard must not generate purchase orders automatically.

## 9. Data Sources

The dashboard may retrieve information from:

- Product Service.
    
- Inventory Service.
    
- Sales Service.
    
- Analytics Service.
    
- Restock Recommendation Service.
    

Data retrieval and calculations should not be implemented directly inside dashboard UI code.

## 10. Empty States

The dashboard must handle an empty or partially configured application.

### No Products

Display a message encouraging the user to add the first product.

### No Sales

Explain that sales records are required for sales analytics.

### No Historical Dataset

Explain that historical data is required for the proposed forecasting workflow.

### No Trained Model

Explain that the forecasting model must be trained before predictions can be generated.

### No Restocking Recommendations

Explain that recommendations require valid inventory and demand information.

Do not display misleading zero values when the data is actually unavailable.

## 11. Loading and Error States

The dashboard should handle:

- Database retrieval failures.
    
- Missing or incomplete data.
    
- Analytics calculation errors.
    
- Forecasting service failures.
    

Use clear messages.

Avoid displaying raw technical exceptions in the normal user interface.

## 12. Dashboard Performance

The dashboard should load efficiently.

Recommended practices:

- Retrieve only the required data.
    
- Avoid unnecessary repeated database queries.
    
- Aggregate data through reusable services.
    
- Use Streamlit caching only where appropriate.
    
- Avoid loading the full historical training dataset for every dashboard interaction.
    

Cached data must not cause important operational values to become misleadingly outdated.

## 13. Dashboard Acceptance Criteria

The dashboard is considered implemented when:

- It displays accurate summary metrics.
    
- It handles empty product and sales records.
    
- It displays sales trends when data is available.
    
- It highlights low-stock products using approved rules.
    
- It displays recent sales when available.
    
- It handles missing forecasting resources.
    
- It does not display fabricated metrics.
    
- It uses application services rather than direct SQL or duplicated business logic.
    
- It handles expected errors gracefully.
    

Testing and verification must be completed separately from implementation.

## 14. Open Decisions

- Exact summary metrics.
    
- Default sales date range.
    
- Number of recent sales records.
    
- Low-stock display threshold.
    
- Whether restocking recommendations appear on the dashboard.
    
- Whether dashboard filters are global or page-specific.
    
- Final dashboard layout.
    

## 15. Related Documentation

- [UI Overview](https://ui-overview.md?utm_source=chatgpt.com)
    
- [Pages Specification](https://pages-specification.md?utm_source=chatgpt.com)
    
- Features
    
- Business Rules
    
- Acceptance Criteria