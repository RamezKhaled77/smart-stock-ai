
# Prediction Logic

## 1. Purpose

This document defines how SmartStock AI generates future demand predictions and makes those predictions available to the restocking recommendation system.

It describes the inference workflow after a forecasting model has been trained and saved.

---

## 2. Prediction Inputs

The prediction component may require:

- A trained model artifact.
- Historical sales observations.
- Product or source identifiers.
- Forecasting horizon.
- Required feature configuration.

The exact input structure depends on the selected model.

The prediction component must validate all required inputs before generating forecasts.

---

## 3. Prediction Workflow

The proposed workflow is:

```text
User Selects Product
        |
        v
Select Forecast Horizon
        |
        v
Retrieve Historical Sales
        |
        v
Validate Historical Data
        |
        v
Load Trained Model
        |
        v
Prepare Latest Features
        |
        v
Generate Prediction
        |
        v
Validate Prediction Output
        |
        v
Return Forecast Results
        |
        v
Restock Recommendation Service
```

The prediction workflow must not train the model during normal page rendering.

## 4. Model Loading

The prediction component should load the selected model artifact.

Expected behavior:

- Check whether the artifact exists.
    
- Load the artifact from a trusted location.
    
- Validate required metadata when available.
    
- Handle incompatible artifacts.
    
- Return a clear error when the model cannot be loaded.
    

The system should avoid loading the same model repeatedly when a safe caching strategy is available.

## 5. Historical Data Retrieval

The prediction component must retrieve enough historical observations to generate all required features.

For example:

- lag_1 requires at least one previous observation.
    
- lag_7 requires at least seven previous observations.
    
- rolling_mean_7 requires seven previous observations.
    
- rolling_mean_30 requires thirty previous observations.
    

The exact history requirement depends on the selected feature set.

Data should be sorted chronologically and grouped correctly.

## 6. Feature Preparation

The same feature definitions used during training must be used during prediction.

Important requirements:

- Feature names must match.
    
- Feature order must match when required by the model.
    
- Feature types must be compatible.
    
- Missing historical values must be handled consistently.
    
- Future observations must not be used.
    

The prediction pipeline should reuse the project's feature engineering functions wherever practical.

## 7. Forecast Horizon

**Decided (DEC-026):** The user may select a forecasting horizon among 7, 14, or 30 future days, with 7 days as the default.

The system must validate the selected horizon before generating predictions.

## 8. Multi-Step Prediction

Recursive forecasting is the approved inference strategy (DEC-025):

1. Prepare features for the next day.
    
2. Generate the next-day prediction.
    
3. Validate the predicted value.
    
4. Append the prediction to the temporary forecasting history.
    
5. Recalculate lag and rolling features.
    
6. Generate the following day's prediction.
    
7. Repeat until the horizon is complete.
    

The temporary prediction history must remain separate from actual operational sales records.

Predictions must not be inserted into the sales table as real sales.

## 9. Prediction Output

The prediction component should return structured results.

Proposed logical fields:

|Field|Description|
|---|---|
|product_id|Operational product identifier when mapped|
|forecast_date|Date being predicted|
|predicted_demand|Predicted sales quantity|
|model_version|Model identifier|
|generated_at|Forecast generation timestamp|

The exact structure may use a Pandas DataFrame or another suitable representation.

## 10. Prediction Validation

The system should validate:

- Prediction output is numeric.
    
- Prediction output is finite.
    
- Prediction dates are valid.
    
- The requested horizon is respected.
    
- Required features are available.
    
- The model output contains the expected number of predictions.
    

Regression models may produce negative numerical predictions.

Because demand cannot normally be negative, the application must define an explicit nonnegative output policy.

A possible policy is to clip negative predictions to zero.

This policy must be documented and applied consistently.

## 11. Rounding Predictions

Regression models may produce fractional values.

For example:

```
Predicted demand = 12.7 units
```

The system should preserve the raw numerical prediction for evaluation and analysis.

If whole-unit quantities are needed for inventory decisions, rounding should happen in the appropriate business logic layer.

The selected rounding strategy must be consistent with the approved inventory rules.

## 12. Integration with Restocking Recommendations

The prediction component returns future demand estimates.

The recommendation service may use these estimates with:

- Current stock.
    
- Incoming stock, if supported.
    
- Lead time.
    
- Safety stock.
    
- Target stock.
    

The recommendation service is responsible for applying inventory rules.

The prediction component must not:

- Change current stock.
    
- Create purchase orders.
    
- Modify sales records.
    
- Automatically approve purchases.
    

