
# Model Evaluation

## 1. Purpose

This document defines how demand forecasting models are evaluated in SmartStock AI.

The evaluation process measures how close predicted demand values are to actual sales observations.

It provides evidence for comparing candidate models and selecting a suitable forecasting approach.

No model should be described as accurate without measured evaluation results.

---

## 2. Evaluation Objectives

The evaluation process should:

- Measure prediction errors.
- Compare candidate models.
- Compare ML models against simple baselines.
- Detect overfitting.
- Evaluate performance on future time periods.
- Support evidence-based model selection.

---

## 3. Evaluation Strategy

The project will use chronological evaluation.

Historical observations are divided into ordered time periods.

Conceptual example:

```text
Historical Timeline
---------------------------------------------------->

|--------- Training ---------|-- Validation --|-- Test --|
```

### Training Set

Used to fit candidate models.

### Validation Set

Used to compare models and select model configurations.

### Test Set

Used for final evaluation after model selection.

The test set should not influence model selection or hyperparameter tuning.

## 4. Evaluation Metrics

The primary evaluation metrics are MAE and RMSE.

### 4.1 Mean Absolute Error (MAE)

MAE calculates the average absolute difference between actual and predicted values.

Formula:

MAE = (1 / n) * sum(|actual - predicted|)

Interpretation:

If MAE is 3.0, the average absolute prediction error is 3 units.

MAE is easy to interpret because it uses the same unit as the target variable.

### 4.2 Root Mean Squared Error (RMSE)

RMSE calculates the square root of the average squared prediction errors.

Formula:

RMSE = sqrt((1 / n) * sum((actual - predicted)^2))

Interpretation:

RMSE penalizes large prediction errors more heavily than MAE.

It is useful for identifying models that occasionally produce large forecasting mistakes.

## 5. Baseline Comparison

Every candidate ML model should be compared against a baseline.

Potential baselines:

- Naive Forecast.
    
- Historical Average.
    

A complex model should not be selected unless it provides a meaningful benefit over the baseline.

If the model does not improve performance, the project should investigate:

- Feature quality.
    
- Data quality.
    
- Forecasting horizon.
    
- Model suitability.
    
- Baseline definition.
    

## 6. Evaluation by Product

Overall metrics may hide differences between products.

Where practical, calculate evaluation metrics for individual products or product groups.

This helps identify:

- Products with predictable demand.
    
- Products with highly variable demand.
    
- Products with insufficient history.
    
- Products for which the model performs poorly.
    

The final reporting approach depends on the selected model granularity.

## 7. Actual vs Predicted Analysis

The project should visualize actual and predicted demand over time.

The comparison should help identify:

- Underprediction.
    
- Overprediction.
    
- Sudden demand changes.
    
- Seasonal patterns.
    
- Systematic forecasting errors.
    

Example visualization:

```
Actual Demand vs Predicted Demand
```

The chart must use real evaluation outputs.

Illustrative values must never be presented as actual model performance.

## 8. Residual Analysis

A residual is the difference between actual and predicted demand.

Conceptually:

residual = actual - predicted

Residual analysis may help identify:

- Consistent underprediction.
    
- Consistent overprediction.
    
- Large isolated errors.
    
- Patterns not captured by the model.
    

A model should not be evaluated using a single metric alone when additional analysis is practical.

## 9. Overfitting Considerations

Overfitting occurs when a model performs well on training data but poorly on unseen data.

The project should compare training and validation performance.

Potential warning signs:

- Very low training error.
    
- Much higher validation error.
    
- Unstable results across time periods.
    

A more complex model is not automatically a better model.

## 10. Data Leakage Checks

Evaluation must verify that:

- Training data comes before validation data.
    
- Validation data comes before test data.
    
- Future sales are not used in features.
    
- Rolling features use past observations only.
    
- Test data is not used during model selection.
    
- Preprocessing transformations are fitted appropriately.
    

A model evaluation result is unreliable if data leakage exists.

## 11. Model Selection Criteria

The selected model should be evaluated using:

1. Validation MAE.
    
2. Validation RMSE.
    
3. Improvement over baseline.
    
4. Performance stability.
    
5. Computational requirements.
    
6. Suitability for the required forecasting horizon.
    

The final test results should be reported separately.

