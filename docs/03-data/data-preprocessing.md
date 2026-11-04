# Data Preprocessing

## 1. Purpose

This document defines the proposed workflow for preparing historical sales data before analysis and machine learning.

The preprocessing pipeline must produce reliable, consistent data while preserving the original source dataset.

Preprocessing decisions must be documented and reproducible.

---

## 2. Input Data

The primary proposed input is:

`data/raw/train.csv`

Expected columns:

- date
- store
- item
- sales

The preprocessing process must validate the input structure before continuing.

---

## 3. Preprocessing Pipeline

The proposed workflow is:

```text
Raw CSV
   |
   v
Load Dataset
   |
   v
Validate Columns
   |
   v
Validate Data Types
   |
   v
Parse Dates
   |
   v
Check Missing Values
   |
   v
Check Duplicate Records
   |
   v
Validate Sales Values
   |
   v
Sort Historical Records
   |
   v
Prepare Processed Dataset
   |
   v
Feature Engineering
```

Each stage should have a clear responsibility.

## 4. Loading Data

Use Pandas to load CSV files.

The loading process should:

- Check whether the file exists.
    
- Read the file safely.
    
- Validate the expected columns.
    
- Report loading errors clearly.
    

The original file must not be modified.

## 5. Column Validation

The preprocessing pipeline must verify that all required columns exist.

Required columns:
```shell
REQUIRED_COLUMNS = [
    "date",
    "store",
    "item",
    "sales",
]
```

If a required column is missing, preprocessing must stop with a clear error.

Unexpected additional columns may be ignored or retained depending on their usefulness, but this behavior must be consistent.

## 6. Data Type Validation

Expected transformations:

- `date`: Convert to a datetime representation.
    
- `store`: Validate as a store identifier.
    
- `item`: Validate as a product identifier.
    
- `sales`: Convert to a numeric representation.
    

Invalid values must be identified before they are removed or transformed.

Do not silently convert invalid values into valid-looking records.

## 7. Date Handling

Dates must be parsed into a consistent datetime format.

The pipeline should:

- Identify invalid dates.
    
- Check the date range.
    
- Sort records chronologically.
    
- Use a consistent timezone policy.
    

The proposed dataset contains daily observations, so the pipeline should verify whether dates follow the expected daily structure for each store-item combination.

## 8. Missing Value Handling

Missing values should be inspected by column.

Potential policies:

|Field|Proposed Handling|
|---|---|
|date|Reject invalid or missing values|
|store|Reject missing identifiers|
|item|Reject missing identifiers|
|sales|Investigate and apply an explicit policy|

Missing sales values must not automatically become zero.

A missing record does not necessarily mean that no sales occurred.

## 9. Duplicate Handling

The expected logical record identity is:

`date + store + item`

The preprocessing pipeline should detect duplicate combinations.

Possible policies:

- Reject duplicates.
    
- Aggregate duplicate sales records when aggregation is justified.
    
- Investigate the source before selecting a handling strategy.
    

The system must not silently drop duplicates.

The selected policy should be recorded in the preprocessing implementation and documentation.

## 10. Sales Validation

Sales values must be checked for:

- Missing values.
    
- Non-numeric values.
    
- Negative values.
    
- Unexpected fractional values.
    
- Unusually large values.
    

Negative sales values should be investigated.

They may represent invalid data or another business concept, such as returns, but the proposed historical dataset is expected to represent units sold.

Do not modify suspicious values without documenting the reason.

## 11. Chronological Sorting

After validation, records should be sorted by:

1. store
    
2. item
    
3. date
    

Chronological sorting is important for:

- Lag features.
    
- Rolling averages.
    
- Time-based train/test splitting.
    
- Forecasting workflows.
    

## 12. Missing Dates and Zero Sales

A missing date and a date with zero sales are not necessarily equivalent.

Before filling missing dates, determine whether the source dataset is expected to contain a complete daily sequence for every store-item combination.

If the dataset is complete, a missing date may indicate a data quality issue.

If the dataset is incomplete, the project must define whether a missing date means:

- No recorded observation.
    
- No sales.
    
- Data collection failure.
    

Zero sales should only be assigned when the interpretation is justified.

## 13. Feature Engineering Preparation

The cleaned dataset should be prepared for feature engineering.

Potential derived features:

- Day of week.
    
- Month.
    
