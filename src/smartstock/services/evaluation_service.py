"""Application service for the model evaluation display (TASK-042).

The user-facing decision (recorded in the task record): show the
already-computed training-time evaluation metrics only. Generating new
per-day predictions for a chart would either reuse the DEC-056 test
window a second time (forbidden — one-touch discipline) or run the
model on non-era data. The stored window-level metrics are the
evidence-backed truth, so this service formats them for display.

Read-only; loads model metadata only (no model file needed).
"""

from pathlib import Path

import config
from smartstock.ml import model_artifacts

ARTIFACTS_DIR = Path(config.MODELS_DIR) / "artifacts"

WINDOW_LABELS = {
    "validation_window": "Validation window (2016)",
    "test_window": "Test window (2017, evaluated once — DEC-056)",
}

BASELINE_LABELS = {
    "naive_validation": "Naive (last value) — validation MAE",
    "moving_average_7_validation": "Moving average (7-day) — validation MAE",
}


def get_evaluation_summary(
    artifacts_dir: Path | None = None,
) -> dict:
    """Stored evaluation metrics for display.

    Args:
        artifacts_dir: Artifact directory; defaults to this module's
            ``ARTIFACTS_DIR`` (patchable in tests).

    Returns:
        Dictionary with ``model_name``, ``model_version``,
        ``trained_at``, ``windows`` (list of ``{"label", "mae", "rmse",
        "predictions"}``, validation first), ``baselines`` (list of
        ``{"label", "mae"}``), and ``dataset_reference``.

    Raises:
        ArtifactError: If the metadata is missing or unreadable.
    """
    if artifacts_dir is None:
        artifacts_dir = ARTIFACTS_DIR
    metadata = model_artifacts.load_model_metadata(artifacts_dir)
    evaluation = metadata["evaluation_metrics"]

    windows = []
    for key in ("validation_window", "test_window"):
        window = evaluation.get(key)
        if not window:
            continue
        windows.append(
            {
                "label": WINDOW_LABELS.get(key, key),
                "mae": window.get("mae"),
                "rmse": window.get("rmse"),
                "predictions": window.get("predictions"),
            }
        )

    baselines = []
    reference = evaluation.get("baselines_for_reference", {})
    for key, label in BASELINE_LABELS.items():
        if key in reference:
            baselines.append({"label": label, "mae": reference[key]})

    return {
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "trained_at": metadata["training_timestamp_utc"],
        "windows": windows,
        "baselines": baselines,
        "dataset_reference": metadata["dataset_reference"],
    }
