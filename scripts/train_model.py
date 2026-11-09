"""Train and persist the selected demand-forecasting model (TASK-032).

Executes the model-training §7 workflow end to end for the DEC-057
selected model (Random Forest):

1. Preprocess the historical dataset (store 1 per DEC-015).
2. Evaluate the candidates on the DEC-056 validation window and record
   the measured metrics (also covers the one-time test confirmation —
   a training/retraining run is a checkpoint, not a tuning loop).
3. Fit the production model on **all complete feature rows of the
   observed history** (2013 → 2017): inference forecasts the future,
   so every observed actual is legitimate training input.
4. Save the artifact atomically (model + metadata, model-training
   §11/§14).

Usage (from the repository root):

    PYTHONPATH=src .venv/bin/python scripts/train_model.py

Requires ``data/raw/train.csv`` (git-ignored).
"""

from pathlib import Path
import sys

from smartstock.ml import model_artifacts as artifacts
from smartstock.ml import preprocessing, training
from smartstock.ml.features import FEATURE_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "train.csv"
ARTIFACTS_DIR = PROJECT_ROOT / "models" / "artifacts"
DATASET_REFERENCE = "data/raw/train.csv (Kaggle store-sales history), store 1, DEC-056 window use"


def main() -> int:
    if not RAW_CSV.is_file():
        print(
            f"ERROR: historical dataset not found at {RAW_CSV}. "
            "The file is git-ignored; place it under data/raw/ first."
        )
        return 1

    print("1/4 Preprocessing historical dataset (store 1)...")
    frame, report = preprocessing.preprocess_dataset(RAW_CSV, store_id=1)
    print(
        f"    {report['prepared_record_count']:,} records, "
        f"{report['product_count']} products"
    )

    print("2/4 Evaluating candidates on the DEC-056 validation window...")
    comparison = training.evaluate_candidates(frame)
    for name, report_ in comparison.candidates.items():
        print(f"    validation {name}: {report_.to_dict()}")
    selected = _selected_candidate()
    selected_report = comparison.candidates[selected.name]

    print("3/4 One-time test-window confirmation (DEC-056)...")
    test_comparison = training.evaluate_on_test(frame, candidates=[selected])
    test_report = test_comparison.candidates[selected.name]
    print(f"    test {selected.name}: {test_report.to_dict()}")

    print("4/4 Fitting the production model on full observed history...")
    from smartstock.ml import features as feature_pipeline

    history_complete = feature_pipeline.drop_rows_without_features(
        feature_pipeline.build_features(frame)
    )
    production = selected.instantiate()
    production.fit(
        history_complete[FEATURE_COLUMNS], history_complete["sales"]
    )

    evaluation_metrics = {
        "selection_rules": "DEC-027",
        "validation_window": {
            "start": "2016-01-01",
            "end": "2016-12-31",
            "mae": round(selected_report.mae, 3),
            "rmse": round(selected_report.rmse, 3),
            "predictions": selected_report.predictions,
        },
        "test_window": {
            "start": "2017-01-01",
            "end": "2017-12-31",
            "mae": round(test_report.mae, 3),
            "rmse": round(test_report.rmse, 3),
            "predictions": test_report.predictions,
        },
        "baselines_for_reference": {
            "moving_average_7_validation": round(
                comparison.baselines["moving_average_7"].mae, 3
            ),
            "naive_validation": round(
                comparison.baselines["naive"].mae, 3
            ),
        },
    }

    metadata = artifacts.build_metadata(
        model_name=selected.name,
        model_parameters=dict(selected.parameters),
        dataset_reference=DATASET_REFERENCE,
        training_row_count=len(history_complete),
        evaluation_metrics=evaluation_metrics,
    )
    model_path, metadata_path = artifacts.save_model_artifact(
        production, metadata, artifacts_dir=ARTIFACTS_DIR
    )

    print("Artifact saved (atomically, verified by reload):")
    print(f"  model    : {model_path}")
    print(f"  metadata : {metadata_path}")
    print(
        f"  fitted on {len(history_complete):,} complete feature rows "
        f"({len(FEATURE_COLUMNS)} features)"
    )
    print(
        "  metrics  : validation MAE "
        f"{evaluation_metrics['validation_window']['mae']}, test MAE "
        f"{evaluation_metrics['test_window']['mae']}"
    )
    return 0


def _selected_candidate():
    """The DEC-057 selected candidate (kept as one source of truth)."""
    for candidate in training.default_candidates():
        if candidate.name == "random_forest":
            return candidate
    raise RuntimeError("Random Forest candidate missing from defaults.")


if __name__ == "__main__":
    raise SystemExit(main())
