
# Data Dictionary

## 1. Purpose

This document defines the meaning, expected data types, and validation rules for the fields used by SmartStock AI.

It covers the proposed historical dataset and the main operational data concepts.

The exact database fields may change when the database schema is finalized.

---

## 2. Historical Dataset Fields

The proposed Kaggle dataset contains four main columns.

| Column | Expected Type | Description |
|---|---|---|
| date | Date | Date of the sales observation |
| store | Integer | Source store identifier |
| item | Integer | Source product identifier |
| sales | Integer | Number of units sold |

### 2.1 date

**Description:** The date associated with the sales observation.

**Expected Format:** A date string that can be parsed into a valid date.

**Validation:**
- Must contain a valid date.
- Must not be missing.
- Must be converted into a consistent internal date representation.

### 2.2 store

**Description:** Identifies the store associated with the sales record.

**Expected Type:** Integer or a compatible numeric identifier.

**Validation:**
- Must not be missing.
- Must contain a valid identifier.
- Must be handled consistently across the dataset.

### 2.3 item

**Description:** Identifies the product associated with the sales record.

**Expected Type:** Integer or a compatible numeric identifier.

**Validation:**
- Must not be missing.
- Must contain a valid identifier.
- Must be mapped consistently when combined with operational products.

### 2.4 sales

**Description:** Number of units sold for a particular item at a particular store on a particular date.

**Expected Type:** Integer.

**Validation:**
- Must be numeric.
- Must not be missing.
- Negative values must be investigated and handled according to an explicit data policy.
- Fractional quantities must not be silently rounded without justification.

---

## 3. Dataset Record Identity

A historical sales observation is identified by the combination of:

- date
- store
- item

The expected dataset should contain no more than one record for the same combination.

Duplicate combinations must be investigated before training.

If duplicates exist, the preprocessing workflow must define whether they should be aggregated, rejected, or handled through another justified method.

---

## 4. Operational Product Fields

The application may use the following product attributes.

| Field | Suggested Type | Description |
|---|---|---|
| id | Integer | Internal product identifier |
| name | String | Product name |
| sku | String | Unique product code |
| category | String | Product category |
| current_stock | Integer | Current stock quantity |
| lead_time_days | Integer | Expected replenishment time |
| safety_stock | Integer | Additional stock buffer |

These are proposed logical attributes, not a finalized database schema.

### Validation Considerations

- Product names should not be empty.
- SKU should be unique if adopted as the product identifier.
- Stock quantities must follow the approved stock policy.
- Lead time must be valid and nonnegative.
- Safety stock must be valid and nonnegative.

The exact rules depend on the approved business requirements.

---

## 5. Operational Sales Fields

| Field | Suggested Type | Description |
|---|---|---|
| id | Integer | Internal sales record identifier |
| product_id | Integer | Related product |
| quantity | Integer | Quantity sold |
| sale_date | Date | Date of sale |
| created_at | DateTime | Record creation timestamp |

### Validation Considerations

- Product must exist.
- Quantity must follow the approved sales policy.
- Sale date must be valid.
- The system must define how cancelled sales and returns are represented.

---

## 6. Inventory Fields

The inventory model is still under consideration.

Potential attributes include:

| Field | Suggested Type | Description |
|---|---|---|
| product_id | Integer | Related product |
| current_stock | Integer | Current available stock |
| lead_time_days | Integer | Replenishment lead time |
| safety_stock | Integer | Additional stock buffer |
| target_stock | Integer | Desired stock level |

Not all fields must be stored directly.

Some values may be calculated when needed.

The final design must avoid storing the same information in multiple places without a clear reason.

---

## 7. Derived Forecasting Features

The machine learning pipeline may generate additional features from historical sales.

These features are not original dataset columns.

| Feature | Suggested Type | Description |
|---|---|---|
| day_of_week | Integer | Day of the week |
| month | Integer | Month number |
| day_of_month | Integer | Day of the month |
| lag_1 | Numeric | Previous day's sales |
| lag_7 | Numeric | Sales seven days earlier |
| rolling_mean_7 | Numeric | Average sales over the previous seven days |
| rolling_mean_30 | Numeric | Average sales over the previous thirty days |

These are candidate features.

Their final definitions and availability must be documented in the feature engineering specification.

---

## 8. Data Type Rules

General rules:

- Dates should use consistent parsing and representation.
- Identifiers should not be treated as continuous numerical measurements.
- Quantities should use numeric types.
- Inventory counts should follow the approved quantity policy.
- Derived numerical features may use floating-point values.
- Missing values must be handled explicitly.

---

## 9. Missing Values

Missing values must be identified before analysis or model training.

Possible handling strategies:

- Reject invalid records.
- Remove records when justified.
- Apply a documented imputation method.
- Preserve missingness when it has analytical meaning.

The selected strategy depends on the field and its role.

Missing sales values must not automatically be interpreted as zero sales.

A missing observation and an observed zero-sales day represent different situations.

---

## 10. Related Documentation

- [Dataset Overview](dataset-overview.md)
- [Data Preprocessing](data-preprocessing.md)
- [Forecasting Strategy](../04-machine-learning/forecasting-strategy.md)
- [Feature Engineering](../04-machine-learning/feature-engineering.md)
- [Database Schema](../02-architecture/database-schema.md)