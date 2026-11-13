"""Forecast page (Forecast-page task, DEC-060).

Selects an operational product, links it to its dataset item's
imported history, and shows the demand forecast for a chosen horizon
(7/14/30 days, DEC-026). Predictions come from the inference module
through the forecast service — this page is purely rendering and input
collection, read-only like every other page (prediction-logic §12).

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. Horizon and model names map to string-table keys so
their labels translate; the model codes themselves stay English.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.i18n import t
from smartstock.ml import model_artifacts
from smartstock.ml.inference import DEFAULT_HORIZON_DAYS, SUPPORTED_HORIZONS
from smartstock.pages.ui import (
    empty_state,
    page_header,
    pill,
    section,
    show_flash,
    strong,
)
from smartstock.services import (
    evaluation_service,
    forecast_service,
    product_service,
)

# Display-label keys; the horizon/model codes stay language-independent.
HORIZON_LABELS = {
    7: "forecast.horizon_7",
    14: "forecast.horizon_14",
    30: "forecast.horizon_30",
}

MODEL_LABELS = {
    "random_forest": "forecast.model_rf",
    "moving_average_7": "forecast.model_ma7",
}


def render() -> None:
    """Render the Forecast page."""
    page_header(
        "query_stats",
        t("forecast.title"),
        t("forecast.description"),
    )

    show_flash()

    try:
        products = product_service.list_products()  # active only
    except DatabaseError as error:
        st.error(t("forecast.load_products_error", error=error))
        return
    if not products:
        empty_state(
            t("forecast.empty_title"),
            t("forecast.empty_message"),
            icon="inventory_2",
        )
        _render_evaluation()
        return

    options = {
        f"{product['name']} ({product['sku']})": product
        for product in products
    }
    selection = st.selectbox(
        t("forecast.filter_product"), list(options), key="forecast_product"
    )
    horizon = st.radio(
        t("forecast.horizon_label"),
        list(SUPPORTED_HORIZONS),
        format_func=lambda days: t(HORIZON_LABELS[days]),
        index=SUPPORTED_HORIZONS.index(DEFAULT_HORIZON_DAYS),
        horizontal=True,
        key="forecast_horizon",
    )

    product = options[selection]
    _render_link_status(product)

    if st.button(
        t("forecast.button_generate"),
        key="forecast_generate",
        type="primary",
        icon=":material/rocket_launch:",
    ):
        _render_forecast(product["id"], horizon)

    _render_evaluation()


def _render_evaluation() -> None:
    """TASK-042: stored, training-time evaluation metrics.

    Per the recorded decision, this displays the already-computed
    window metrics only — no new predictions, keeping the DEC-056
    one-touch test-window discipline intact. The numbers are the
    measured values from model selection, never illustrative ones.
    """
    section("monitoring", t("forecast.section_accuracy"))
    try:
        summary = evaluation_service.get_evaluation_summary()
    except model_artifacts.ArtifactError as error:
        st.info(
            t("forecast.eval_not_available"),
            icon=":material/speed:",
        )
        st.caption(str(error))
        return

    st.caption(t("forecast.eval_caption"))
    windows = summary["windows"]
    if windows:
        columns = st.columns(len(windows))
        for index, window in enumerate(windows):
            columns[index].metric(
                window["label"],
                f"MAE {window['mae']}",
                help=t(
                    "forecast.eval_window_help",
                    rmse=window["rmse"],
                    predictions=window["predictions"],
                ),
                icon=":material/monitoring:",
                border=True,
            )
    if summary["baselines"]:
        baselines_text = "; ".join(
            f"{row['label']} {row['mae']}"
            for row in summary["baselines"]
        )
        st.caption(
            t("forecast.eval_baselines", baselines=baselines_text)
        )
    st.caption(
        t(
            "forecast.eval_model_caption",
            name=summary["model_name"],
            version=summary["model_version"],
            trained_at=summary["trained_at"],
        )
    )


def _render_link_status(product: dict) -> None:
    """Show whether the selected product can be forecast at all."""
    linked = product.get("dataset_item_id")
    if linked is None:
        st.info(
            t("forecast.no_link_info", name=product["name"]),
            icon=":material/link_off:",
        )
    else:
        st.markdown(
            f":material/link: {t('forecast.linked_label')}: "
            f"{strong(str(linked))}",
            unsafe_allow_html=True,
        )


def _render_forecast(product_id: int, horizon: int) -> None:
    """Generate and display the forecast (service handles all errors)."""
    try:
        result = forecast_service.get_forecast(product_id, horizon)
    except forecast_service.ProductNotLinkError as error:
        st.info(str(error), icon=":material/link_off:")
        return
    except model_artifacts.ArtifactError as error:
        st.warning(
            t("forecast.artifact_warning"),
            icon=":material/pending:",
        )
        st.caption(str(error))
        return
    except forecast_service.ForecastError as error:
        # e.g. the DEC-058 "No suitable history exists" state or an
        # unsupported horizon: understandable conditions, not crashes.
        st.info(
            t("forecast.error_not_available", error=error),
            icon=":material/info:",
        )
        return
    except (DatabaseError, ValueError) as error:
        st.error(t("forecast.error_generation_failed", error=error))
        return

    section(
        "insights",
        t(
            "forecast.section_result",
            name=result["product"]["name"],
            sku=result["product"]["sku"],
        ),
    )
    # Yellow pill = the estimate/caution tone (DEC-065): every number
    # below is an estimate, not a guaranteed outcome.
    st.markdown(
        f'{pill(t("forecast.pill_estimate"), "caution")} '
        + t("forecast.pill_note"),
        unsafe_allow_html=True,
    )
    method_code = result["model_used"]
    method_label = (
        t(MODEL_LABELS[method_code])
        if method_code in MODEL_LABELS
        else method_code
    )
    st.caption(t("forecast.method_caption", method=method_label))

    rows = result["rows"]
    total = sum(row["predicted_demand"] for row in rows)
    columns = st.columns(3)
    columns[0].metric(
        t("forecast.metric_total", days=result["horizon_days"]),
        f"{total:.1f}",
        icon=":material/trending_up:",
        border=True,
    )
    columns[1].metric(
        t("forecast.metric_avg_per_day"),
        f"{total / len(rows):.1f}",
        icon=":material/calendar_month:",
        border=True,
    )
    columns[2].metric(
        t("forecast.metric_dataset_item"),
        result["dataset_item_id"],
        icon=":material/dataset:",
        border=True,
    )

    import pandas as pd

    date_label = t("forecast.column_date")
    demand_label = t("forecast.column_predicted")
    table = pd.DataFrame(
        [
            {
                date_label: row["forecast_date"],
                demand_label: row["predicted_demand"],
            }
            for row in rows
        ]
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            demand_label: st.column_config.NumberColumn(
                demand_label, format="%.1f",
            ),
        },
    )
    st.caption(t("forecast.rounding_caption"))