## 13. Error Handling

The prediction component should handle:

|Situation|Expected Behavior|
|---|---|
|Model artifact missing|Explain that model training is required|
|Invalid model artifact|Report a model loading error|
|Insufficient historical data|Report insufficient history|
|Invalid forecasting horizon|Reject the request|
|Missing required features|Stop prediction and report the issue|
|Invalid model output|Reject the prediction result|
|No matching product history|Explain that no suitable history exists|

Errors should be logged where appropriate and displayed to the user in a clear form.

## 14. Forecast Persistence

Storing generated forecasts is optional.

Possible approaches:

### Generate on Demand

Generate forecasts whenever requested.

Advantages:

- Simple implementation.
    
- No need to maintain historical forecast records.
    

Disadvantages:

- Repeated calculations.
    
- Limited ability to compare previous predictions with actual results.
    

### Store Forecast Results

Save generated predictions with model metadata.

Advantages:

- Historical forecast tracking.
    
- Actual-versus-predicted comparisons.
    
- Better reporting.
    

Disadvantages:

- Additional database complexity.
    
- Requires a forecast versioning and update policy.
    

Status: Open.

The initial implementation may generate forecasts on demand unless forecast history becomes a confirmed requirement.

## 15. Testing Requirements

Prediction tests should verify:

- Successful model loading.
    
- Missing model handling.
    
- Input validation.
    
- Feature consistency.
    
- Correct forecasting horizon.
    
- Recursive prediction behavior if implemented.
    
- Negative prediction handling.
    
- Output validation.
    
- No modification of operational inventory.
    
- No insertion of predictions as actual sales.
    

## 16. Open Decisions

Resolved on 2026-11-04 (see `../07-project-management/decisions.md`):

- ~~Final forecasting horizon~~ → DEC-026 (user-selectable 7/14/30 days, default 7).
- ~~Recursive or direct multi-step prediction~~ → DEC-025 (recursive).
- ~~Forecast persistence~~ → DEC-028 (generate on demand; no persistence in v1).

Resolved at TASK-032/TASK-033 (2026-11-09/10):

- ~~Final model artifact format~~ → joblib + JSON metadata (DEC-057 model, `model_artifacts.py`).
- ~~Minimum historical data requirement~~ → DEC-058 (31 observed days for the model path; MA-7 recursive fallback for 1–30 days; refusal with a clear error at 0 days).
- ~~Negative prediction handling~~ → clip to zero, documented (§10; the Random Forest structurally cannot emit negatives).
- ~~Prediction rounding policy~~ → raw prediction preserved by this layer; rounding happens in business logic (§11).
- Model version selection strategy — single version in v1; recorded in metadata per run.

## 17. Related Documentation

- [ML Overview](https://ml-overview.md?utm_source=chatgpt.com)
    
- [Forecasting Strategy](https://forecasting-strategy.md?utm_source=chatgpt.com)
    
- [Feature Engineering](https://feature-engineering.md?utm_source=chatgpt.com)
    
- [Model Training](https://model-training.md?utm_source=chatgpt.com)
    
- [Model Evaluation](https://model-evaluation.md?utm_source=chatgpt.com)
    
- Business Rules
    
- System Architecture

---

## 18. Implementation Status — Completed (TASK-033, 2026-11-10)

Implemented in `src/smartstock/ml/inference.py`, tested by
`tests/test_ml_inference.py` (20 tests):

- `forecast_product(model, metadata, history, horizon_days, product_id)`
  — validated horizon (DEC-026), validated single-series history
  (numeric, non-negative, one observation per day; duplicates are
  rejected with aggregation guidance), chronological re-sorting.
- DEC-058 paths: ≥31 observed days → Random Forest with recursive
  features (observation-wise, matching training math exactly);
  1–30 days → trailing-7-day average applied recursively (reusing the
  tested baseline function — no duplicated logic); 0 days → explicit
  "No suitable history exists" error (§13).
- §8 recursive loop: each prediction joins the per-call working
  history before the next day's features; operational sales records
  are never touched (§12); output contract per §9 with raw (§11)
  predictions clipped to ≥ 0 (§10, tested with a negative stub) and a
  non-finite-output rejection (§13).
- Verified manually-replicated recursion on a real trained forest and
  a constant-series exactness pin; real-artifact pins forecast item 1
  for 2018-01-01→07 deterministically with the model path.

Remaining for the Forecast page task: the mapping between operational
products and dataset `item` identifiers (DEC-052 kept them separate
deliberately) — to be decided when that page is designed.