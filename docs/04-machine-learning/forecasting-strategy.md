
# Forecasting Strategy

## 1. Purpose

This document defines the proposed demand forecasting strategy for SmartStock AI.

The objective is to estimate future daily demand for products using historical sales observations.

The forecasting strategy should remain simple, measurable, and suitable for the available dataset and development environment.

---

## 2. Forecasting Problem

The forecasting problem is defined as:

Given historical daily sales for a product, predict its expected sales quantity for future dates.

### Forecasting Unit

The proposed forecasting unit is:

One product for one future date.

### Target Variable

The target variable is:

`sales`

It represents the observed number of units sold on a particular date.

### Forecasting Granularity

Daily forecasting is proposed because the historical dataset contains daily observations.

---

## 3. Forecasting Approaches

The project will evaluate multiple forecasting approaches.

### 3.1 Naive Forecast

Uses the latest available observation as the prediction.

For example:

If the most recent observed demand is 10 units, the next forecast may be 10 units.

This provides a simple baseline.

### 3.2 Historical Average

Uses an average of previous demand observations.

Possible averaging windows:

- Previous 7 days.
- Previous 30 days.

The selected window must be validated.

### 3.3 Linear Regression

Uses historical and date-based features to estimate demand.

It provides a simple supervised learning candidate.

### 3.4 Random Forest Regressor

Uses an ensemble of decision trees to model nonlinear relationships between features and demand.

It is a candidate main model because it can capture more complex patterns than simple linear regression.

However, it must demonstrate acceptable validation performance before selection.

---

## 4. Proposed Feature Set

Potential features include:

| Feature | Description |
|---|---|
| day_of_week | Day of the week |
| month | Month number |
| day_of_month | Day of the month |
| lag_1 | Sales from the previous day |
| lag_7 | Sales from seven days earlier |
| rolling_mean_7 | Average sales over the previous seven days |
| rolling_mean_30 | Average sales over the previous thirty days |

The feature set is proposed and may be reduced or expanded after evaluation.

Detailed definitions belong in the feature engineering document.

---

## 5. Forecasting Horizon

The forecasting horizon defines how many future days the model should predict.

Candidate horizons:

- 7 days.
- 14 days.
- 30 days.

**Status:** Decided (DEC-026).

The forecast horizon is user-selectable among 7, 14, or 30 future days, with 7 days as the default.

The horizon choice considers:

- Inventory lead time.
- Available historical data.
- Forecast evaluation results.
- Practical usefulness for restocking decisions.

A longer horizon may increase forecasting uncertainty.

---

## 6. Forecasting Strategy for Multiple Future Days

Generating forecasts for multiple future days requires careful handling of historical features.

For example, a prediction for day 2 may require the predicted demand for day 1 if the model uses recent sales lags.

Two general strategies are possible.

### Recursive Forecasting

1. Generate the next day's prediction.
2. Add that prediction to the available history.
3. Recalculate features.
4. Generate the following day's prediction.
5. Repeat until the requested horizon is reached.

Advantages:
- Reuses a single one-step forecasting model.
- Supports flexible forecast horizons.

Limitations:
- Prediction errors may accumulate across future days.

### Direct Forecasting

Train separate models or prediction strategies for different forecast horizons.

Advantages:
- Can model each horizon independently.

Limitations:
- More training and evaluation complexity.
- Requires additional implementation decisions.

**Status:** Decided (DEC-025). Recursive forecasting is the inference strategy for the initial implementation, because it reuses a single one-step model and supports any allowed horizon (7/14/30 days). Error accumulation over longer horizons must remain documented as a limitation (LIM-008).

Direct forecasting remains a documented alternative; switching to it later requires a new decision superseding DEC-025.

---

## 7. Model Selection

Candidate models should be evaluated using the same chronological validation strategy.

**Selection rules (DEC-027):**

