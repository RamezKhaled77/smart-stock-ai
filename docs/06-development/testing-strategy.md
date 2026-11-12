# Testing Strategy

## 1. Purpose

This document defines how SmartStock AI should be tested during development and before final delivery.

The goal is to verify that:

- Business rules work correctly.
- Data is processed safely.
- Database operations are reliable.
- Forecasting logic is valid.
- ML evaluation avoids data leakage.
- Restocking recommendations are correct.
- Streamlit workflows behave as expected.

Testing is part of implementation, not a final optional activity.

---

## 2. Testing Principles

### 2.1 Test Behavior, Not Just Code Execution

A function running without an exception does not prove that its output is correct.

Tests should verify expected behavior using explicit inputs and expected outputs.

### 2.2 Test Business Logic Independently

Business rules should be testable without running Streamlit.

Prefer testing pure functions and application services independently.

### 2.3 Use Small and Controlled Test Data

Most automated tests should use small fixtures or synthetic datasets.

Do not require the full Kaggle dataset to run ordinary unit tests.

### 2.4 Avoid False Confidence

Do not:

- Mock every dependency in a way that hides real integration problems.
- Claim tests passed without running them.
- Ignore failing tests without documenting why.
- Use training data as proof of forecasting quality.
- Treat successful application startup as proof that all features work.

### 2.5 Keep Tests Reproducible

Tests should produce consistent results.

Avoid depending on:
- Unstable external APIs.
- Internet connectivity.
- Uncontrolled current dates.
- Local user-specific files.
- Existing production-like database contents.

---

## 3. Testing Tools

Proposed testing tools:

| Tool | Purpose |
|---|---|
| pytest | Main testing framework |
| pytest-cov | Optional code coverage reporting |
| pandas testing utilities | DataFrame comparison |
| SQLite in-memory database | Isolated database tests |
| Streamlit manual testing | Interface verification |

The final dependency list should be maintained in the project's dependency documentation.

---

## 4. Testing Levels

### 4.1 Unit Testing

Unit tests verify small independent functions.

Examples:

- Input validation.
- Inventory calculations.
- Sales calculations.
- Date feature generation.
- Lag feature generation.
- Rolling average calculations.
- Forecast evaluation metrics.
- Restocking calculations.
- Data transformation functions.

Unit tests should be fast and independent.

### 4.2 Integration Testing

Integration tests verify that multiple components work together.

Examples:

- Repository and SQLite interactions.
- Service and repository interactions.
- Sales recording and inventory updates.
- CSV import and persistence.
- Forecast service and saved model loading.
- Recommendation service and inventory data.

Use temporary or in-memory databases where possible.

### 4.3 UI Testing

UI testing verifies the behavior of the Streamlit application.

For the initial project, manual testing may be used for important UI workflows.

Examples:

- Navigation between pages.
- Form submission.
- Validation messages.
- Data display.
- CSV upload.
- Forecast generation.
- Empty states.
- Error states.

Automated UI testing may be introduced later if it provides sufficient value.

### 4.4 ML Testing

ML testing verifies the correctness of the forecasting pipeline.

Examples:

- Feature generation.
- Chronological splitting.
- Leakage prevention.
- Model training.
- Model serialization and loading.
- Prediction output validation.
- Evaluation metric calculations.

A model that trains successfully is not necessarily a useful model.

Model quality must be evaluated separately.

---

## 5. Test Organization

Proposed test directory:

```text
tests/
├── conftest.py
├── unit/
│   ├── test_validation.py
│   ├── test_inventory.py
│   ├── test_sales.py
│   ├── test_preprocessing.py
│   ├── test_features.py
│   ├── test_metrics.py
│   └── test_recommendations.py
├── integration/
│   ├── test_database.py
│   ├── test_repositories.py
│   ├── test_sales_workflow.py
│   ├── test_csv_import.py
│   └── test_forecasting_service.py
└── fixtures/
    ├── sample_sales.csv
    └── sample_products.csv
```


This is a proposed structure.

Adjust it to match the final project structure without creating unnecessary complexity.

## 6. Unit Testing Requirements

### 6.1 Input Validation

Test:

- Valid product fields.
    
- Missing required fields.
    
- Invalid numeric values.
    
- Invalid dates.
    
- Invalid sales quantities.
    
- Invalid product identifiers.
    

Expected behavior:

Invalid input should be rejected with clear, predictable errors.

### 6.2 Inventory Logic

Test:

- Stock retrieval.
    
- Positive stock adjustments.
    
- Negative adjustments where permitted.
    
- Zero adjustments.
    
- Invalid quantities.
    
- Negative stock behavior according to the approved policy.
    

**Confirmed policy (DEC-034):** Negative stock is never allowed. Tests must verify that no inventory operation can drive current stock below zero.

### 6.3 Sales Logic

Test:

- Valid sales records.
    
- Invalid sales quantities.
    
- Unknown products.
    
- Date validation.
    
- Approved inventory updates.
    
- Insufficient stock behavior.
    
- Historical import behavior.
    

### 6.4 Data Preprocessing

Test:

- Correct column validation.
    
- Date parsing.
    
- Missing values.
    
- Invalid data types.
    
- Duplicate records.
    
- Negative sales values.
    
- Empty datasets.
    

Expected behavior must follow the data preprocessing specification.

### 6.5 Feature Engineering

Test:

- Day-of-week features.
    
- Month features.
    
- Day-of-month features.
    
- Lag 1.
    
- Lag 7.
    
- Rolling mean 7.
    
- Rolling mean 30.
    
- Insufficient historical observations.
    
- Group boundaries between different products or stores.
    

Important:

Lag and rolling calculations must never mix observations from different product or store groups.

Rolling features must exclude the current target value.

### 6.6 Evaluation Metrics

Test:

- MAE calculation.
    
- RMSE calculation.
    
- Equal-length prediction and target inputs.
    
- Empty input handling.
    
- Invalid numeric values.
    
- Correct metric values for known examples.
    

## 7. Integration Testing Requirements

### 7.1 Database

Verify:

- Database initialization.
    
- Table creation.
    
- Record insertion.
    
- Record retrieval.
    
- Record updates.
    
- Approved deletion behavior.
    
- Transaction handling.
    
- Persistence across connections.
    

### 7.2 Product and Inventory Workflow

Verify:

1. Create a product.
    
2. Retrieve the product.
    
3. Update its information.
    
4. Retrieve the updated product.
    
5. Apply an approved stock adjustment.
    
6. Verify the persisted stock value.
    

### 7.3 Sales Workflow

Verify:

1. Create or select a valid product.
    
2. Record a valid sale.
    
3. Verify the stored sale.
    
4. Verify the resulting stock according to the approved business rules.
    

Also verify that failed sales do not leave partially applied changes.

### 7.4 CSV Import

Verify:

- Valid CSV import.
    
- Missing required columns.
    
- Invalid dates.
    
- Invalid quantities.
    
- Duplicate records.
    
- Partially invalid files.
    
- Empty files.
    
- Persistence behavior.
    
- Import summary accuracy.
    

Verify explicitly that historical sales imports do not modify current inventory unless an approved reconciliation workflow exists.

### 7.5 Forecasting Integration

Verify:

- Model artifact loading.
    
- Input preparation.
    
- Prediction generation.
    
- Output structure.
    
- Error handling for missing artifacts.
    
- Error handling for insufficient history.
    

Forecasting must not modify inventory or create fake sales records.

## 8. Machine Learning Testing

### 8.1 Synthetic Test Dataset

Use a small deterministic dataset with known behavior.

Example:

```
import pandas as pddef create_sample_sales():    dates = pd.date_range(        start="2025-01-01",        periods=40,        freq="D"    )    return pd.DataFrame({        "date": dates,        "store": 1,        "item": 1,        "sales": range(10, 50)    })
```

This fixture is only an example.

Adapt it to the final dataset structure and feature-engineering implementation.

### 8.2 Chronological Split Validation

Verify that:

- Training observations precede validation observations.
    
- Validation observations precede test observations.
    
- Split boundaries are chronological.
    
- Future target values are not included in historical features.
    

Do not use random train-test splitting for the primary time-series evaluation.

### 8.3 Data Leakage Checks

Explicitly test:

- Rolling features use historical values only.
    
- Lag features use previous observations only.
    
- Product and store groups are isolated.
    
- Future observations do not affect past features.
    
- Preprocessing does not use future target information.
    

### 8.4 Model Training

Verify:

- Training runs on valid input data.
    
- The model produces valid predictions.
    
- Model artifacts are saved successfully.
    
