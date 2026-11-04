
# Model Training

## 1. Purpose

This document defines the model training workflow for SmartStock AI.

The training process prepares historical sales data, trains candidate forecasting models, evaluates them, and saves the selected model for future predictions.

Training must be reproducible and separated from the normal application prediction workflow.

---

## 2. Training Objectives

The training process should:

- Load validated historical sales data.
- Generate forecasting features.
- Prepare chronological training and validation datasets.
- Train candidate models.
- Compare their performance against baselines.
- Select a suitable model.
- Save the trained model and metadata.

---

## 3. Candidate Models

The following approaches may be evaluated.

### 3.1 Naive Forecast

A simple baseline based on the latest available observation.

### 3.2 Historical Average

A baseline using an average of previous observations.

### 3.3 Linear Regression

A simple regression model.

Potential advantages:

- Easy to understand.
- Fast to train.
- Useful as a reference model.

### 3.4 Random Forest Regressor

An ensemble regression model.

Potential advantages:

- Can capture nonlinear relationships.
- Works with numerical features.
- Does not require feature scaling in the same way as many distance-based models.

Its suitability must be demonstrated through validation.

---

## 4. Training Data Preparation

The training pipeline should:

1. Load the raw dataset.
2. Validate required columns.
3. Run preprocessing.
4. Generate forecasting features.
5. Separate features from the target.
6. Remove or handle rows with insufficient history.
7. Split data chronologically.

The training process must use the approved preprocessing and feature engineering functions.

Avoid implementing separate, inconsistent preprocessing logic inside training scripts.

---

## 5. Feature Matrix and Target

The target variable is:

`sales`

Candidate feature columns:

- day_of_week
- month
- day_of_month
- lag_1
- lag_7
- rolling_mean_7
- rolling_mean_30

The exact feature list must remain consistent between training and prediction.

If model-specific preprocessing is needed, it should be included in the saved model pipeline where practical.

---

## 6. Chronological Splitting

Training data must precede validation data.

Conceptual example:

```text
|---------------- Training ----------------|--- Validation ---|
```

A separate later test period should be preserved for final evaluation.

The actual split dates must be selected after inspecting the dataset.

Random splitting must not be used as the main evaluation approach.

## 7. Training Process

The training process should:

1. Prepare the training features.
    
2. Prepare the target values.
    
3. Initialize a candidate model.
    
4. Fit the model using training data.
    
5. Generate validation predictions.
    
6. Calculate evaluation metrics.
    
7. Record the results.
    
8. Repeat for other candidates.
    
9. Compare candidates against the baselines.
    

The training process should not use the validation target values during model fitting.

## 8. Random Forest Configuration

Random Forest is a candidate model.

Potential parameters include:

|Parameter|Purpose|
|---|---|
|n_estimators|Number of decision trees|
|max_depth|Maximum tree depth|
|min_samples_split|Minimum samples required to split a node|
|min_samples_leaf|Minimum samples required at a leaf|
|random_state|Reproducibility|

Initial values should be selected conservatively.

The project should avoid unnecessary large hyperparameter searches.

Training performance must be practical on a CPU-based environment.

## 9. Reproducibility

The training process should:

- Use fixed random seeds where applicable.
    
- Record model parameters.
    
- Record feature configuration.
    
- Record dataset version or source.
    
- Record training date.
    
- Record evaluation metrics.
    

The same documented configuration should produce reproducible results within reasonable environment limitations.

## 10. Model Selection

The selected model should be based on validation evidence.

Selection should consider:

- MAE.
    
- RMSE.
    
- Baseline comparison.
    
- Computational cost.
    
- Prediction stability.
    
- Suitability for the forecasting horizon.
    

Do not select a model simply because it is more advanced.

A simpler model may be preferable if it performs similarly and is easier to maintain.

## 11. Saving Model Artifacts

Use Joblib to save the selected model.

Proposed artifact structure:

```
models/
└── artifacts/
    ├── demand_model.joblib
    └── model_metadata.json
```

The exact naming convention may change.

Metadata should include:

- Model name.
    
- Model version.
    
- Training timestamp.
    
- Dataset reference.
    
- Feature names.
    
- Training configuration.
    
- Evaluation metrics.
    
- Forecasting granularity.
    

Model files should be loaded only from trusted project artifacts.

## 12. Training Script

A standalone script may be used:

`scripts/train_model.py`

Responsibilities:

- Execute the training workflow.
    
- Report training progress.
    
- Display evaluation metrics.
    
- Save the selected model.
    
- Save relevant metadata.
    
- Report failures clearly.
    

Training should not be embedded directly inside Streamlit page rendering.

## 13. Retraining Strategy

The initial version may use a manually triggered training workflow.

Possible future strategies:

- Retrain when new historical data becomes available.
    
- Retrain on a scheduled interval.
    
- Retrain when evaluation performance degrades.
    

Automatic scheduled retraining is not required for the initial implementation.

The selected retraining policy remains open.

## 14. Training Failure Handling

The training workflow should handle:

- Missing dataset files.
    
- Invalid dataset structure.
    
- Insufficient observations.
    
- Feature generation failures.
    
- Model fitting errors.
    
- Evaluation failures.
    
- Model serialization errors.
    

A failed training process must not replace a previously valid model artifact with an incomplete or corrupted artifact.

## 15. Testing Requirements

Training tests should verify:

- Input validation.
    
- Feature and target separation.
    
- Chronological splitting.
    
- Model fitting.
    
- Metric calculation.
    
- Artifact saving and loading.
    
- Metadata generation.
    
- Failure handling.
    

Use small controlled datasets for automated tests.

Do not require the full Kaggle dataset for every unit test.

## 16. Open Decisions

- Final model selection.
    
- Final model parameters.
    
- Exact training and validation date ranges.
    
- Final feature set.
    
- Model versioning strategy.
    
- Retraining frequency.
    
- Model metadata format.
    
- Whether the final model should be trained per item or across multiple items.
    

## 17. Related Documentation

- [ML Overview](https://ml-overview.md?utm_source=chatgpt.com)
    
- [Forecasting Strategy](https://forecasting-strategy.md?utm_source=chatgpt.com)
    
- [Feature Engineering](https://feature-engineering.md?utm_source=chatgpt.com)
    
- [Model Evaluation](https://model-evaluation.md?utm_source=chatgpt.com)
    
- [Prediction Logic](https://prediction-logic.md?utm_source=chatgpt.com)