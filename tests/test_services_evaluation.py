"""Tests for the evaluation service (TASK-042).

The display policy (recorded decision): show stored training-time
metrics only — no new predictions, keeping the DEC-056 one-touch test
window intact. Tests verify the stored numbers are surfaced faithfully
and that missing/unreadable artifacts raise ``ArtifactError``.
"""

import json
from pathlib import Path

import pytest

from smartstock.ml import model_artifacts
from smartstock.services import evaluation_service

pytestmark = pytest.mark.filterwarnings(
    "ignore:The inplace keyword:Warning"
)


def _write_artifacts(directory: Path, metadata: dict) -> Path:
    """Minimal artifact dir: metadata only (no model file needed)."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / model_artifacts.METADATA_FILE).write_text(
        json.dumps(metadata)
    )
    return directory


def full_metadata() -> dict:
    """Realistic metadata matching the documented evaluation shape."""
    return {
        "model_name": "random_forest",
        "model_version": "1.0.0",
        "training_timestamp_utc": "2026-11-09T06:03:38Z",
        "dataset_reference": "test dataset",
        "feature_names": list(model_artifacts.FEATURE_COLUMNS),
        "training_configuration": {"model_parameters": {}},
        "evaluation_metrics": {
            "validation_window": {
                "start": "2016-01-01",
                "end": "2016-12-31",
                "mae": 6.033,
                "rmse": 7.785,
                "predictions": 18300,
            },
            "test_window": {
                "start": "2017-01-01",
                "end": "2017-12-31",
                "mae": 6.088,
                "rmse": 7.91,
                "predictions": 18250,
            },
            "baselines_for_reference": {
                "naive_validation": 10.27,
                "moving_average_7_validation": 8.077,
            },
        },
        "forecasting_granularity": {
            "unit": "product (store 1), daily quantity",
            "horizons_supported": [7, 14, 30],
            "default_horizon_days": 7,
            "recursive_forecasting": True,
        },
    }


class TestStoredMetrics:
    def test_windows_and_baselines_surfaced_faithfully(
        self, tmp_path: Path
    ) -> None:
        directory = _write_artifacts(tmp_path / "a", full_metadata())
        summary = evaluation_service.get_evaluation_summary(
            artifacts_dir=directory
        )
        assert summary["model_name"] == "random_forest"
        assert summary["trained_at"] == "2026-11-09T06:03:38Z"
        # Validation first, then the labeled one-touch test window.
        assert [w["mae"] for w in summary["windows"]] == [6.033, 6.088]
        assert summary["windows"][1]["label"].startswith("Test window")
        assert summary["windows"][1]["label"].endswith("DEC-056)")
        assert summary["windows"][0]["predictions"] == 18300
        assert [b["mae"] for b in summary["baselines"]] == [
            10.27, 8.077,
        ]

    def test_missing_optional_sections_omitted(
        self, tmp_path: Path
    ) -> None:
        metadata = full_metadata()
        metadata["evaluation_metrics"] = {"validation_window": {
            "mae": 6.033, "rmse": 7.785, "predictions": 18300,
        }}
        directory = _write_artifacts(tmp_path / "a", metadata)
        summary = evaluation_service.get_evaluation_summary(
            artifacts_dir=directory
        )
        assert len(summary["windows"]) == 1
        assert summary["baselines"] == []


class TestArtifactStates:
    def test_missing_metadata_raises(self, tmp_path: Path) -> None:
        directory = tmp_path / "empty"
        directory.mkdir()
        with pytest.raises(model_artifacts.ArtifactError, match="train_model"):
            evaluation_service.get_evaluation_summary(
                artifacts_dir=directory
            )

    def test_unreadable_metadata_raises(self, tmp_path: Path) -> None:
        directory = tmp_path / "bad"
        directory.mkdir()
        (directory / model_artifacts.METADATA_FILE).write_text("{nope")
        with pytest.raises(model_artifacts.ArtifactError, match="unreadable"):
            evaluation_service.get_evaluation_summary(
                artifacts_dir=directory
            )

    def test_invalid_contract_raises(self, tmp_path: Path) -> None:
        metadata = full_metadata()
        metadata["evaluation_metrics"] = "not a dict"
        directory = _write_artifacts(tmp_path / "contract", metadata)
        with pytest.raises(model_artifacts.ArtifactError):
            evaluation_service.get_evaluation_summary(
                artifacts_dir=directory
            )


@pytest.mark.skipif(
    not (Path("models") / "artifacts" / "model_metadata.json").is_file(),
    reason="real artifact not trained in this checkout",
)
class TestRealArtifact:
    """Pins the display against the real trained model's metadata."""

    def test_real_metrics_are_the_task031_numbers(self) -> None:
        summary = evaluation_service.get_evaluation_summary()
        assert summary["model_name"] == "random_forest"
        validation, test = summary["windows"]
        assert validation["mae"] == 6.033
        assert test["mae"] == 6.088
        assert test["label"].endswith("DEC-056)")
        # The model beats both baselines (DEC-027 selection rule).
        baseline_maes = [row["mae"] for row in summary["baselines"]]
        assert validation["mae"] < min(baseline_maes)
