"""Schema assets for the operational SQLite database.

Points to the single approved SQL schema file and records the table
structure that the initialization must produce, so verification has one
authoritative source.
"""

from pathlib import Path

# database/schema.sql at the repository root.
# src/smartstock/database/schema.py -> parents[3] is the repo root.
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "database" / "schema.sql"

# Tables the application requires (v1: no movements, no forecast
# results; historical import tables arrive with DEC-052).
REQUIRED_TABLES = (
    "products",
    "sales",
    "import_batches",
    "historical_sales",
)

# Expected columns per approved schema, used by initialization checks.
# Column order does not matter; only presence.
EXPECTED_COLUMNS = {
    "products": [
        "id",
        "name",
        "sku",
        "category",
        "current_stock",
        "lead_time_days",
        "safety_stock",
        "is_active",
        "created_at",
        "updated_at",
    ],
    "sales": [
        "id",
        "product_id",
        "quantity",
        "sale_date",
        "created_at",
    ],
    "import_batches": [
        "id",
        "source_filename",
        "file_sha256",
        "store",
        "total_rows",
        "out_of_store_rows",
        "rejected_rows",
        "duplicate_rows",
        "imported_rows",
        "first_date",
        "last_date",
        "created_at",
    ],
    "historical_sales": [
        "id",
        "item",
        "sale_date",
        "quantity",
        "import_batch_id",
    ],
}