1. Primary metric: validation MAE.
2. A candidate model must beat both baselines (Naive Forecast and Historical Average) on validation MAE to be eligible.
3. RMSE is the tie-breaker when MAE values are effectively equal.
4. If two candidates' validation MAE values are within 5% of each other, prefer the simpler, more understandable model.
5. If no candidate meaningfully beats the baselines, document and investigate rather than forcing a selection.

The selected model should also:

- Produce valid nonnegative demand estimates after applying an explicit output policy.
- Be computationally practical.
- Be understandable enough for the project documentation.

---

## 8. Time-Based Validation

The dataset must be split chronologically.

**Decided split (DEC-056, 2026-11-09):**

```text
Historical Timeline ------------------------------------->

|==== 2013 2014 2015 ====|===== 2016 =====|===== 2017 =====|
        Training              Validation         Test
```

- Training 2013-01-01 → 2015-12-31; Validation 2016 (full calendar year); Test 2017 (full calendar year).
- Model selection uses validation MAE only (DEC-027); the test window is evaluated once at final model selection (TASK-031).
- Random splitting is not appropriate for the primary forecasting evaluation.

## 9. Forecast Output

The forecasting component should return structured results.

Proposed fields:

|Field|Description|
|---|---|
|product_id|Operational product identifier or source mapping|
|forecast_date|Date being predicted|
|predicted_demand|Predicted sales quantity|
|model_version|Model identifier|
|generated_at|Forecast generation timestamp|

These are logical output fields, not a finalized database schema.

## 10. Prediction Constraints

The system should:

- Reject invalid forecasting inputs.
    
- Check whether enough historical observations exist.
    
- Prevent future information from entering model features.
    
- Validate generated predictions.
    
- Avoid silently converting invalid outputs.
    
- Clearly identify the forecasting period.
    

Predicted demand may be fractional because regression models produce continuous values.

If the business layer requires whole units, rounding must follow a documented policy.

The ML model should not silently apply inventory-specific rounding rules.

## 11. Integration with Restocking

Forecasting results are inputs to the recommendation service.

The recommendation service may use:

- Forecasted demand.
    
- Current stock.
    
- Incoming stock, if supported.
    
- Lead time.
    
- Safety stock.
    
- Target stock.
    

The exact formula depends on approved business rules.

The forecast itself must not update inventory.

## 12. Handling Products with Limited History

Some products may not have enough observations for reliable forecasting.

The system should define a minimum history requirement.

Potential behavior:

- Use a simple baseline.
    
- Display a warning.
    
- Mark the forecast as unavailable.
    
- Require additional historical data.
    

The minimum observation count must be determined during implementation and evaluation.

## 13. Open Decisions

Resolved on 2026-11-04 (see `../07-project-management/decisions.md`):

- ~~Final forecasting horizon~~ → DEC-026 (user-selectable 7/14/30, default 7).
- ~~Recursive or direct multi-step forecasting~~ → DEC-025 (recursive).
- ~~Forecast output persistence~~ → DEC-028 (generate on demand, no persistence in v1).

Still to be resolved based on measured evidence or later approval:

- ~~Final forecasting model~~ → DEC-057 (Random Forest, selected by DEC-027 rules at TASK-031).
- ~~Minimum historical observations~~ → measured at TASK-028 (feature set needs 31 observations; inference-time policy decided at TASK-033).
- ~~Final chronological split dates~~ → DEC-056 (Train 2013–2015, Validation 2016, Test 2017).
- Prediction rounding policy (TASK-033).
- Handling new products with no sales history (TASK-033).
    

## 14. Related Documentation

- [ML Overview](https://ml-overview.md?utm_source=chatgpt.com)
    
- [Feature Engineering](https://feature-engineering.md?utm_source=chatgpt.com)
    
- [Model Training](https://model-training.md?utm_source=chatgpt.com)
    
- [Model Evaluation](https://model-evaluation.md?utm_source=chatgpt.com)
    
- [Prediction Logic](https://prediction-logic.md?utm_source=chatgpt.com)
    
- Business Rules