- Saved artifacts can be loaded.
    
- Required metadata is available.
    

### 8.5 Forecast Inference

Verify:

- Predictions have the expected length.
    
- Predictions contain valid numeric values.
    
- Prediction dates are correct.
    
- Supported horizons are respected.
    
- Recursive forecasting behaves as expected if implemented.
    

Do not assume that predictions must always be positive without reviewing the approved prediction post-processing policy.

## 9. Restocking Recommendation Tests

The recommendation engine must be tested independently of the ML model.

Test:

- Demand input.
    
- Lead time.
    
- Safety stock.
    
- Inventory position.
    
- Reorder point.
    
- Target stock.
    
- Recommended order quantity.
    
- Missing parameters.
    
- Zero demand.
    
- Insufficient or invalid inputs.
    

Example proposed formula:

`Reorder Point = Average Daily Demand * Lead Time + Safety Stock`

Example proposed formula:

`Recommended Order Quantity = max(0, Target Stock - Inventory Position)`

These formulas must be updated if the final business rules change.

Verify that generating a recommendation does not change current stock.

## 10. Streamlit Manual Testing Checklist

### Application Startup

- Application starts successfully.
    
- Navigation is available.
    
- No unexpected runtime errors appear.
    

### Dashboard

- Metrics load correctly.
    
- Empty database behavior is understandable.
    
- Charts display valid data.
    
- Low-stock information matches business rules.
    

### Products and Inventory

- Product listing works.
    
- Product creation works.
    
- Product editing works.
    
- Invalid input is rejected.
    
- Inventory values are accurate.
    

### Sales Management

- Sales can be recorded.
    
- Invalid sales are rejected.
    
- Sales history is displayed.
    
- Approved inventory behavior works.
    

### CSV Import

- Valid files can be uploaded.
    
- Invalid files show useful errors.
    
- Preview works if implemented.
    
- Import summary is correct.
    
- Historical imports do not unexpectedly modify inventory.
    

### Sales Analytics

- Sales trends are accurate.
    
- Filters work where supported.
    
- Empty periods are handled.
    

### AI Forecasting

- Forecasting page loads.
    
- Supported forecasts can be generated.
    
- Insufficient history is handled.
    
- Prediction values and dates are displayed correctly.
    
- Model loading errors are handled.
    

### Restocking Recommendations

- Recommendations follow approved formulas.
    
- Required parameters are available.
    
- Missing inputs are explained.
    
- Recommendations do not modify inventory.
    

## 11. Test Data Management

Use:

- Small synthetic datasets.
    
- Temporary SQLite databases.
    
- Controlled CSV fixtures.
    
- Deterministic input values.
    

Avoid using real operational data in automated tests.

Do not commit large datasets or generated model artifacts unless the project explicitly requires them.

Test fixtures must be small enough to run quickly.

## 12. Test Execution

The basic test command (the package lives under `src/`, so the path
must be on `PYTHONPATH`; tests are organized flat under `tests/` by
layer — there is no separate `tests/unit` layout):

```
PYTHONPATH=src python -m pytest
```

To run one test file while developing:

```
PYTHONPATH=src python -m pytest tests/test_services_analytics.py
```

To run the integration tests (real `app.py` startup and end-to-end
workflows):

```
PYTHONPATH=src python -m pytest tests/integration
```

If coverage is installed:

```
PYTHONPATH=src python -m pytest --cov
```

## 13. Failure Handling

When a test fails:

1. Read the failure details.
    
2. Identify whether the issue is in the implementation, test, or specification.
    
3. Check related business rules.
    
4. Fix the root cause when clear.
    
5. Re-run the affected test.
    
6. Re-run the relevant test suite.
    
7. Record unresolved issues.
    

Do not change a test merely to make incorrect implementation pass.

If the expected behavior is unclear because a business rule is unresolved, record the question instead of inventing expected behavior.

## 14. Definition of Test Completion

A feature may be marked Tested when:

- Relevant automated tests have been executed.
    
- All required tests pass.
    
- Relevant integration behavior has been checked.
    
- Known failures are documented.
    

A feature may be marked Verified when:

- Its acceptance criteria are satisfied.
    
- Its user-facing behavior has been checked.
    
- Important edge cases are covered.
    
- No unresolved critical issue remains.
    

Test results must reflect actual execution.

Never report an unexecuted test as passed.