- Day of month.
    
- Lag features.
    
- Rolling averages.
    

Important constraints:

- Features must use only information available at prediction time.
    
- Rolling calculations must not include future observations.
    
- Data must remain chronologically ordered.
    
- Initial rows without enough historical observations must be handled explicitly.
    

The detailed feature generation process belongs in the machine learning documentation.

## 14. Data Splitting

Forecasting evaluation must use chronological splitting.

Random train/test splitting is not appropriate for the primary time-series evaluation workflow because it can expose future information during training.

A possible approach:

- Earlier observations: Training set.
    
- Later observations: Validation set.
    
- Most recent observations: Test set.
    

The exact date ranges and split ratios must be selected after inspecting the dataset.

## 15. Data Leakage Prevention

The preprocessing pipeline must prevent information from the future from entering model inputs.

Examples of potential leakage:

- Calculating rolling means using future observations.
    
- Using actual future sales to generate lag features for a prediction.
    
- Applying transformations using information from the test period when they should be fitted on training data only.
    
- Randomly mixing future and past observations during evaluation.
    

All feature calculations must respect the prediction timeline.

## 16. Processed Data Output

Processed datasets may be saved under:

`data/processed/`

Possible output files:

- `cleaned_sales.csv`
    
- `training_features.csv`
    
- `validation_features.csv`
    
- `test_features.csv`
    

These filenames are proposed and may change.

Generated data should be reproducible from the original source and documented preprocessing steps.

## 17. Logging and Reporting

The preprocessing workflow should report:

- Input file name.
    
- Number of input records.
    
- Number of valid records.
    
- Missing value counts.
    
- Duplicate record counts.
    
- Invalid record counts.
    
- Date range.
    
- Number of stores.
    
- Number of items.
    
- Output file location.
    

If records are removed or transformed, the reason and count should be reported.

## 18. Testing Requirements

Preprocessing tests should cover:

- Missing required columns.
    
- Invalid date values.
    
- Invalid numeric values.
    
- Missing identifiers.
    
- Duplicate records.
    
- Negative sales.
    
- Empty datasets.
    
- Chronological sorting.
    
- Missing dates.
    
- Output consistency.
    

Tests should use small controlled datasets rather than depending on the complete Kaggle dataset.

## 19. Open Decisions

Resolved by implementation based on TASK-005 inspection evidence (2026-11-04). The source dataset contains zero missing values, zero duplicate keys, zero negative or fractional sales, and a complete daily sequence for every store-item combination, so strict rejection policies can be applied without any effect on the actual data:

| Question | Resolved Policy | Rationale |
|---|---|---|
| Invalid-record policy | Reject with a clear `DatasetError` naming the column and count; never silently convert or drop. | No conversions needed for the source data; loud failure protects future imported data. |
| Duplicate aggregation policy | Reject duplicate (date, store, item) keys; no silent dropping. | Source contains none. If a future import introduces duplicates, aggregation requires investigation and would change data; that must be explicit, not automatic. |
| Missing-date interpretation | Reported via `detect_date_gaps`; dates are read as observed, zeros are not fabricated. | Source is complete, so any gap is unexpected; inserting synthetic zeros would invent demand evidence. Implemented in `detect_date_gaps`. |
| Negative sales handling | Reject. | Dataset is expected to represent units sold; the source has none. Negative values must be investigated before use, never auto-corrected. |
| Processed dataset formats | `data/processed/store_1_cleaned_sales.csv` produced by `scripts/prepare_dataset.py` (sideline: cannot be regenerated without `data/raw/train.csv`). | Reproducible single store-cleaned output (DEC-015); git-ignored per the data directory rules. |
| Preserve additional columns | Only the four required columns are kept. | Per DEC-015 the `store` column is filtered away at preprocessing; surviving frame preserves `date, item, sales` plus store for join/verification. |

Still open (to be resolved in the ML phases):

- Final train/validation/test date ranges (selected after the chronological-split design in the model evaluation phase).
    

## 20. Related Documentation

- [Dataset Overview](https://dataset-overview.md?utm_source=chatgpt.com)
    
- [Data Dictionary](https://data-dictionary.md?utm_source=chatgpt.com)
    
- [CSV Import Specification](https://csv-import-specification.md?utm_source=chatgpt.com)
    
- Feature Engineering
    
- Model Evaluation