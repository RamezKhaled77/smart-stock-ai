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
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    sku             TEXT    NOT NULL UNIQUE,
    category        TEXT    NOT NULL DEFAULT '',
    current_stock   INTEGER NOT NULL DEFAULT 0 CHECK (current_stock >= 0),
    lead_time_days  INTEGER NOT NULL DEFAULT 3 CHECK (lead_time_days >= 0),
    safety_stock    INTEGER NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
    dataset_item_id INTEGER DEFAULT NULL
        CHECK (dataset_item_id IS NULL OR dataset_item_id > 0),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
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

-- Historical import storage (DEC-052): imported Kaggle-dataset records
-- keyed by the dataset's `item` number, never by product_id and never
-- touching the operational sales table (BR-014, DEC-016). Zero sales
-- are valid observations in this table (unlike `sales`).
CREATE TABLE IF NOT EXISTS import_batches (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source_filename   TEXT    NOT NULL,
    file_sha256       TEXT    NOT NULL UNIQUE,
    store             INTEGER NOT NULL CHECK (store > 0),
    total_rows        INTEGER NOT NULL CHECK (total_rows >= 0),
    out_of_store_rows INTEGER NOT NULL CHECK (out_of_store_rows >= 0),
    rejected_rows     INTEGER NOT NULL CHECK (rejected_rows >= 0),
    duplicate_rows    INTEGER NOT NULL CHECK (duplicate_rows >= 0),
    imported_rows     INTEGER NOT NULL CHECK (imported_rows >= 0),
    first_date        TEXT,
    last_date         TEXT,
    created_at        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item            INTEGER NOT NULL CHECK (item > 0),
    sale_date       TEXT    NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity >= 0),
    import_batch_id INTEGER NOT NULL REFERENCES import_batches(id),
    -- DEC-053 hard guarantee: no overlapping import can store the same
    -- (item, date) observation twice.
    UNIQUE (item, sale_date)
);

CREATE INDEX IF NOT EXISTS idx_historical_batch
    ON historical_sales (import_batch_id);
