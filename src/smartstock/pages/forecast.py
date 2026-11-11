"""Forecast page (Forecast-page task, DEC-060).

Selects an operational product, links it to its dataset item's
imported history, and shows the demand forecast for a chosen horizon
(7/14/30 days, DEC-026). Predictions come from the inference module
through the forecast service — this page is purely rendering and input
collection, read-only like every other page (prediction-logic §12).
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.ml import model_artifacts
from smartstock.ml.inference import DEFAULT_HORIZON_DAYS, SUPPORTED_HORIZONS
from smartstock.pages.ui import show_flash
from smartstock.services import (
    evaluation_service,
    forecast_service,
    product_service,
)

HORIZON_LABELS = {
    7: "Next 7 days",
    14: "Next 14 days",
    30: "Next 30 days",
}

MODEL_LABELS = {
    "random_forest": "Random Forest model (needs ≥ 31 days of history)",
    "moving_average_7": (
        "Trailing 7-day average fallback (history under 31 days, "
        "DEC-058)"
    ),
}


def render() -> None:
    """Render the Forecast page."""
    st.title("🔮 Demand Forecast")
    st.caption(
        "Advisory demand estimates per product, based on the linked "
        "dataset item's imported sales history. Forecasts are "
        "estimates — not guaranteed outcomes."
    )

    show_flash()

    products = product_service.list_products()  # active only
    if not products:
        st.info(
            "No active products yet. Add products on the Products & "
            "Inventory page first."
        )
        _render_evaluation()
        return

    options = {
        f"{product['name']} ({product['sku']})": product
        for product in products
    }
    selection = st.selectbox(
        "Product", list(options), key="forecast_product"
    )
    horizon = st.radio(
        "Forecast horizon",
        list(SUPPORTED_HORIZONS),
        format_func=HORIZON_LABELS.__getitem__,
        index=SUPPORTED_HORIZONS.index(DEFAULT_HORIZON_DAYS),
        horizontal=True,
        key="forecast_horizon",
    )

    product = options[selection]
    _render_link_status(product)

    if st.button("Generate forecast", key="forecast_generate"):
        _render_forecast(product["id"], horizon)

    _render_evaluation()


def _render_evaluation() -> None:
    """TASK-042: stored, training-time evaluation metrics.

    Per the recorded decision, this displays the already-computed
    window metrics only — no new predictions, keeping the DEC-056
    one-touch test-window discipline intact. The numbers are the
    measured values from model selection, never illustrative ones.
    """
    st.subheader("📐 How accurate is the model?")
    try:
        summary = evaluation_service.get_evaluation_summary()
    except model_artifacts.ArtifactError as error:
        st.info(
            "Evaluation metrics become available after the model is "
            "trained — run ``scripts/train_model.py`` first."
        )
        st.caption(str(error))
        return

    st.caption(
        "Measured during model selection on held-out evaluation data "
        "(MAE/RMSE in units per product-day — lower is better). No "
        "predictions are generated here, so the one-time 2017 test "
        "window stays untouched (DEC-056)."
    )
    windows = summary["windows"]
    if windows:
        columns = st.columns(len(windows))
        for index, window in enumerate(windows):
            columns[index].metric(
                window["label"],
                f"MAE {window['mae']}",
                help=(
                    f"RMSE {window['rmse']} over "
                    f"{window['predictions']:,} product-days."
                ),
            )
    if summary["baselines"]:
        st.caption(
            "Context — simple baselines on the same validation data: "
            + "; ".join(
                f"{row['label']} {row['mae']}"
                for row in summary["baselines"]
            )
            + ". The model must beat these to be selected (DEC-027) — "
            "and it did."
        )
    st.caption(
        f"Model: {summary['model_name']} v{summary['model_version']}, "
        f"trained {summary['trained_at']}. Forecasts are estimates — "
        "actual demand can differ (prediction-logic §11)."
    )


def _render_link_status(product: dict) -> None:
    """Show whether the selected product can be forecast at all."""
    linked = product.get("dataset_item_id")
    if linked is None:
        st.info(
            f"'{product['name']}' has no dataset item linked yet. Set "
            "'Linked dataset item' in the product's edit form "
            "(Replenishing → Edit product) to enable forecasting "
            "(DEC-060)."
        )
    else:
        st.caption(f"Linked dataset item: {linked}")


def _render_forecast(product_id: int, horizon: int) -> None:
    """Generate and display the forecast (service handles all errors)."""
    try:
        result = forecast_service.get_forecast(product_id, horizon)
    except forecast_service.ProductNotLinkError as error:
        st.info(str(error))
        return
    except model_artifacts.ArtifactError as error:
        st.warning(
            "The forecasting model artifact is not available — run "
            "``scripts/train_model.py`` first."
        )
        st.caption(str(error))
        return
    except forecast_service.ForecastError as error:
        # e.g. the DEC-058 "No suitable history exists" state or an
        # unsupported horizon: understandable conditions, not crashes.
        st.info(f"Forecast not available: {error}")
        return
    except (DatabaseError, ValueError) as error:
        st.error(f"Could not generate the forecast: {error}")
        return

    st.subheader(
        f"Forecast for {result['product']['name']} "
        f"({result['product']['sku']})"
    )
    st.caption(f"Method: {MODEL_LABELS.get(result['model_used'], result['model_used'])}")

    rows = result["rows"]
    total = sum(row["predicted_demand"] for row in rows)
    columns = st.columns(3)
    columns[0].metric(
        f"Total demand ({result['horizon_days']} days)",
        f"{total:.1f}",
    )
    columns[1].metric(
        "Average per day",
        f"{total / len(rows):.1f}",
    )
    columns[2].metric("Dataset item", result["dataset_item_id"])

    import pandas as pd

    table = pd.DataFrame(
        [
            {
                "Date": row["forecast_date"],
                "Predicted demand": row["predicted_demand"],
            }
            for row in rows
        ]
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Predicted demand": st.column_config.NumberColumn(
                "Predicted demand", format="%.1f",
            ),
        },
    )
    st.caption(
        "Raw predictions are rounded for display only; restocking "
        "formulas use their own approved demand rule (DEC-059)."
    )
