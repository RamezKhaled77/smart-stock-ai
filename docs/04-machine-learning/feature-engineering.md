
# Feature Engineering

## 1. Purpose

This document defines the proposed features used by the demand forecasting models.

Feature engineering transforms historical sales records into structured numerical inputs that machine learning models can use.

All generated features must respect the forecasting timeline.

Future information must never be used to generate features for past predictions.

---

## 2. Input Data

The feature engineering pipeline expects cleaned historical sales data.

Expected columns:

- date
- store
- item
- sales

The data should already have passed the preprocessing validation process.

Each observation represents daily sales for a specific store-item combination.

---

## 3. Feature Categories

The proposed feature categories are:

1. Date-based features.
2. Lag features.
3. Rolling statistical features.
4. Product or store identifiers when appropriate.

The final feature set must be selected through evaluation.

---

## 4. Date-Based Features

Date-based features describe calendar information.

### 4.1 day_of_week

Represents the day of the week.

Possible values:

- 0: Monday
- 1: Tuesday
- 2: Wednesday
- 3: Thursday
- 4: Friday
- 5: Saturday
- 6: Sunday

Generated from the observation date.

### 4.2 month

Represents the month number.

Possible values:

- 1 through 12.

### 4.3 day_of_month

Represents the day within the month.

Possible values:

- 1 through 31.

These features may help the model identify calendar-related demand patterns.

---

## 5. Lag Features

Lag features represent historical sales observations.

### 5.1 lag_1

Sales from the previous day.

```python
lag_1 = sales.shift(1)
```

### 5.2 lag_7

Sales from seven days earlier.

```
lag_7 = sales.shift(7)
```

Lag calculations must be performed separately for each forecasting series.

For the proposed dataset, the series is identified by:

- store
    
- item
    

Records must be sorted chronologically before generating lag features.

## 6. Rolling Statistical Features

Rolling features summarize historical observations over a selected window.

### 6.1 rolling_mean_7

Average sales over the previous seven observations.

### 6.2 rolling_mean_30

Average sales over the previous thirty observations.

Important:

Rolling features must exclude the current target observation.

A safe conceptual approach is:

1. Shift the sales series by one observation.
    
2. Calculate the rolling average on the shifted series.
    

Example:

```
previous_sales = sales.shift(1)rolling_mean_7 = previous_sales.rolling(7).mean()rolling_mean_30 = previous_sales.rolling(30).mean()
```

This ensures that the current target value is not included in its own features.

## 7. Feature Generation Example

Example implementation:

```
import pandas as pddef create_sales_features(    data: pd.DataFrame,) -> pd.DataFrame:    required_columns = [        "date",        "store",        "item",        "sales",    ]    missing_columns = [        column        for column in required_columns        if column not in data.columns    ]    if missing_columns:        raise ValueError(            f"Missing required columns: {missing_columns}"        )    result = data.copy()    result["date"] = pd.to_datetime(result["date"])    result = result.sort_values(        ["store", "item", "date"]    ).copy()    grouped = result.groupby(        ["store", "item"],        sort=False,    )["sales"]
```

This is an illustrative implementation.

It must be tested against small datasets before being used in the complete training pipeline.

## 8. Handling Initial Missing Features

Lag and rolling features require historical observations.

As a result, the first observations in each series may contain missing feature values.

Possible strategies:

- Remove rows without sufficient history from model training.
    
- Use a simpler forecasting approach for products with limited history.
    
- Define an explicit fallback strategy.
    

Missing values must not be filled arbitrarily.

The selected approach should be consistent between training and prediction.

## 9. Feature and Target Separation

The target variable is:

`sales`

Candidate model features:

```
FEATURE_COLUMNS = [    "day_of_week",    "month",    "day_of_month",    "lag_1",    "lag_7",    "rolling_mean_7",    "rolling_mean_30",]
```

The target must not be included in the feature matrix.

Identifiers such as `store` and `item` may be considered as model inputs, depending on the selected modeling approach.

They should not automatically be treated as continuous numerical measurements.

## 10. Preventing Data Leakage

Data leakage occurs when information unavailable at prediction time enters the model inputs.

Examples:

- Using current-day sales to predict current-day sales.
    
- Using future observations in rolling averages.
    
- Randomly splitting chronological observations.
    
- Calculating features across different product series.
    
- Using validation or test information during training-time transformations.
    

The feature engineering pipeline must ensure that every feature is generated using information available before the target date.

## 11. Multi-Step Forecasting

For recursive forecasting, future feature values must be updated after each prediction.

Example:

1. Generate the prediction for day 1.
    
2. Append the predicted value to the historical series.
    
3. Recalculate lag and rolling features.
    
4. Predict day 2.
    
5. Repeat for the remaining horizon.
    

Actual future sales must not be used during a real future forecasting workflow.

## 12. Feature Selection

The initial feature set is a starting point.

Features may be removed or added based on:

- Validation performance.
    
- Data availability.
    
- Computational cost.
    
- Model complexity.
    
- Risk of leakage.
    

Every important feature change should be recorded.

## 13. Testing Requirements

Feature engineering tests should verify:

- Correct chronological sorting.
    
- Correct grouping by store and item.
    
- Correct lag calculations.
    
- Correct rolling calculations.
    
- No use of the current target in rolling features.
    
- Correct date-based values.
    
- Expected handling of missing initial values.
    
- Consistent feature column order.
    

Tests should use small datasets with manually verifiable expected values.

## 14. Open Decisions

- Whether store and item identifiers should be model features.
    
- Whether additional calendar features are useful.
    
- Whether lag_14 or lag_30 should be evaluated.
    
- Whether rolling median or standard deviation is useful.
    
- Minimum history required for each feature set.
    
- Final feature selection.
    

## 15. Related Documentation

- [Forecasting Strategy](https://forecasting-strategy.md?utm_source=chatgpt.com)
    
- Data Preprocessing
    
- [Model Training](https://model-training.md?utm_source=chatgpt.com)
    
- [Model Evaluation](https://model-evaluation.md?utm_source=chatgpt.com)