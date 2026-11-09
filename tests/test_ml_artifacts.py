"""Tests for model artifact persistence (TASK-032).

Uses tiny fitted models and the repo's tmp paths — never the real
artifact directory.
"""

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from smartstock.ml import model_artifacts as artifacts


class BrokenModel:
    """Picklable object with no ``predict`` method (§14 probe)."""


@pytest.fixture
def fitted_model():
    model = LinearRegression()
    model.fit([[1, 2, 3], [4, 5, 6]], [10, 20])
    return model


@pytest.fixture
def metadata() -> dict:
    return artifacts.build_metadata(
        model_name="linear_regression",
        model_parameters={"fit_intercept": True},
        dataset_reference="synthetic test data",
        training_row_count=2,
        evaluation_metrics={"validation_window": {"mae": 1.5}},
    )


class TestMetadataContract:
    def test_required_fields_present(self, metadata) -> None:
        for field in artifacts.REQUIRED_METADATA_FIELDS:
            assert field in metadata

    def test_feature_names_match_enforced_set(self, metadata) -> None:
        assert metadata["feature_names"] == [
            "day_of_week", "month", "day_of_month", "lag_1", "lag_7",
            "rolling_mean_7", "rolling_mean_30",
        ]

    def test_timestamp_format(self, metadata) -> None:
        # ISO UTC layout from model-training §9.
        assert metadata["training_timestamp_utc"].endswith("Z")
        assert "T" in metadata["training_timestamp_utc"]

    def test_evaluation_and_config_recorded(self, metadata) -> None:
        assert metadata["evaluation_metrics"] == {
            "validation_window": {"mae": 1.5}
        }
        assert metadata["training_configuration"]["training_row_count"] == 2
        assert metadata["dataset_reference"] == "synthetic test data"


class TestSaveAndLoad:
    def test_roundtrip(self, fitted_model, metadata, tmp_path) -> None:
        model_path, metadata_path = artifacts.save_model_artifact(
            fitted_model, metadata, artifacts_dir=tmp_path
        )
        assert model_path.name == "demand_model.joblib"
        assert metadata_path.name == "model_metadata.json"
        loaded_model, loaded_metadata = artifacts.load_model_artifact(
            tmp_path
        )
        assert isinstance(loaded_model, LinearRegression)
        assert loaded_metadata == metadata
        # Metadata is valid, loadable JSON with an indent.
        raw = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        assert raw["model_name"] == "linear_regression"

    def test_saved_model_predicts(self, fitted_model, metadata, tmp_path) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        model, loaded_meta = artifacts.load_model_artifact(tmp_path)
        width = getattr(model, "n_features_in_", len(loaded_meta["feature_names"]))
        frame = pd.DataFrame([[2, 3, 4]][:width])
        assert len(model.predict(frame)) == 1

    def test_partial_state_never_left_behind(
        self, fitted_model, metadata, tmp_path
    ) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        assert not any(
            path.suffix == ".tmp" for path in tmp_path.iterdir()
        )


class TestFailureHandling:
    def test_invalid_model_leaves_previous_artifact_untouched(
        self, fitted_model, metadata, tmp_path
    ) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        previous = (tmp_path / "demand_model.joblib").read_bytes()

        with pytest.raises(artifacts.ArtifactError, match="predict"):
            artifacts.save_model_artifact(
                BrokenModel(), metadata, tmp_path
            )
        # §14: previous valid artifact stays intact, no stray temps.
        assert (tmp_path / "demand_model.joblib").read_bytes() == previous
        assert not any(path.suffix == ".tmp" for path in tmp_path.iterdir())

    def test_bad_metadata_rejected_before_write(
        self, fitted_model, metadata, tmp_path
    ) -> None:
        broken = dict(metadata)
        del broken["model_version"]
        with pytest.raises(
            artifacts.ArtifactError, match="model_version"
        ):
            artifacts.save_model_artifact(
                fitted_model, broken, artifacts_dir=tmp_path
            )
        assert not (tmp_path / "demand_model.joblib").exists()

    def test_feature_name_mismatch_rejected(
        self, fitted_model, metadata, tmp_path
    ) -> None:
        broken = dict(metadata, feature_names=["lag_1", "lag_7"])
        with pytest.raises(artifacts.ArtifactError, match="feature_names"):
            artifacts.save_model_artifact(fitted_model, broken, tmp_path)

    def test_missing_artifact_raises_helpful_error(self, tmp_path) -> None:
        with pytest.raises(artifacts.ArtifactError, match="train_model"):
            artifacts.load_model_artifact(tmp_path)

    def test_corrupt_model_file_raises(self, fitted_model, metadata, tmp_path) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        (tmp_path / "demand_model.joblib").write_bytes(b"corrupted")
        with pytest.raises(artifacts.ArtifactError, match="could not be loaded"):
            artifacts.load_model_artifact(tmp_path)

    def test_corrupt_metadata_raises(self, fitted_model, metadata, tmp_path) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        (tmp_path / "model_metadata.json").write_text("{not json")
        with pytest.raises(artifacts.ArtifactError, match="unreadable"):
            artifacts.load_model_artifact(tmp_path)

    def test_missing_metadata_fields_on_load_rejected(
        self, fitted_model, metadata, tmp_path
    ) -> None:
        artifacts.save_model_artifact(fitted_model, metadata, tmp_path)
        broken = dict(metadata)
        del broken["forecasting_granularity"]
        (tmp_path / "model_metadata.json").write_text(json.dumps(broken))
        with pytest.raises(
            artifacts.ArtifactError, match="forecasting_granularity"
        ):
            artifacts.load_model_artifact(tmp_path)


@pytest.fixture(scope="class")
def real_artifact():
    """The repo artifact (regenerated via scripts/train_model.py)."""
    repo_dir = Path("models") / "artifacts"
    if not (repo_dir / "demand_model.joblib").is_file():
        pytest.skip("Model artifact not generated in this checkout")
    return artifacts.load_model_artifact(repo_dir)


class TestRealArtifact:
    """Pins the repo artifact (regenerated via scripts/train_model.py)."""

    def test_selected_model_and_features(self, real_artifact) -> None:
        model, metadata = real_artifact
        assert metadata["model_name"] == "random_forest"
        assert metadata["feature_names"] == [
            "day_of_week", "month", "day_of_month", "lag_1", "lag_7",
            "rolling_mean_7", "rolling_mean_30",
        ]
        assert metadata["training_configuration"][
            "training_row_count"
        ] == 89_800

    def test_pinned_metrics(self, real_artifact) -> None:
        _, metadata = real_artifact
        metrics = metadata["evaluation_metrics"]
        assert metrics["validation_window"]["mae"] == pytest.approx(6.033)
        assert metrics["test_window"]["mae"] == pytest.approx(6.088)
        assert (
            metrics["baselines_for_reference"]["moving_average_7_validation"]
            == pytest.approx(8.077)
        )
