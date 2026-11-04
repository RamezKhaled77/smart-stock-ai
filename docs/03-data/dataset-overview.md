# Dataset Overview

## 1. Purpose

This document describes the historical dataset used by SmartStock AI for sales analysis and demand forecasting.

The dataset provides historical daily sales records that can be used to understand demand patterns and train machine learning models.

The dataset is intended for machine learning and analytical purposes. It is not a replacement for the application's operational inventory database.

---

## 2. Proposed Dataset

**Dataset Name:** Store Item Demand Forecasting Competition

**Source:** Kaggle

**URL:** https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data

**Status:** Proposed - Requires Download and Validation

The dataset contains historical daily sales records from multiple stores and products.

### Expected Characteristics

- Approximately 913,000 records.
- 10 stores.
- 50 products.
- Five years of historical sales.
- Daily sales observations.

These characteristics must be verified against the downloaded dataset before implementation.

### Verified Actual Characteristics (TASK-005 inspection, 2026-11-04)

The file `data/raw/train.csv` was inspected programmatically. Verified facts:

| Property | Verified Value |
|---|---|
| Records | 913,000 exactly (10 stores × 50 items × 1,826 days) |
| Columns | `date` (string), `store` (int64), `item` (int64), `sales` (int64) |
| Date range | 2013-01-01 → 2017-12-31 (1,826 days) |
| Stores | Integers 1–10 |
| Items | Integers 1–50, every store has all 50 items |
| Missing values | 0 in all columns |
| Duplicate (date, store, item) keys | 0 |
| Negative sales | 0 |
| Fractional sales | 0 |
| Day gaps within store-item series | 1 day only — the daily sequence is complete for every combination |
| Zero-sales records | 1 (in the entire dataset) |
| Mean sales | 52.25 overall; 47.27 within store 1 |

Conclusions:

- The dataset is complete and internally consistent; no record-level quality issues were found.
- Date completeness means the missing-date handling policy (see `data-preprocessing.md`) has no effect on this dataset, but the pipeline still performs the check and reports gaps.
- Store 1 (per DEC-015) contains 91,300 rows covering all 50 items across the full five-year range — sufficient history for model development and chronological evaluation.

---

## 3. Dataset Files

The competition provides CSV files.

Expected files include:

- `train.csv`
- `test.csv`
- `sample_submission.csv`

### train.csv

Contains historical sales observations.

Expected columns:

- date
- store
- item
- sales

This file is the primary candidate for model development and evaluation.

### test.csv

Contains records for which sales values are not provided.

It may be useful for understanding the competition's original prediction format, but it is not required for the application's forecasting workflow.

### sample_submission.csv

Provides the expected submission format for the original competition.

It is not required for the initial application.

---

## 4. Dataset Usage

The dataset may be used for:

1. Exploring historical sales patterns.
2. Understanding demand behavior.
3. Building preprocessing workflows.
4. Creating forecasting features.
5. Training candidate machine learning models.
6. Evaluating forecasting performance.
7. Demonstrating the forecasting functionality.

The dataset should not automatically be treated as real operational inventory data.

---

## 5. Historical Data vs Operational Data

SmartStock AI distinguishes between two data sources.

### Historical Dataset

Used for:

- Model training.
- Model evaluation.
- Historical sales analysis.
- Demand pattern exploration.

The historical dataset may contain multiple stores and products.

### Operational Data

Used by the application for:

- Product management.
- Current inventory.
- Manually recorded sales.
- Inventory adjustments.
- Restocking recommendations.

Operational data is stored in SQLite.

The two sources must be mapped carefully before combining them.

---

## 6. Dataset Limitations

The proposed dataset does not provide all information required by an inventory management system.

It does not directly include:

- Current stock levels.
- Product purchase prices.
- Product selling prices.
- Supplier information.
- Lead times.
- Safety stock.
- Purchase orders.
- Inventory movements.
- Stockout records.
- Returns.

These values must not be invented or presented as actual dataset information.

If the application needs additional operational attributes, they should be entered or generated through a clearly documented and controlled process.

---

## 7. Store and Item Mapping

The dataset contains two identifiers:

- `store`
- `item`

The initial application is designed around a single-store workflow.

Therefore, the project must define how historical records will be mapped to the operational product catalog.

**Decided approach (DEC-015):** Filter the historical data to exactly one store (store 1 by default) and treat each `item` value as one application product.

- Filtering one store yields approximately 45,600 daily records (1 store × 50 items × 5 years), sufficient for forecasting experiments and CPU-friendly.
- The `item` → product mapping must be documented during data preparation.
- The `store` column is used only to filter during preprocessing; it is not kept as an operational concept, and the application does not support multiple operational branches.

The existence of multiple stores in the dataset does not mean that the application supports multiple operational branches.

---

## 8. Dataset Validation

Before using the dataset, verify:

- All expected columns exist.
- Date values can be parsed.
- Store and item identifiers are valid.
- Sales values have valid numeric types.
- Missing values are identified.
- Duplicate records are checked.
- The expected date range is present.
- Sales quantities are nonnegative or handled according to an explicit policy.

Dataset assumptions must be verified rather than blindly trusted.

---

## 9. Data Storage

Recommended local structure:

```text
data/
├── raw/
│   └── train.csv
├── processed/
└── README.md
```

Rules:

- Keep original source files unchanged.
    
- Store generated datasets in `processed/`.
    
- Do not overwrite raw data during preprocessing.
    
- Avoid committing large datasets to Git unless explicitly required.
    

## 10. Dataset Selection Status

The Kaggle dataset is the current proposed source.

Before final approval, confirm:

- The dataset is accessible.
    
- The downloaded files match the expected structure.
    
- The data quality is acceptable.
    
- The dataset supports the selected forecasting objective.
    
- The dataset license and usage conditions are suitable for the project.
    

If the dataset is unsuitable, another source may be evaluated.

## 11. Related Documentation

- [Data Dictionary](https://data-dictionary.md?utm_source=chatgpt.com)
    
- [Data Preprocessing](https://data-preprocessing.md?utm_source=chatgpt.com)
    
- [CSV Import Specification](https://csv-import-specification.md?utm_source=chatgpt.com)
    
- Forecasting Strategy