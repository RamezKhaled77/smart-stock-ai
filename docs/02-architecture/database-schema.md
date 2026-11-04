
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
| is_active | INTEGER | Soft-delete flag (1 = active, 0 = deactivated) |
| created_at | TEXT | Creation timestamp |
| updated_at | TEXT | Last update timestamp |

### Decisions Applied (2026-11-04)

- `current_stock` is maintained **directly** on the products table (DEC-047). Sales and approved manual adjustments update the column in a transaction; no movement entity exists in v1.
- `lead_time_days` is a manual per-product field defaulting to `3` when omitted (DEC-037).
- `safety_stock` is a manual per-product field defaulting to `0` when omitted (DEC-036).
- `is_active` implements the soft-delete policy (DEC-048). Removal deactivates; rows are never deleted. Counts and listings exclude inactive products (BR-026).
- Negative stock is forbidden (DEC-034): the column carries a `CHECK (current_stock >= 0)`.
- Stock status derives from `current_stock` against the reorder point (BR-008).

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
- Quantity must be validated (positive integer, and checked against available stock at recording time per DEC-035).
- **Returns and cancelled sales are not supported in v1 (DEC-049).** Recorded sales rows are immutable; corrections happen through explicitly recorded manual stock adjustments only.
- Historical imported records are distinguished from manually entered sales via the separate historical dataset files; the operational `sales` table receives only application-recorded sales in v1.

---

## 6. Inventory Movements

**Status: Decided — not built in version 1 (DEC-047)**

Stock storage was evaluated against two models:

- **Option A: Store current stock directly** — a maintained `current_stock` column on the products table. Simple to implement and query; suitable for the small single-store v1 application.
- **Option B: Inventory movements** — every stock change recorded as a movement row, current stock derived or cached. Better traceability, but more implementation complexity and sync handling.

**Decision: Option A (DEC-047).** Version 1 stores current stock directly on the products table, and the Inventory Movements entity is not created. Consequences:

- Sales (validated against stock per DEC-035) and manual stock adjustments update `current_stock` directly in a transaction.
- No stock-change history or audit trail exists in v1. If movement tracking is approved later, it requires a new entity, backfill logic, and a superseding decision.
- Manual corrections to wrong data are explicit user operations on the stock value; the previous value may be overwritten and is not recoverable from the database (consistent with DEC-049's immutable-sales stance and DEC-046's approval requirement for destructive operations).

For reference, the potential movement fields if the entity is ever approved: id (INTEGER PK), product_id (INTEGER FK), movement_type (TEXT), quantity (INTEGER), movement_date (TEXT), notes (TEXT), created_at (TEXT).

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

```

A product can have multiple sales records. The Inventory Movements entity is not built in v1 (DEC-047), and Forecast Results are excluded per DEC-028.

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

**Decided policy (DEC-048): soft delete.** Products carry an `is_active` flag (default 1). The removal action sets `is_active = 0`; database rows are never deleted, so sales and other related records can never become inconsistent. Listings, counts, and recommendations exclude inactive products unless explicitly requested (BR-026). Reactivation is possible.

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
|Store current stock directly or derive it from movements|**Closed (DEC-047)** — direct `current_stock` column; movements entity not built in v1|
|Inventory movement history|**Closed (DEC-047)** — no movement history in v1; may be approved later with a superseding decision|
|Forecast result persistence|**Closed (DEC-028)** — generated on demand; Forecast Results entity not built in v1|
|Soft deletion policy|**Closed (DEC-048)** — soft delete via `is_active` flag|
|Returns representation|**Closed (DEC-049)** — no returns support in v1; recorded sales immutable|
|Duplicate CSV import handling|Open — to be resolved during CSV import implementation|
|Historical dataset mapping|**Closed (DEC-015)** — one selected store; each `item` maps to one product|
|Exact column constraints|**Closed (2026-11-04, TASK-009)** — defined in the approved SQL schema (`database/sql/schema.sql`): PKs, FKs with enforcement, unique `sku`, NOT NULL where applicable, `CHECK` constraints on stock and quantities, ISO date TEXT format|

## 15. Related Documentation

- Business Rules
    
- Requirements
    
- CSV Import Specification
    
- [System Architecture](https://system-architecture.md?utm_source=chatgpt.com)