The project should document why a model was selected.

## 12. Evaluation Report

The evaluation report should include:

- Dataset reference.
    
- Evaluation period.
    
- Model name.
    
- Model configuration.
    
- Feature set.
    
- MAE.
    
- RMSE.
    
- Baseline metrics.
    
- Comparison results.
    
- Important limitations.
    
- Model selection decision.
    

Example report structure:

|Model|MAE|RMSE|
|---|---|---|
|Naive Forecast|Measured value|Measured value|
|Historical Average|Measured value|Measured value|
|Linear Regression|Measured value|Measured value|
|Random Forest|Measured value|Measured value|

The table must be populated only with actual evaluation results.

## 13. Testing Requirements

Evaluation code should be tested with small datasets where expected metric values can be calculated manually.

Tests should verify:

- MAE calculation.
    
- RMSE calculation.
    
- Correct actual and prediction alignment.
    
- Empty input handling.
    
- Invalid input handling.
    
- Chronological split behavior.
    
- Baseline comparison logic.
    

## 14. Limitations

Evaluation metrics measure performance on historical data.

They do not guarantee future performance.

Forecast quality may change due to:

- New products.
    
- Promotions.
    
- Seasonal changes.
    
- Unexpected events.
    
- Supply limitations.
    
- Changes in customer behavior.
    

The application should communicate predictions as estimates.

## 15. Open Decisions

- Final chronological split dates.
    
- Evaluation frequency.
    
- Whether to report metrics per product.
    
- Whether additional metrics are necessary.
    
- Final model selection thresholds.
    
- How to handle unstable product-level performance.
    

## 16. Related Documentation

- [ML Overview](https://ml-overview.md?utm_source=chatgpt.com)
    
- [Forecasting Strategy](https://forecasting-strategy.md?utm_source=chatgpt.com)
    
- [Model Training](https://model-training.md?utm_source=chatgpt.com)
    
- [Feature Engineering](https://feature-engineering.md?utm_source=chatgpt.com)
    
- [Prediction Logic](https://prediction-logic.md?utm_source=chatgpt.com)

---

## 17. Implementation Status — Candidate Evaluation Results (TASK-030, 2026-11-09)

Implemented in `src/smartstock/ml/training.py`, tested by
`tests/test_ml_training.py` (16 tests). Workflow per model-training §7:
DEC-056 windows, features built on the shared chronology (per-row
transforms only — no leakage path from validation into fitting), each
candidate fit **only** on training rows, validation scored one step
ahead exactly like the baselines so the DEC-027 comparison is
like-for-like (18,300 predictions each).

Measured results — Validation 2016, store 1, pooled MAE/RMSE:

| Model | MAE | RMSE | Beats naive (10.270)? | Beats MA-7 (8.077)? |
|---|---|---|---|---|
| Naive Forecast | 10.270 | 13.761 | — | — |
| Historical Average (7-day) | 8.077 | 10.556 | — | — |
| Historical Average (30-day) | 8.298 | 10.915 | — | — |
| Linear Regression | **6.482** | **8.387** | Yes | Yes |
| Random Forest (200 trees, min_samples_leaf 5, seed 2026) | 6.033 | 7.785 | Yes | Yes |

Both supervised candidates **pass the DEC-027 floor** (beat every
baseline on validation MAE). Random Forest edges Linear Regression by
0.449 MAE (Linear Regression is ≈7.4% worse) and also wins RMSE — the
gap **exceeds** DEC-027's 5% "prefer simpler" band, so on validation
evidence alone the Random Forest is the stronger candidate. The final
selection (TASK-031) is made with the project owner, weighing this
margin against interpretability and recursive-multi-step stability
(DEC-025).

Per-product mean errors (§6 of this doc): the worst item is **15** for
both candidates (Linear Regression 9.914 MAE, Random Forest 9.349) —
item 15 is also the highest-mean-demand item (79.7/day, see the data
exploration doc), so its absolute errors are naturally larger;
proportional difficulty appears roughly even.

Random-seed reproducibility (model-training §9): results repeat under
fixed `random_state=2026` up to parallel float summation order
(≈1e-15); the seed is recorded in each candidate report. The test
window (2017) remains untouched — it is evaluated once at final model
selection (TASK-031).