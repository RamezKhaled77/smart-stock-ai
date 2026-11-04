

# CSV Import Specification

## 1. Purpose

This document defines how CSV files are imported into SmartStock AI.

The import functionality allows users to provide sales data for analysis and forecasting.

The import workflow must validate incoming data before accepting it.

It must also protect operational inventory from unintended changes.

---

## 2. Supported Import Type

The initial application is expected to support sales CSV imports.

Two different use cases must be distinguished:

### Historical Dataset Import

Used for:

- Model training.
- Historical analysis.
- Forecasting preparation.

Historical imports do not automatically create operational sales transactions.

### Operational Sales Import

Used to import sales records that belong to the application's operational sales history.

This may affect inventory depending on the approved sales and inventory rules.

The initial implementation must not treat every uploaded CSV as an operational stock-changing import.

The import type must be clear to the user.

---

## 3. Historical Dataset Format

The proposed Kaggle dataset uses the following columns:

```csv
date,store,item,sales
2013-01-01,1,1,13
2013-01-02,1,1,11
```

The example above illustrates the expected column structure only.

Actual values must come from the downloaded dataset.

### Required Columns

|Column|Description|
|---|---|
|date|Sales observation date|
|store|Source store identifier|
|item|Source product identifier|
|sales|Units sold|

## 4. Operational Sales Format

A separate operational CSV format may be defined.

Proposed columns:

```
sale_date,sku,quantity
2026-01-01,PROD-001,5
2026-01-02,PROD-002,3
```

This format is a proposal.

The final operational import format must be approved before implementation.

### Required Fields

|Field|Description|
|---|---|
|sale_date|Date of the sale|
|sku|Existing product identifier|
|quantity|Quantity sold|

An operational import must not create products implicitly unless that behavior is explicitly approved.

## 5. Import Workflow

The proposed workflow:

1. User opens the CSV import page.
    
2. User selects the import type.
    
3. User uploads a CSV file.
    
4. The system checks the file format.
    
5. The system validates required columns.
    
6. The system validates data types.
    
7. The system checks missing and invalid values.
    
8. The system checks duplicate records.
    
9. The system displays an import preview.
    
10. The user reviews the validation summary.
    
11. The system imports accepted records according to the selected import type.
    
12. The system displays the final import result.
    

No data should be committed before validation and confirmation.

## 6. File Validation

The application should validate:

- File extension.
    
- File readability.
    
- Required columns.
    
- File encoding where possible.
    
- Empty files.
    
- Unexpected data formats.
    

The application should not trust a file merely because its extension is `.csv`.

Invalid files should be rejected with a clear explanation.

## 7. Data Validation

Validation should include:

### Dates

- Must be valid dates.
    
- Must follow the accepted date policy.
    
- Must not contain invalid values.
    

### Identifiers

- Required identifiers must not be missing.
    
- Operational product identifiers must match existing products.
    

### Quantities

- Must be numeric.
    
- Must follow the approved quantity policy.
    
- Negative quantities must be rejected unless a separately approved return workflow supports them.
    

### Duplicate Records

Duplicate handling must be defined according to the import type.

The system must not silently import duplicate records.

## 8. Import Preview

Before confirmation, display:

- Uploaded file name.
    
- Total number of rows.
    
- Valid row count.
    
- Invalid row count.
    
- Duplicate row count.
    
- Missing value summary.
    
- Date range when available.
    
- Sample records.
    
- Validation errors.
    

The user should be able to understand what will happen before confirming the import.

## 9. Historical Import Rules

Historical imports are intended for analysis and forecasting.

Important rules:

- They must not automatically reduce current inventory.
    
- They must not silently create operational sales transactions.
    
- They must preserve the source dataset's meaning.
    
- They must follow the approved preprocessing workflow.
    
- Their source and import metadata should be identifiable.
    

An explicit stock reconciliation operation, if introduced later, must be separate from historical data import.

## 10. Operational Import Rules

Operational sales imports may create sales records.

Before implementation, the project must define:

- Whether sales imports reduce current stock.
    
- Whether insufficient stock blocks the import.
    
- How duplicate imports are detected.
    
- Whether imports can be rolled back.
    
- How partially invalid files are handled.
    
- Whether imported records need source identifiers.
    

Until these decisions are approved, operational import behavior must not be assumed.

## 11. Import Atomicity

The preferred approach is to validate the complete file before writing records.

For database-backed imports, use a transaction when multiple related records must be saved together.

If the import fails during the database operation, the application should avoid leaving partially imported data unless partial imports are explicitly supported.

## 12. Duplicate Import Prevention

The system should consider repeated uploads of the same file.

Potential approaches:

- Store import metadata.
    
- Generate a file fingerprint.
    
- Use source record identifiers.
    
- Apply business-level duplicate checks.
    

The final approach depends on the selected import model.

A simple filename comparison is not sufficient to guarantee that a file is unique.

## 13. Error Handling

The import workflow should distinguish between:

- File-level errors.
    
- Column-level errors.
    
- Row-level validation errors.
    
- Database errors.
    
- Duplicate records.
    

Error messages should explain the issue without exposing unnecessary technical details.

For large files, the application should avoid displaying every invalid row at once.

A summarized report with a limited number of examples may be more practical.

## 14. Import Result

After a successful import, display:

- Total rows processed.
    
- Accepted records.
    
- Rejected records.
    
- Duplicate records.
    
- Import timestamp.
    
- Import type.
    
- Final status.
    

The application must report actual results.

It must not claim that records were imported if the database transaction failed.

## 15. Security Considerations

CSV uploads should be treated as untrusted input.

The application should:

- Validate uploaded content.
    
- Avoid unsafe file path handling.
    
- Avoid executing uploaded content.
    
- Avoid trusting user-provided filenames.
    
- Handle unexpected file sizes appropriately.
    
- Prevent uploaded values from being interpreted as executable code.
    

If data is later exported to CSV, consider spreadsheet formula injection risks.

## 16. Open Decisions

|Decision|Status|
|---|---|
|Historical import format|Proposed|
|Operational import format|Proposed|
|Duplicate detection strategy|Open|
|Partial import support|Open|
|Import rollback behavior|Open|
|Insufficient stock policy|Open|
|Import history storage|Open|
|Stock reconciliation workflow|Open|

## 17. Related Documentation

- [Dataset Overview](https://dataset-overview.md?utm_source=chatgpt.com)
    
- [Data Dictionary](https://data-dictionary.md?utm_source=chatgpt.com)
    
- [Data Preprocessing](https://data-preprocessing.md?utm_source=chatgpt.com)
    
- Business Rules
    
- Database Schema
    
- User Flows