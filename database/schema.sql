-- SmartStock AI operational database schema (SQLite).
--
-- Implements docs/02-architecture/database-schema.md with the decisions:
--   DEC-047: current_stock stored directly; no Inventory Movements entity in v1.
--   DEC-048: soft delete via the is_active flag; rows are never deleted.
--   DEC-049: no returns in v1; recorded sales rows are immutable.
-- All timestamps and dates are stored as ISO 8601 TEXT (UTC timestamps,
-- plain YYYY-MM-DD dates).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    sku            TEXT    NOT NULL UNIQUE,
    category       TEXT    NOT NULL DEFAULT '',
    current_stock  INTEGER NOT NULL DEFAULT 0 CHECK (current_stock >= 0),
    lead_time_days INTEGER NOT NULL DEFAULT 3 CHECK (lead_time_days >= 0),
    safety_stock   INTEGER NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
    is_active      INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at     TEXT    NOT NULL,
    updated_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    sale_date  TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sales_product_date
    ON sales (product_id, sale_date);
