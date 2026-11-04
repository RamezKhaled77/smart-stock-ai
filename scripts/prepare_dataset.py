"""Prepare the historical dataset for store 1 (DEC-015).

Runs the preprocessing pipeline on ``data/raw/train.csv`` and writes
the cleaned, chronologically sorted subset to
``data/processed/store_1_cleaned_sales.csv``.

Usage (from the repository root):

    PYTHONPATH=src .venv/bin/python scripts/prepare_dataset.py [store_id]
"""

from pathlib import Path
import sys

from smartstock.ml.preprocessing import preprocess_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "train.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "store_1_cleaned_sales.csv"


def main() -> int:
    store_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # The raw dataset must never be modified; only the processed copy
    # under data/processed/ is written.
    cleaned, report = preprocess_dataset(RAW_CSV, store_id=store_id)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_CSV, index=False)

    date_min, date_max = report["date_range"]
    print("Preprocessing report")
    print(f"  source file       : {report['source_file']}")
    print(f"  source records    : {report['source_record_count']:,}")
    print(f"  selected store    : {report['store_id']}")
    print(f"  prepared records  : {report['prepared_record_count']:,}")
    print(f"  date range        : {date_min.date()} -> {date_max.date()}")
    print(f"  products          : {report['product_count']}")
    print(f"  zero-sales records: {report['zero_sales_record_count']}")
    print(f"  series checked    : {report['combinations_checked']}")
    print(f"  series with gaps  : {report['combinations_with_gaps']}")
    print(f"  missing dates     : {report['total_missing_dates']}")
    print(f"  output written to : {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
