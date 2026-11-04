# Known Limitations

## 1. Purpose

This document records known or expected limitations of SmartStock AI.

Its purpose is to make project constraints visible and prevent the application from presenting uncertain results as guaranteed facts.

Limitations should be updated as implementation and evaluation reveal more information.

---

## 2. Limitation Categories

Use these categories:

| Category | Meaning |
|---|---|
| Data | Limitations caused by available data |
| ML | Limitations caused by forecasting methods |
| Business | Limitations in operational rules |
| Application | Limitations in functionality |
| Performance | Hardware or execution constraints |
| Scope | Features intentionally excluded |
| Evaluation | Limitations in testing or validation |

---

## 3. Data Limitations

### LIM-001: Historical Dataset Does Not Represent Full Inventory Operations

- Category: Data
- Status: Expected
- Description:

The proposed Kaggle Store Item Demand Forecasting dataset contains historical sales information.

It does not provide a complete operational inventory dataset.

Expected missing information includes:

- Current stock.
- Incoming stock.
- Supplier details.
- Purchase orders.
- Product purchase costs.
- Supplier lead times.
- Inventory adjustments.

Impact:

Historical sales data alone cannot provide a complete picture of current inventory.

Mitigation:

Maintain operational inventory information separately in the application.

---

### LIM-002: Dataset Selection Is Not Final

- Category: Data
- Status: Open
- Description:

The Kaggle dataset is currently proposed but must be inspected before final adoption.

Impact:

The actual data structure, quality, and suitability may affect the preprocessing and forecasting implementation.

Mitigation:

Inspect the downloaded files and document the actual findings before building dependent ML functionality.

---

### LIM-003: Historical Sales Are Not Guaranteed to Represent True Demand

- Category: Data
- Status: Expected
- Description:

Recorded sales may not always represent the actual demand for a product.

For example:

- A product may have been unavailable.
- A store may have been closed.
- A product may have been temporarily discontinued.
- Sales may have been affected by unusual events.

Impact:

A model trained on sales data may learn observed sales patterns rather than unconstrained customer demand.

Mitigation:

Clearly describe model predictions as demand estimates based on available historical sales.

Do not claim that the model knows actual unmet demand when stockout information is unavailable.

---

### LIM-004: Limited External Business Information

- Category: Data
- Status: Expected
- Description:

The initial dataset does not necessarily contain pricing, promotions, supplier information, or external market conditions.

Impact:

The model may not explain demand changes caused by these factors.

Mitigation:

Document the limitation and avoid claiming that the initial forecasting model considers information it does not receive.

---

## 4. Machine Learning Limitations

### LIM-005: Forecast Accuracy Is Not Guaranteed

- Category: ML
- Status: Expected
- Description:

Forecasting models estimate future values based on historical patterns.

Unexpected events and changing customer behavior can cause prediction errors.

Impact:

Predictions may differ significantly from actual future sales.

Mitigation:

Evaluate the model using historical validation and test periods.

Display predictions as estimates rather than guaranteed outcomes.

---

### LIM-006: Limited Feature Set

- Category: ML
- Status: Proposed
- Description:

The initial model may use a relatively small set of calendar and historical sales features.

Potential features include:

- Day of week.
- Month.
- Day of month.
- Lagged sales.
- Rolling averages.

Impact:

The model may not capture all important demand drivers.

Mitigation:

Start with simple features and expand only when additional data is available and evaluation supports the change.

---

### LIM-007: Limited Model Complexity

- Category: ML
- Status: Expected
- Description:

The initial implementation prioritizes CPU-friendly models and manageable training workflows.

Impact:

More advanced approaches may outperform the initial models in some situations.

Mitigation:

Use baselines and evaluation results to determine whether the selected model is sufficient.

Do not introduce heavier frameworks without a clear need.

---

### LIM-008: Multi-Step Forecasting Error Accumulation

- Category: ML
- Status: Expected
- Description:

If recursive forecasting is used, future predictions may depend on previous predicted values.

Prediction errors can accumulate across the forecast horizon.

Impact:

Longer-horizon predictions may become less reliable.

Mitigation:

Evaluate performance at different forecast horizons and document the selected inference strategy.

---

### LIM-009: Cold-Start and Insufficient History

- Category: ML
- Status: Expected
- Description:

New products or products with limited historical observations may not have enough information for reliable forecasting.

Impact:

The application may be unable to generate meaningful predictions for every product.

Mitigation:

Define a minimum history requirement and provide clear fallback behavior when supported.

