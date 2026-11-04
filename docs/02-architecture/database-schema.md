
## 4. `docs/02-architecture/database-schema.md`


# Database Schema

## 1. Overview

SmartStock AI uses SQLite as its proposed operational database.

The database stores information required to operate the inventory management application.

The historical dataset used for machine learning is treated separately from operational database records.

This document defines a proposed logical data model.

It does not represent a fully approved final SQL schema.

Some details depend on unresolved business rules and must be confirmed before implementation.

---

## 2. Design Principles

The database should:

- Store operational records consistently.
- Maintain clear relationships between products and sales.
- Support inventory management.
- Avoid unnecessary duplication.
- Preserve historical sales information.
- Support future analytical queries.
- Use appropriate primary and foreign keys.

The initial application is designed around a single store.

Multi-branch support is not included unless explicitly approved later.

---

## 3. Proposed Entities

The initial logical model may contain:

1. Products
2. Sales
3. Inventory Movements
4. Forecast Results (Optional)

The exact structure and required fields are subject to validation.

---

## 4. Products

Represents products managed by the application.

### Proposed Fields

| Field | Suggested Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| name | TEXT | Product name |
| sku | TEXT | Unique product identifier |
| category | TEXT | Product category |
| current_stock | INTEGER | Current available stock |
| lead_time_days | INTEGER | Expected replenishment time |
| safety_stock | INTEGER | Additional stock buffer |
| created_at | TEXT | Creation timestamp |
| updated_at | TEXT | Last update timestamp |

### Notes

- `id` is the internal product identifier.
- `sku` is proposed as a unique business identifier.
- `current_stock` must follow the approved inventory policy.
- Lead time and safety stock may be optional depending on the final business rules.
- `current_stock` may be maintained directly or derived from inventory movements. This is an open design decision.

---

## 5. Sales

Represents operational sales records.

### Proposed Fields

| Field | Suggested Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| product_id | INTEGER | Related product |
| quantity | INTEGER | Units sold |
| sale_date | TEXT | Date of sale |
| created_at | TEXT | Record creation timestamp |

### Relationships

- Each sales record belongs to one product.
- A product may have multiple sales records.

### Notes

- `product_id` references `products.id`.
- Quantity must be validated.
- Historical imported records must be distinguished from manually entered sales if required.
- The effect of returns and cancelled sales is still an open decision.

---

## 6. Inventory Movements

**Status: Proposed / Requires Approval**

An inventory movement records a change in stock.

Potential movement types:

- Initial Stock.
- Manual Stock Adjustment.
- Sale.
- Return.
- Restock.

### Proposed Fields

| Field | Suggested Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| product_id | INTEGER | Related product |
| movement_type | TEXT | Type of stock movement |
| quantity | INTEGER | Movement quantity |
| movement_date | TEXT | Date of movement |
| notes | TEXT | Optional explanation |
| created_at | TEXT | Record creation timestamp |

### Important Design Question

There are two possible inventory models.

**Option A: Store current stock directly**

The products table stores the current stock quantity.

Advantages:
- Simple implementation.
- Easy to query.
- Suitable for a small initial application.

Disadvantages:
- Limited stock history.
- Harder to audit stock changes.

**Option B: Use inventory movements**

Every stock change is recorded as a movement.

Current stock can be calculated from the movement history or maintained as a cached value.

Advantages:
- Better traceability.
- Easier auditing.
- Clear history of stock changes.

Disadvantages:
- More implementation complexity.
- Requires careful handling of movement consistency.

**Decision Status:** Open.

The final choice must follow the approved inventory requirements.

---

## 7. Forecast Results

**Status: Decided — not built in version 1 (DEC-028)**

Forecast persistence was evaluated and rejected for the initial application: forecasts are generated on demand and are not stored.

Consequences:

- The database schema in version 1 contains Products, Sales, and (pending approval) Inventory Movements only.
- Forecast-versus-actual visualization is computed by comparing a generated forecast against actual recorded sales history, not from stored forecast rows.
- If forecast history, tracking, or reporting over time becomes an approved requirement later, a new decision must supersede DEC-028 and this entity may then be introduced.

For reference, the potential fields if the entity is ever approved would be: id (INTEGER PK), product_id (INTEGER FK), forecast_date (TEXT), predicted_demand (REAL), model_version (TEXT), created_at (TEXT).

---

## 8. Relationships

The proposed relationships are:

```shell
Products
   |
   | 1
   |
   |------< Sales
   |
   |------< Inventory Movements
   |
   |------< Forecast Results (Optional)

```

A product can have multiple sales records and multiple inventory movements.

Forecast results are optional and depend on the approved implementation scope.

## 9. Historical Dataset Mapping

The proposed Kaggle Store Item Demand Forecasting dataset contains:

- date
    
- store
    
- item
    
- sales
    

These fields do not directly match the operational database schema.

A mapping process is required.

### Proposed Mapping

|Dataset Field|Application Concept|
|---|---|
|date|sale_date|
|item|Product mapping key|
|sales|quantity|
|store|Store identifier in source data|

The dataset contains multiple stores and items.

The initial application is not assumed to support multiple branches.

Therefore, the project must define how historical records are mapped to the initial product catalog.

A possible approach is to create a stable mapping between source item identifiers and application product identifiers.

The source `store` value may be used during training and analysis without introducing multi-branch operational support.

This mapping must be documented before combining historical data with operational records.

## 10. Data Integrity

The database implementation should consider:

- Primary key constraints.
    
- Foreign key constraints.
    
- Unique product identifiers.
    
- Appropriate NOT NULL constraints.
    
- Valid quantity ranges.
    
- Consistent date formats.
    
- Parameterized SQL queries.
    

SQLite foreign key enforcement should be enabled for database connections.

Transactions should be used when multiple related database changes must succeed or fail together.

## 11. Deletion and Historical Records

Deletion behavior is not fully approved.

Potential policies:

- Hard deletion.
    
- Soft deletion.
    
- Prevent deletion when historical records exist.
    

Historical sales and inventory records should not become inconsistent when a product is deleted.

The final policy must be defined before implementing deletion operations.

## 12. CSV Import Considerations

Historical CSV imports must not automatically modify current inventory.

The import process should distinguish between:

- Historical sales data used for forecasting.
    
- Operational sales entered into the application.
    
- Explicit stock reconciliation operations.
    

Duplicate detection and import rollback behavior are still open decisions.

The import process must validate records before saving them.

## 13. Database Initialization

The database initialization process should:

1. Check whether the database exists.
    
2. Create the database when needed.
    
3. Create required tables.
    
4. Apply approved schema definitions.
    
5. Enable foreign key enforcement.
    

Schema changes should be handled carefully.

Avoid deleting or recreating an existing database simply to apply a schema change.

## 14. Open Decisions

|Decision|Status|
|---|---|
|Store current stock directly or derive it from movements|Open|
|Inventory movement history|Open|
|Forecast result persistence|**Closed (DEC-028)** — generated on demand; Forecast Results entity not built in v1|
|Soft deletion policy|Open|
|Returns representation|Open|
|Duplicate CSV import handling|Open|
|Historical dataset mapping|**Closed (DEC-015)** — one selected store; each `item` maps to one product|
|Exact column constraints|Open|

## 15. Related Documentation

- Business Rules
    
- Requirements
    
- CSV Import Specification
    
- [System Architecture](https://system-architecture.md?utm_source=chatgpt.com)