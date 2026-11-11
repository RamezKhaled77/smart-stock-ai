"""Application service for product demand forecasts (Forecast page).

Per DEC-060 the user selects an operational **product**; the forecast
consumes the linked dataset item's imported ``historical_sales`` series
(operational sales are not mixed in v1). The prediction itself is the
tested inference module (DEC-025/DEC-026/DEC-057/DEC-058) — this
service only composes retrieval + prediction and never mutates
anything (prediction-logic §12: no inventory/stock/sales changes).
"""

from pathlib import Path

import pandas as pd

import config
from smartstock.database.connection import ConnectionContext, session
from smartstock.ml import model_artifacts
from smartstock.ml.inference import (
    DEFAULT_HORIZON_DAYS,
    ForecastError,
    forecast_product,
)
from smartstock.repositories import (
    historical_repository,
    product_repository,
)

# Directory the saved model artifact lives in (config.MODELS_DIR
# mirrors the training workflow's location).
ARTIFACTS_DIR = Path(config.MODELS_DIR) / "artifacts"


class ProductNotLinkError(ForecastError):
    """The selected product has no dataset item linked (DEC-060)."""


def _run(db_path: Path | None) -> ConnectionContext:
    """Open a session for the configured (or given) database."""
    if db_path is None:
        db_path = config.DATABASE_PATH
    return session(db_path)


def _zero_filled_series(daily_totals: dict[str, int]) -> pd.DataFrame:
    """One-row-per-calendar-day frame between the first and last day.

    The trained model's world is a continuous daily series; the
    dataset's zero-sales days are observations (DEC-060). Gaps inside
    the span are filled with 0 so the inference module sees one
    observation per date, as required.
    """
    dates = sorted(daily_totals)
    first_day = pd.Timestamp(dates[0])
    last_day = pd.Timestamp(dates[-1])
    series = [
        daily_totals.get(day.strftime("%Y-%m-%d"), 0)
        for day in pd.date_range(first_day, last_day, freq="D")
    ]
    return pd.DataFrame(
        {
            "date": [
                day.strftime("%Y-%m-%d")
                for day in pd.date_range(first_day, last_day, freq="D")
            ],
            "sales": series,
        }
    )


def get_forecast(
    product_id: int,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    db_path: Path | None = None,
    model=None,
    metadata: dict | None = None,
) -> dict:
    """Forecast demand for one product over the chosen horizon.

    Args:
        product_id: Operational product that must have a linked
            dataset item (DEC-060).
        horizon_days: One of 7/14/30 (DEC-026).
        db_path: Database to use; defaults to the configured path.
        model, metadata: Optional preloaded artifact (testing hook);
            when omitted the saved artifact is loaded once per call.

    Returns:
        Dictionary with the product, the linked dataset item, the
        inferred path label (``model_used``), and the forecast
        ``rows`` (one per day: forecast_date string and
        predicted_demand rounded for display to 3 decimals — the
        business layer rounds, prediction-logic §11).

    Raises:
        ValueError: If the product does not exist or is inactive.
        ProductNotLinkError: If the product has no dataset item
            linked.
        ForecastError: Unsupported horizon, empty/no-history series
            (DEC-058), or a non-finite model output.
        model_artifacts.ArtifactError: If the artifact files are
            missing or invalid.
        DatabaseError: If reading product or history fails.
    """
    with _run(db_path) as connection:
        product = product_repository.get_product(connection, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} does not exist.")
        if not product["is_active"]:
            raise ValueError("Product is inactive and cannot be forecast.")
        item = product.get("dataset_item_id")
        if item is None:
            raise ProductNotLinkError(
                "'{}' ({}) has no dataset item linked yet. Link one on "
                "the Products & Inventory page to enable forecasts "
                "(DEC-060).".format(product["name"], product["sku"])
            )
        daily_totals = historical_repository.get_daily_sales_for_item(
            connection, item
        )

    if not daily_totals:
        raise ForecastError(
            "No suitable history exists for the linked dataset item "
            f"{item} (prediction-logic §13): importing historical "
            "sales for that item is required before forecasting."
        )

    if model is None or metadata is None:
        loaded_model, loaded_metadata = model_artifacts.load_model_artifact(
            ARTIFACTS_DIR
        )
        model = model if model is not None else loaded_model
        metadata = metadata if metadata is not None else loaded_metadata

    history = _zero_filled_series(daily_totals)
    frame = forecast_product(
        model,
        metadata,
        history,
        horizon_days=horizon_days,
        product_id=product_id,
    )

    rows = [
        {
            "forecast_date": row.forecast_date.strftime("%Y-%m-%d"),
            "predicted_demand": round(float(row.predicted_demand), 3),
        }
        for row in frame.itertuples()
    ]
    return {
        "product": product,
        "dataset_item_id": item,
        "horizon_days": horizon_days,
        "model_used": frame["model_used"].iloc[0],
        "model_version": metadata["model_version"],
        "rows": rows,
    }