Do not generate misleading forecasts from insufficient data.

---

## 5. Business Logic Limitations

### LIM-010: Restocking Recommendations Depend on Operational Inputs

- Category: Business
- Status: Expected
- Description:

Restocking recommendations require more than historical sales predictions.

They may depend on:

- Current inventory.
- Lead time.
- Safety stock.
- Target stock.
- Incoming inventory.
- Inventory position.

Impact:

Missing or inaccurate operational information can produce misleading recommendations.

Mitigation:

Display recommendations only when required inputs are available and valid.

Clearly identify missing inputs.

---

### LIM-011: No Automatic Purchasing

- Category: Scope
- Status: Accepted
- Description:

The initial application provides restocking recommendations only.

It does not automatically place purchase orders or communicate with suppliers.

Impact:

Users must review and act on recommendations manually.

Mitigation:

Keep recommendations advisory and explain the inputs used.

---

### LIM-012: No Automatic Inventory Reconciliation from Historical Imports

- Category: Business
- Status: Accepted
- Description:

Historical sales imports do not automatically modify current inventory.

Impact:

Users must manage current stock through the approved inventory workflows.

Mitigation:

Keep historical demand records separate from current inventory operations.

---

## 6. Application Scope Limitations

### LIM-013: Initial Single-Store Workflow

- Category: Scope
- Status: Proposed
- Description:

The initial application is designed around a single-store workflow.

Impact:

Multi-branch inventory management is not part of the initial implementation unless explicitly approved.

Mitigation:

Keep the architecture understandable and avoid unnecessary multi-branch functionality.

---

### LIM-014: No POS Integration

- Category: Scope
- Status: Deferred
- Description:

The initial application does not automatically connect to an external Point of Sale system.

Impact:

Sales may need to be entered manually or imported through CSV.

Mitigation:

Support the approved manual sales and CSV workflows.

---

### LIM-015: Limited User and Permission Management

- Category: Scope
- Status: Deferred
- Description:

Advanced user roles and permission management are not part of the initial core scope.

Impact:

The initial application may operate as a simple local or single-user application.

Mitigation:

Avoid introducing complex authentication and authorization systems without a confirmed requirement.

---

## 7. Performance Limitations

### LIM-016: CPU-Based Model Training

- Category: Performance
- Status: Expected
- Description:

The development environment relies on a CPU and integrated graphics.

Impact:

Large or computationally expensive models may take longer to train.

Mitigation:

Use lightweight Scikit-learn models and optimize based on actual measurements.

A dedicated GPU is not required for the proposed initial approach.

---

### LIM-017: Large Dataset Processing

- Category: Performance
- Status: Expected
- Description:

Large historical datasets may increase memory usage and processing time.

Impact:

Repeated full-dataset loading and expensive transformations may slow the application.

Mitigation:

Separate training workflows from normal application usage.

Use caching for appropriate read-only operations.

Use smaller fixtures for ordinary automated tests.

---

## 8. Evaluation Limitations

### LIM-018: Historical Evaluation Does Not Guarantee Future Performance

- Category: Evaluation
- Status: Expected
- Description:

Model performance on historical validation and test periods does not guarantee equivalent accuracy in future periods.

Impact:

Real-world forecasting quality may change over time.

Mitigation:

Document evaluation periods and metrics.

Avoid presenting historical evaluation results as guaranteed future accuracy.

---

### LIM-019: Limited Real-World Validation

- Category: Evaluation
- Status: Expected
- Description:

A public historical dataset may not fully represent the behavior of an actual small Egyptian store.

Impact:

The application may demonstrate forecasting and inventory concepts without proving performance in a real business environment.

Mitigation:

Describe the project as an educational prototype unless real-world validation is performed.

---

## 9. Limitation Management

When a new limitation is discovered:

1. Assign a unique limitation ID.
2. Describe the issue.
3. Identify its category.
4. Explain its impact.
5. Record its current status.
6. Document mitigation where possible.
7. Update related project documentation.

Do not hide limitations merely to make the project appear more advanced.

A clearly documented limitation is preferable to an unsupported claim.

---

## 10. Final Reporting Guidelines

When presenting the project:

- Distinguish forecasts from actual sales.
- Distinguish sales history from actual customer demand.
- Distinguish restocking recommendations from automatic purchasing.
- Distinguish historical evaluation from guaranteed future accuracy.
- Explain the dataset's limitations.
- Report the actual model evaluation results.
- Avoid claiming production readiness without appropriate evidence.

The project should demonstrate a practical and honest use of AI for inventory decision support.