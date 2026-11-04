# Machine Learning Overview

## 1. Purpose

This document describes the role of Machine Learning in SmartStock AI.

The main objective is to predict future product demand using historical sales data.

The application uses these predictions to support inventory planning and generate restocking recommendations.

Machine Learning is a decision-support component, not an automatic inventory management system.

---

## 2. Problem Definition

SmartStock AI addresses a demand forecasting problem.

Given historical sales observations for a product, the system attempts to estimate the expected sales quantity for future dates.

### Input

Historical sales information, including:

- Sales dates.
- Product identifiers.
- Historical sales quantities.
- Date-based features.
- Historical demand patterns.

### Output

Predicted demand for future dates.

Example:

| Date | Predicted Demand |
|---|---:|
| 2026-11-02 | 12 |
| 2026-11-03 | 15 |
| 2026-11-04 | 13 |
| 2026-11-05 | 17 |

The values above are illustrative examples, not actual model results.

---

## 3. Machine Learning Scope

The initial ML component focuses on:

1. Historical sales analysis.
2. Data preprocessing.
3. Feature engineering.
4. Demand forecasting.
5. Model evaluation.
6. Future demand prediction.

The system does not initially attempt to predict:

- Product prices.
- Supplier delivery delays.
- Customer behavior.
- Product profitability.
- Market trends from external sources.

These topics may be considered in future versions if suitable data becomes available.

---

## 4. Machine Learning Approach

The project will use traditional supervised machine learning.

The forecasting problem will initially be approached as a regression task.

The model receives historical and time-based features and predicts a numerical demand value.

Deep learning is not required for the initial implementation.

### Candidate Models

The following approaches may be evaluated:

- Naive Forecast.
- Historical Average.
- Linear Regression.
- Random Forest Regressor.

These are candidate approaches, not final model selections.

The final choice must be based on validation results.

---

## 5. Baseline Models

A baseline provides a simple reference for evaluating more advanced models.

### Naive Forecast

Predicts that future demand will be equal to the most recent observed demand.

### Historical Average

Predicts demand using an average of previous observations.

The exact averaging window must be defined in the forecasting strategy.

A machine learning model should demonstrate meaningful improvement over a suitable baseline before being selected.

---

## 6. Main Forecasting Pipeline

The proposed pipeline is:

```text
Historical Sales Dataset
          |
          v
    Data Validation
          |
          v
   Data Preprocessing
          |
          v
   Feature Engineering
          |
          v
   Chronological Split
          |
          v
    Model Training
          |
          v
    Model Evaluation
          |
          v
   Model Selection
          |
          v
   Save Model Artifact
          |
          v
     Load Model
          |
          v
   Generate Forecasts
```

Training and prediction are separate workflows.

## 7. Training Workflow

The training workflow should:

1. Load the historical dataset.
    
2. Validate its structure.
    
3. Clean and prepare the data.
    
4. Generate forecasting features.
    
5. Split observations chronologically.
    
6. Train candidate models.
    
7. Evaluate model performance.
    
8. Compare models against baselines.
    
9. Select a suitable model.
    
10. Save the selected model and metadata.
    

The training workflow should be reproducible.

Training should not run every time the user opens a Streamlit page.

## 8. Prediction Workflow

The prediction workflow should:

1. Load the selected trained model.
    
2. Retrieve the required historical observations.
    
3. Prepare the latest available features.
    
4. Generate future predictions.
    
5. Validate prediction outputs.
    
6. Return structured forecasting results.
    

Prediction must use information available at the time the forecast is generated.

The prediction component must not directly modify inventory records.

## 9. Forecasting Granularity

The proposed forecasting granularity is daily demand per product.

The system should produce demand estimates for future dates.

The exact forecasting horizon is still open.

Possible horizons include:

- 7 days.
    
- 14 days.
    
- 30 days.
    

The selected horizon should match the inventory planning requirements and the reliability of available historical data.

## 10. Model Evaluation

Models should be evaluated using suitable regression metrics.

Primary metrics:

- Mean Absolute Error (MAE).
    
- Root Mean Squared Error (RMSE).
    

Evaluation must use chronological validation.

Random train/test splitting must not be used as the primary evaluation strategy.

The system should compare candidate models against baseline forecasts.

## 11. Model Artifacts

The selected model may be saved using Joblib.

Model artifacts should be stored separately from source code.

The system should preserve enough metadata to identify:

- Model type.
    
- Training date.
    
- Training dataset.
    
- Feature configuration.
    
- Evaluation metrics.
    
- Model version.
    

Only trusted model artifacts should be loaded.

## 12. Integration with Inventory Management

Machine Learning predicts future demand.

Inventory business logic uses the forecast to support restocking decisions.

The responsibilities are separate:

|Component|Responsibility|
|---|---|
|Forecasting|Predict future demand|
|Inventory Logic|Calculate inventory position|
|Recommendation Logic|Determine suggested restocking quantity|
|Streamlit UI|Display results|

The forecasting model must not decide when to purchase products.

That decision belongs to the business logic layer.

## 13. Limitations

Forecast quality depends on the quality and relevance of historical data.

Potential limitations include:

- Sudden changes in demand.
    
- Missing historical observations.
    
- Promotions and seasonal events not represented in the data.
    
- Limited product attributes.
    
- Differences between historical and operational datasets.
    
- Unexpected stockouts that hide actual demand.
    

Predictions should be presented as estimates rather than guaranteed future sales.

## 14. Success Criteria

The ML component should:

- Successfully load and validate historical data.
    
- Generate forecasting features without data leakage.
    
- Train candidate regression models.
    
- Evaluate models using chronological validation.
    
- Compare models against a baseline.
    
- Save and load the selected model.
    
- Generate valid future predictions.
    
- Integrate with restocking recommendations.
    

Actual performance must be reported using measured evaluation results.

No accuracy level should be claimed before evaluation.

## 15. Open Decisions

- Final forecasting model.
    
- Final feature set.
    
- Forecasting horizon.
    
- Model granularity.
    
- Training and validation date ranges.
    
- Model retraining strategy.
    
- Forecast persistence strategy.
    
- Handling products with insufficient history.
    

## 16. Related Documentation

- [Forecasting Strategy](https://forecasting-strategy.md?utm_source=chatgpt.com)
    
- [Feature Engineering](https://feature-engineering.md?utm_source=chatgpt.com)
    
- [Model Training](https://model-training.md?utm_source=chatgpt.com)
    
- [Model Evaluation](https://model-evaluation.md?utm_source=chatgpt.com)
    
- [Prediction Logic](https://prediction-logic.md?utm_source=chatgpt.com)
    
- Data Preprocessing