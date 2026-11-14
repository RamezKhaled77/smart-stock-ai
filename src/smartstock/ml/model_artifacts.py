"""Model artifact persistence (TASK-032).

Implements model-training §11/§14 for the selected forecasting model
(DEC-057, Random Forest):

- ``save_model_artifact`` writes the model (joblib) and its metadata
  (JSON) **atomically**: both payloads are written to temporary files,
  the model is re-loaded and verified, and only then are the final
  files replaced — a failed run can never replace a previously valid
  artifact with an incomplete or corrupted one.
- ``load_model_artifact`` reads both and validates the metadata
  against the required fields; inference consumers rely on the
  metadata's ``feature_names`` matching the training feature order
  (:data:`smartstock.ml.features.FEATURE_COLUMNS`).

Artifact layout (default):

```
models/artifacts/
├── demand_model.joblib
└── model_metadata.json
```

Artifact files are git-ignored runtime data; they are regenerated
locally with ``scripts/train_model.py``.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from smartstock.i18n import t
from smartstock.ml.features import FEATURE_COLUMNS

DEFAULT_ARTIFACTS_DIR = Path("models") / "artifacts"
MODEL_FILE = "demand_model.joblib"
METADATA_FILE = "model_metadata.json"

# model-training §11 metadata contract.
REQUIRED_METADATA_FIELDS = [
    "model_name",
    "model_version",
    "training_timestamp_utc",
    "dataset_reference",
    "feature_names",
    "training_configuration",
    "evaluation_metrics",
    "forecasting_granularity",
]


class ArtifactError(Exception):
    """Raised when an artifact cannot be saved or safely loaded."""


def build_metadata(
    model_name: str,
    model_parameters: dict,
    dataset_reference: str,
    training_row_count: int,
    evaluation_metrics: dict,
    model_version: str = "1.0.0",
) -> dict:
    """Assemble the §11 metadata record for one training run.

    ``training_row_count`` is the number of complete feature rows the
    artifact actually fitted on; metrics come from the DEC-027
    evaluation runs (validation 2016 / test 2017), not from this fit.
    """
    return {
        "model_name": model_name,
        "model_version": model_version,
        "training_timestamp_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "dataset_reference": dataset_reference,
        "feature_names": list(FEATURE_COLUMNS),
        "training_configuration": {
            "model_parameters": model_parameters,
            "training_row_count": training_row_count,
            "training_window": "full observed history (DEC-057 artifact)",
        },
        "evaluation_metrics": evaluation_metrics,
        "forecasting_granularity": {
            "unit": "product (store 1), daily quantity",
            "horizons_supported": [7, 14, 30],
            "default_horizon_days": 7,
            "recursive_forecasting": True,
        },
    }


def save_model_artifact(
    model,
    metadata: dict,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> tuple[Path, Path]:
    """Persist the fitted model and metadata atomically (§11, §14).

    Steps: validate metadata → write joblib + JSON to temporary files
    → reload the model from disk and verify it predicts on a sample
    feature row shape → replace the final paths. On any error the
    temporary files are removed and the previous artifact (if any)
    stays untouched.
    """
    _validate_metadata(metadata)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / MODEL_FILE
    metadata_path = artifacts_dir / METADATA_FILE

    fd_model, temp_model = tempfile.mkstemp(
        dir=artifacts_dir, suffix=".tmp"
    )
    fd_meta, temp_metadata = tempfile.mkstemp(
        dir=artifacts_dir, suffix=".tmp"
    )
    os.close(fd_model)
    os.close(fd_meta)
    try:
        joblib.dump(model, temp_model)
        with open(temp_metadata, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, sort_keys=True)
            handle.write("\n")

        # §14: verify the payload really is a loadable, usable model.
        reloaded = joblib.load(temp_model)
        if not hasattr(reloaded, "predict"):
            raise ArtifactError(
                "Reloaded artifact has no ``predict`` method."
            )
        # Column names are irrelevant to sklearn predict; the width
        # follows the model's recorded expectation when available.
        width = getattr(reloaded, "n_features_in_", None) or len(
            metadata["feature_names"]
        )
        sample = pd.DataFrame([[0] * width])
        reloaded.predict(sample)

        os.replace(temp_model, model_path)
        os.replace(temp_metadata, metadata_path)
    except Exception:
        for temp in (temp_model, temp_metadata):
            try:
                os.unlink(temp)
            except OSError:
                pass
        raise
    return model_path, metadata_path


def load_model_metadata(
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> dict:
    """Load and validate only the model metadata (no model file).

    The evaluation display (TASK-042) reads the stored training-time
    metrics from metadata alone — loading the full model would be
    wasted work for a read-only summary.

    Raises:
        ArtifactError: If the metadata file is missing, unreadable,
            or fails the contract validation.
    """
    artifacts_dir = Path(artifacts_dir)
    metadata_path = artifacts_dir / METADATA_FILE
    if not metadata_path.is_file():
        raise ArtifactError(t("svc.forecast.metadata_missing"))
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactError(
            f"Metadata file {metadata_path} is unreadable: {error}"
        ) from error
    _validate_metadata(metadata)
    return metadata


def load_model_artifact(
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> tuple[object, dict]:
    """Load the model and metadata, validating the metadata contract.

    Raises:
        ArtifactError: If files are missing, JSON is unreadable, or the
            metadata misses required fields.
    """
    artifacts_dir = Path(artifacts_dir)
    model_path = artifacts_dir / MODEL_FILE
    metadata_path = artifacts_dir / METADATA_FILE
    if not model_path.is_file() or not metadata_path.is_file():
        raise ArtifactError(
            "Model artifact not found. Run "
            "``scripts/train_model.py`` to create one first (the "
            "artifact files are git-ignored runtime data)."
        )
    try:
        model = joblib.load(model_path)
    except Exception as error:
        raise ArtifactError(
            f"Model file {model_path} could not be loaded: {error}"
        ) from error
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactError(
            f"Metadata file {metadata_path} is unreadable: {error}"
        ) from error
    _validate_metadata(metadata)
    if not hasattr(model, "predict"):
        raise ArtifactError("Loaded model has no ``predict`` method.")
    return model, metadata


def _validate_metadata(metadata: dict) -> None:
    if not isinstance(metadata, dict):
        raise ArtifactError("Metadata must be a JSON object.")
    missing = [
        field
        for field in REQUIRED_METADATA_FIELDS
        if field not in metadata
    ]
    if missing:
        raise ArtifactError(
            f"Metadata is missing required fields: {missing}."
        )
    feature_names = metadata["feature_names"]
    if feature_names != list(FEATURE_COLUMNS):
        raise ArtifactError(
            "Metadata feature_names do not match the enforced training "
            f"feature set ({FEATURE_COLUMNS})."
        )
    if not isinstance(metadata["evaluation_metrics"], dict):
        raise ArtifactError(
            "Metadata evaluation_metrics must be a JSON object."
        )
