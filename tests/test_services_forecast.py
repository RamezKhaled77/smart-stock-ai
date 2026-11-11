"""Tests for the forecast service (DEC-060 mapping + inference path).

The real ``data/smartstock.db`` is never touched; a stub model replaces
the joblib artifact for the model path, and a skip-guarded test pins
the real artifact against the real imported store-1 data.
"""

from pathlib import Path

import numpy as np
import pytest

from smartstock.database.connection import session
from smartstock.database.initialization import initialize_database
from smartstock.ml import model_artifacts
from smartstock.ml.inference import ForecastError
from smartstock.repositories import historical_repository
from smartstock.services import forecast_service, product_service


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_smartstock.db"
    initialize_database(path)
    return path


def import_item_history(path: Path, item: int, day_totals: dict) -> None:
    """Store one imported batch for ``item`` (rows: date → quantity)."""
    rows = [(item, date, quantity) for date, quantity in day_totals.items()]
    meta = {
        "source_filename": "test.csv",
        "file_sha256": f"sha256-test-{item}-" + str(sorted(day_totals)),
        "store": 1,
        "total_rows": len(rows),
        "out_of_store_rows": 0,
        "rejected_rows": 0,
        "duplicate_rows": 0,
        "first_date": min(day_totals) if day_totals else None,
        "last_date": max(day_totals) if day_totals else None,
    }
    with session(path) as connection:
        historical_repository.create_import_batch(connection, meta, rows)


class StubModel:
    """Predicts a constant, echoing feature row count."""

    def predict(self, features):
        return [7.0] * len(features)


def stub_metadata() -> dict:
    return model_artifacts.build_metadata(
        model_name="stub",
        model_parameters={},
        dataset_reference="test",
        training_row_count=1,
        evaluation_metrics={},
    )


def make_stub_forecast(path: Path) -> dict:
    """Linked product + 40-day item history + stub model path."""
    import datetime as dt

    product = product_service.create_product(
        name="Linked", sku="SKU-LK", db_path=path,
        dataset_item_id=1,
    )
    totals = {
        (
            dt.date(2024, 1, 1) + dt.timedelta(offset)
        ).isoformat(): 2
        for offset in range(40)
    }
    import_item_history(path, 1, totals)
    return forecast_service.get_forecast(
        product["id"],
        7,
        db_path=path,
        model=StubModel(),
        metadata=stub_metadata(),
    )


class TestDec060LinkGate:
    """Unlinked/no-history products are refused with clear messages."""

    def test_unlinked_product_refused(self, db_path: Path) -> None:
        product = product_service.create_product(
            name="Unlinked", sku="SKU-UL", db_path=db_path
        )
        with pytest.raises(
            forecast_service.ProductNotLinkError, match="no dataset item"
        ):
            forecast_service.get_forecast(
                product["id"], 7, db_path=db_path
            )

    def test_linked_item_without_imported_rows_refused(
        self, db_path: Path
    ) -> None:
        product = product_service.create_product(
            name="Empty", sku="SKU-EMP", db_path=db_path,
            dataset_item_id=5,
        )
        with pytest.raises(ForecastError, match="No suitable history"):
            forecast_service.get_forecast(
                product["id"], 7, db_path=db_path
            )

    def test_missing_product_rejected(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            forecast_service.get_forecast(999, 7, db_path=db_path)

    def test_inactive_product_rejected(self, db_path: Path) -> None:
        product = product_service.create_product(
            name="Inactive", sku="SKU-IA", db_path=db_path
        )
        product_service.set_product_active(
            product["id"], False, db_path=db_path
        )
        with pytest.raises(ValueError, match="inactive"):
            forecast_service.get_forecast(
                product["id"], 7, db_path=db_path
            )


class TestZeroFillAndPaths:
    def test_gap_inside_span_is_zero_filled(
        self, db_path: Path
    ) -> None:
        product = product_service.create_product(
            name="Gapped", sku="SKU-GAP", db_path=db_path,
            dataset_item_id=3,
        )
        import_item_history(
            db_path, 3, {"2024-01-01": 2, "2024-01-03": 2}
        )
        # Span 3 days, the missing day zero-filled → series [2, 0, 2].
        # 3 days < 31 → MA-7 fallback path (each prediction joins the
        # trailing window, exactly as in tests/test_ml_inference.py).
        result = forecast_service.get_forecast(
            product["id"], 7, db_path=db_path
        )
        assert result["model_used"] == "moving_average_7"
        working = [2.0, 0.0, 2.0]
        for index, row in enumerate(result["rows"]):
            assert row["predicted_demand"] == pytest.approx(
                round(float(np.mean(working[-7:])), 3)
            )
            working.append(float(np.mean(working[-7:])))
        assert result["rows"][0]["forecast_date"] == "2024-01-04"

    def test_model_path_used_for_full_history(self, db_path) -> None:
        result = make_stub_forecast(db_path)
        assert result["model_used"] == "random_forest"
        # Stub prediction 7.0, clipped/rounded for display.
        assert all(
            row["predicted_demand"] == pytest.approx(7.0)
            for row in result["rows"]
        )

    def test_dates_continue_after_history_end(self, db_path) -> None:
        result = make_stub_forecast(db_path)
        assert result["rows"][0]["forecast_date"] == "2024-02-10"
        assert result["rows"][-1]["forecast_date"] == "2024-02-16"


@pytest.fixture(scope="module")
def real_setup(tmp_path_factory):
    """Linked product + real item-1 import + real artifact."""
    import datetime as dt

    from smartstock.ml import preprocessing

    artifacts_dir = Path("models") / "artifacts"
    if not (artifacts_dir / "demand_model.joblib").is_file():
        pytest.skip("Model artifact not generated in this checkout")
    csv_path = Path("data/raw/train.csv")
    if not csv_path.is_file():
        pytest.skip("Historical dataset not present")

    path = tmp_path_factory.mktemp("forecast_real") / "db.sqlite"
    initialize_database(path)
    frame, _ = preprocessing.preprocess_dataset(csv_path, store_id=1)
    item1 = frame[frame["item"] == 1]
    day_totals = dict(zip(item1["date"].dt.strftime("%Y-%m-%d"), item1["sales"].astype(int)))
    import_item_history(path, 1, day_totals)
    product = product_service.create_product(
        name="Real Item", sku="SKU-REAL", db_path=path,
        dataset_item_id=1,
    )
    return path, product, len(day_totals)


class TestArtifactAndRealData:
    def test_missing_artifact_raises_clear_error(
        self, db_path: Path, monkeypatch, tmp_path: Path
    ) -> None:
        product = product_service.create_product(
            name="Linked", sku="SKU-ART", db_path=db_path,
            dataset_item_id=1,
        )
        import_item_history(
            db_path, 1, {f"2024-01-{day:02d}": 2 for day in range(1, 11)}
        )
        monkeypatch.setattr(
            forecast_service, "ARTIFACTS_DIR", tmp_path / "none"
        )
        with pytest.raises(
            model_artifacts.ArtifactError, match="train_model"
        ):
            forecast_service.get_forecast(
                product["id"], 7, db_path=db_path
            )

    def test_real_artifact_forecasts_real_import(
        self, real_setup
    ) -> None:
        path, product, observed_days = real_setup
        result = forecast_service.get_forecast(
            product["id"], 7, db_path=path
        )
        assert result["model_used"] == "random_forest"
        assert len(result["rows"]) == 7
        # Continues after 2017-12-31 (the dataset's last day).
        assert result["rows"][0]["forecast_date"] == "2018-01-01"
        assert observed_days == 1826  # 5 years, pin per dataset docs
