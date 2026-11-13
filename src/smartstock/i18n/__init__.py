"""Bilingual interface support — English / Arabic (F-020, DEC-066).

One small translation module instead of a framework dependency:

- :data:`SUPPORTED_LANGUAGES` — the two interface languages.
- :func:`current_language` / :func:`set_language` — the active
  language, kept in Streamlit session state (default English).
- :func:`t` — translate a key for a language, with placeholders.
- :func:`language_switcher` — the sidebar language control.
- :func:`apply_direction` — right-to-left CSS for the Arabic UI.

Design rules (DEC-066):

- **English is the default language.** The approved UI tests pin
  English widget labels, so an untouched session renders exactly the
  pre-existing interface; switching to Arabic is an explicit user
  action.
- **Strings live in one table.** Pages request ``t("page.key")``; both
  languages must define every key (enforced by ``tests/test_i18n.py``),
  so a missing translation can never silently leak an English label
  into the Arabic UI or vice versa.
- **No business logic here.** This module only chooses words; pages
  remain responsible for behavior.

Arabic rendering notes: the interface text flips to Arabic and the
whole app switches to right-to-left direction; numerals and SKUs stay
in Western digits in v1 (deliberate, documented in the UI overview).
"""

import streamlit as st

# The two interface languages, shown in the switcher in their own
# language so users can always find their language (F-020).
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ar": "العربية",
}

DEFAULT_LANGUAGE = "en"

_SESSION_KEY = "language"


def current_language() -> str:
    """Return the active language code: ``"en"`` (default) or ``"ar"``.

    Falls back to the default when session state is unavailable (bare
    test runners), so helpers always return a valid language.
    """
    try:
        return st.session_state.get(_SESSION_KEY, DEFAULT_LANGUAGE)
    except Exception:  # noqa: BLE001 — no runtime context in bare runners
        return DEFAULT_LANGUAGE


def set_language(code: str) -> None:
    """Set the active interface language.

    Raises ``ValueError`` for unsupported codes, before touching
    session state, so invalid input never changes anything.
    """
    if code not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(
            f"Unsupported language {code!r}; supported: {supported}"
        )
    try:
        st.session_state[_SESSION_KEY] = code
    except Exception:  # noqa: BLE001 — no runtime context in bare runners
        pass


def is_rtl() -> bool:
    """Whether the active language reads right-to-left."""
    return current_language() == "ar"


def t(key: str, lang: str | None = None, **params) -> str:
    """Translate ``key`` for ``lang`` (default: the active language).

    Lookup order: the requested language, then English (so an Arabic
    session never shows a raw key when only the English string exists),
    then the key itself. ``{placeholders}`` in the string are filled
    from ``params``.
    """
    language = lang if lang is not None else current_language()
    text = STRINGS.get(language, {}).get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    if params:
        text = text.format(**params)
    return text


def language_switcher() -> None:
    """Render the sidebar language control (call once, from app.py).

    Selecting the other language stores it in session state and reruns
    the app so every page re-renders in the new language.
    """
    chosen = st.selectbox(
        t("common.language"),
        list(SUPPORTED_LANGUAGES),
        format_func=lambda code: SUPPORTED_LANGUAGES[code],
        index=list(SUPPORTED_LANGUAGES).index(current_language()),
        key="language_switcher",
    )
    if chosen != current_language():
        set_language(chosen)
        st.rerun()


def apply_direction() -> None:
    """Apply right-to-left page direction for Arabic (DEC-066).

    Called from the shared UI design-system injection so every page
    render carries it. English sessions emit nothing.
    """
    if not is_rtl():
        return
    st.markdown(
        "<style>html { direction: rtl; }</style>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# The string table. Keys are namespaced by area ("nav", "common", then the
# page name). English strings are the exact interface strings the approved
# tests pin — do not reword them here without checking the tests.
# Arabic strings must cover every English key (parity-checked by tests).
# ---------------------------------------------------------------------------

STRINGS = {
    "en": {
        # Sidebar and navigation (app.py).
        "common.language": "Language",
        "nav.overview": "Overview",
        "nav.inventory": "Inventory",
        "nav.sales": "Sales",
        "nav.forecasting": "Forecasting",
        "nav.data": "Data",
        "nav.dashboard": "Dashboard",
        "nav.products": "Products & Inventory",
        "nav.restock": "Restocking Recommendations",
        "nav.sales_management": "Sales Management",
        "nav.analytics": "Sales Analytics",
        "nav.forecast": "Demand Forecast",
        "nav.imports": "Data Import",
        # Dashboard page (pilot translation, DEC-066).
        "dashboard.title": "Dashboard",
        "dashboard.description": (
            "Snapshot of the current inventory and sales situation. All "
            "windows end at today (UTC); restocking advice stays "
            "advisory (DEC-031)."
        ),
        "dashboard.trend_window": "Sales trend window",
        "dashboard.last_7_days": "Last 7 days",
        "dashboard.last_30_days": "Last 30 days",
        "dashboard.load_error": "Could not load the dashboard: {error}",
        "dashboard.metric_active_products": "Active products",
        "dashboard.metric_total_stock": "Total stock",
        "dashboard.metric_needs_reorder": "Products needing reorder",
        "dashboard.metric_needs_reorder_help": (
            "Current stock at or below the reorder point (BR-022). "
            "Products without sales history are not counted yet."
        ),
        "dashboard.metric_units_sold_7": "Units sold (last 7 days)",
        "dashboard.metric_sales_count_7": "Sales recorded (last 7 days)",
        "dashboard.metric_top_seller": "Top seller (30 days)",
        "dashboard.metric_top_seller_help": (
            "Units sold by the best-selling product of the last 30 days."
        ),
        "dashboard.trend_section_7": "Sales trend — last 7 days",
        "dashboard.trend_section_30": "Sales trend — last 30 days",
        "dashboard.trend_empty_title": "No sales in this window",
        "dashboard.trend_empty_message": (
            "Record sales on the Sales Management page to see trends "
            "here."
        ),
        "dashboard.top_section": "Top sellers — last 30 days",
        "dashboard.top_empty_title": "No sales in the last 30 days",
        "dashboard.top_empty_message": (
            "Once sales are recorded, the best-selling products appear "
            "here."
        ),
        "dashboard.column_rank": "Rank",
        "dashboard.column_name": "Name",
        "dashboard.column_sku": "SKU",
        "dashboard.column_units_sold": "Units sold",
        "dashboard.column_stock": "Stock",
        "dashboard.column_avg_demand": "Avg daily demand",
        "dashboard.column_reorder_point": "Reorder point",
        "dashboard.column_suggested_order": "Suggested order",
        "dashboard.low_section": "Low-stock overview",
        "dashboard.low_all_ok": "All products are In Stock.",
        "dashboard.low_warning": (
            "{count} product(s) are Out of Stock or Low Stock "
            "(current stock at or below the reorder point, BR-008)."
        ),
        "dashboard.low_caption": (
            "Order suggestions are advisory (DEC-031). Review details "
            "on the Restocking Recommendations page."
        ),
        "dashboard.readiness_section": "Forecast readiness",
        "dashboard.readiness_empty_title": "No active products yet",
        "dashboard.readiness_empty_message": (
            "Add products to start forecasting."
        ),
        "dashboard.readiness_none_linked": (
            "No product is linked to a dataset item yet, so nothing is "
            "forecastable. Link items on the Products & Inventory page "
            "(DEC-060), then open Demand Forecast."
        ),
        "dashboard.readiness_caption": (
            "{linked} of {total} active products are linked to a "
            "dataset item and can be forecast on the Demand Forecast "
            "page."
        ),
        # Sales Management page (TASK-020/021).
        "common.all": "All",
        "sales.title": "Sales Management",
        "sales.description": (
            "Recorded sales reduce stock automatically. Recording is "
            "rejected when the requested quantity exceeds the available "
            "stock — the sale is not stored and the inventory stays "
            "unchanged."
        ),
        "sales.tab_record": "Record sale",
        "sales.tab_history": "Sales history",
        "sales.record_section": "Record a sale",
        "sales.load_products_error": "Could not load products: {error}",
        "sales.no_products_title": "No products yet",
        "sales.no_products_entry_message": (
            "A sale needs a product. Add one on the Products & "
            "Inventory page first."
        ),
        "sales.no_products_history_message": (
            "Sales history appears here once products and sales exist."
        ),
        "sales.field_product": "Product *",
        "sales.product_label": "{name} ({sku}) — {stock} in stock",
        "sales.metric_available_stock": "Available stock",
        "sales.field_quantity": "Quantity *",
        "sales.field_sale_date": "Sale date *",
        "sales.sale_date_help": (
            "Backdated entries are allowed; future dates are rejected."
        ),
        "sales.button_record": "Record sale",
        "sales.error_date_required": "Sale date is required.",
        "sales.error_not_recorded": "Sale not recorded: {error}",
        "sales.success_recorded": (
            "Recorded sale of {quantity} unit(s) of '{name}' on {date}. "
            "Remaining stock: {stock}."
        ),
        "sales.history_section": "Sales history",
        "sales.load_history_error": (
            "Could not load sales history: {error}"
        ),
        "sales.filter_product": "Product",
        "sales.filter_all_time": "All time",
        "sales.filter_from": "From",
        "sales.filter_to": "To",
        "sales.warning_date_order": (
            "The 'From' date is after the 'To' date."
        ),
        "sales.caption_all_time": (
            "{count} sale(s), {units} unit(s) total (all time)."
        ),
        "sales.caption_between": (
            "{count} sale(s), {units} unit(s) total between {start} "
            "and {end}."
        ),
        "sales.empty_no_sales_title": "No sales recorded yet",
        "sales.empty_no_sales_message": (
            "Record the first sale in the **Record sale** tab."
        ),
        "sales.info_no_match": "No sales match the current filters.",
        "sales.column_product": "Product",
        "sales.column_quantity": "Quantity",
        "sales.column_sale_date": "Sale date",
        "sales.column_recorded_at": "Recorded at",
        "sales.unknown_product": "Product {id}",
        # Products & Inventory page (TASK-016/017/018).
        "products.title": "Products & Inventory",
        "products.description": (
            "Active products with their current stock and stock status "
            "(reorder point = average daily demand of the last 30 days "
            "× lead time + safety stock)."
        ),
        "products.tab_list": "Product list",
        "products.tab_add": "Add product",
        "products.tab_edit": "Edit product",
        "products.tab_stock": "Adjust stock",
        "products.load_error": "Could not load products: {error}",
        "products.no_products_title": "No products yet",
        "products.no_products_list_message": (
            "Create your first product in the **Add product** tab "
            "above to start tracking stock and demand."
        ),
        "products.no_products_edit_title": "No products to edit yet",
        "products.no_products_first_message": (
            "Add a product in the **Add product** tab first."
        ),
        "products.no_match_warning": (
            "No products match the current search and filters."
        ),
        "products.search_label": "Search products",
        "products.search_placeholder": "Type a product name or SKU…",
        "products.search_help": (
            "Filters by product name or SKU, case-insensitive."
        ),
        "products.filter_category": "Category",
        "products.no_category": "(no category)",
        "products.filter_status": "Stock status",
        "products.caption_showing": (
            "Showing {shown} of {total} products."
        ),
        "products.column_name": "Name",
        "products.column_sku": "SKU",
        "products.column_category": "Category",
        "products.column_stock": "Stock",
        "products.column_lead_time": "Lead time (days)",
        "products.column_safety_stock": "Safety stock",
        "products.column_reorder_point": "Reorder point",
        "products.column_avg_demand": "Avg daily demand",
        "products.column_status": "Status",
        "products.low_stock_warning": (
            "{count} product(s) are Out of Stock or Low Stock and may "
            "need restocking: {names}."
        ),
        "products.add_section": "Add product",
        "products.add_caption": (
            "Required: name and SKU. Lead time defaults to 3 days and "
            "safety stock to 0."
        ),
        "products.field_name": "Name *",
        "products.field_sku": "SKU *",
        "products.field_category": "Category (optional)",
        "products.field_initial_stock": "Initial stock",
        "products.field_lead_time": "Lead time (days)",
        "products.field_safety_stock": "Safety stock",
        "products.button_create": "Create product",
        "products.error_not_created": "Product not created: {error}",
        "products.success_created": (
            "Created '{name}' ({sku}) with {stock} units in stock."
        ),
        "products.edit_section": "Edit product",
        "products.select_to_edit": "Product to edit",
        "products.product_label": "{name} ({sku}){flag}",
        "products.inactive_flag": " (inactive)",
        "products.field_dataset_item": (
            "Linked dataset item (optional, blank = none)"
        ),
        "products.field_link_item": (
            "Forecast via a linked dataset item"
        ),
        "products.button_save": "Save changes",
        "products.caption_soft_delete": (
            "Removal deactivates the product (soft delete): history is "
            "kept and the action is reversible (DEC-048)."
        ),
        "products.confirm_deactivate": (
            "I understand this deactivates the product"
        ),
        "products.button_deactivate": "Deactivate product",
        "products.error_confirm_first": "Tick the confirmation box first.",
        "products.error_not_deactivated": (
            "Product not deactivated: {error}"
        ),
        "products.success_deactivated": (
            "'{name}' deactivated. Its sales history is preserved; "
            "reactivation is possible."
        ),
        "products.caption_inactive": (
            "This product is currently deactivated (not listed, not "
            "sold). You can edit it or reactivate it below."
        ),
        "products.button_reactivate": "Reactivate product",
        "products.error_not_reactivated": (
            "Product not reactivated: {error}"
        ),
        "products.success_reactivated": "'{name}' reactivated.",
        "products.error_not_saved": "Changes not saved: {error}",
        "products.success_updated": "Updated '{name}' ({sku}).",
        "products.stock_section": "Adjust stock",
        "products.stock_caption": (
            "**Add / remove units** for receipts, damage, and manual "
            "changes. **Set exact stock** is a correction that "
            "overwrites the stored value — use it to fix wrong data."
        ),
        "products.operation_label": "Operation",
        "products.operation_change": "Add or remove units",
        "products.operation_exact": "Set exact stock (correction)",
        "products.stock_filter_product": "Product",
        "products.metric_current_stock": "Current stock",
        "products.field_change": "Change (+ receive / − remove)",
        "products.button_apply": "Apply adjustment",
        "products.error_adjustment_rejected": "Adjustment rejected: {error}",
        "products.success_adjusted": (
            "Stock adjusted. '{name}' now has {stock} units."
        ),
        "products.exact_warning": (
            "Corrections overwrite the stored stock without a recorded "
            "explanation. Prefer 'Add or remove units' for regular "
            "changes."
        ),
        "products.field_exact": "Exact stock count",
        "products.button_set": "Set stock level",
        "products.error_correction_rejected": "Correction rejected: {error}",
        "products.success_set": (
            "Stock set to {stock} units for '{name}'."
        ),
        # Restocking Recommendations page (TASK-036).
        "restock.title": "Restocking Recommendations",
        "restock.description": (
            "Advisory only — nothing is ordered automatically. Demand "
            "is the average daily sold quantity up to the most recent "
            "sale (days without sales count as zero)."
        ),
        "restock.load_error": "Could not load recommendations: {error}",
        "restock.empty_title": "No active products yet",
        "restock.empty_message": (
            "Add products on the Products & Inventory page to receive "
            "restocking recommendations."
        ),
        "restock.metric_needs_reorder": "Products needing reorder",
        "restock.metric_available": "Recommendations available",
        "restock.metric_no_data": "Without enough data",
        "restock.metric_no_data_help": (
            "No sales history or no stock level recorded yet."
        ),
        "restock.section_restock": "Consider restocking",
        "restock.all_ok": (
            "No product is at or below its reorder point right now."
        ),
        "restock.section_unavailable": "Not available yet",
        "restock.column_name": "Name",
        "restock.column_sku": "SKU",
        "restock.column_stock": "Stock",
        "restock.column_avg_demand": "Avg daily demand",
        "restock.column_lead_time": "Lead time (days)",
        "restock.column_safety_stock": "Safety stock",
        "restock.column_reorder_point": "Reorder point",
        "restock.column_target": "Target stock",
        "restock.column_order": "Order",
        "restock.export_button": "Export recommendations (CSV)",
        "restock.expander_title": (
            "{name} ({sku}) — order {count} unit(s)"
        ),
        "restock.hero_label": (
            "Suggested order (units) — {name} ({sku})"
        ),
        # Sales Analytics page (TASK-041).
        "common.all_products": "All products",
        "analytics.title": "Sales Analytics",
        "analytics.description": (
            "Quantity-based sales insights (F-006): units sold and "
            "patterns. Revenue analytics need price data the "
            "application does not store."
        ),
        "analytics.load_products_error": "Could not load products: {error}",
        "analytics.empty_title": "No active products yet",
        "analytics.empty_message": (
            "Add products on the Products & Inventory page, then "
            "record sales to see analytics."
        ),
        "analytics.filter_start": "Start date",
        "analytics.filter_end": "End date",
        "analytics.filter_product": "Product filter",
        "analytics.error_invalid_range": "Invalid range: {error}",
        "analytics.load_error": "Could not load analytics: {error}",
        "analytics.metric_units_sold": "Units sold",
        "analytics.metric_sales_recorded": "Sales recorded",
        "analytics.metric_avg_per_day": "Avg units/day",
        "analytics.metric_avg_help": (
            "Over all {days} days in the range (days without sales "
            "count as zero)."
        ),
        "analytics.metric_days_with_sales": "Days with sales",
        "analytics.metric_days_help": (
            "Out of {days} days in the range."
        ),
        "analytics.section_daily": "Daily units sold",
        "analytics.no_sales_title": "No sales in this range",
        "analytics.no_sales_daily_message": (
            "Record sales in this date range, or widen the range, to "
            "see the daily trend."
        ),
        "analytics.section_weekday": "Weekday pattern",
        "analytics.weekday_caption": (
            "Average units sold per weekday over the whole range — "
            "days without sales count as zero."
        ),
        "analytics.column_weekday": "Weekday",
        "analytics.column_avg_units": "Avg units",
        "analytics.weekday_mon": "Mon",
        "analytics.weekday_tue": "Tue",
        "analytics.weekday_wed": "Wed",
        "analytics.weekday_thu": "Thu",
        "analytics.weekday_fri": "Fri",
        "analytics.weekday_sat": "Sat",
        "analytics.weekday_sun": "Sun",
        "analytics.section_per_product": "Sales by product",
        "analytics.no_sales_product_message": (
            "Record sales in this date range, or widen the range, to "
            "see the per-product ranking."
        ),
        "analytics.column_rank": "Rank",
        "analytics.column_name": "Name",
        "analytics.column_sku": "SKU",
        "analytics.column_units_sold": "Units sold",
        "analytics.column_sales": "Sales",
        "analytics.column_share": "Share",
        "analytics.export_per_product": "Export sales by product (CSV)",
        "analytics.section_performance": "Product performance",
        "analytics.no_sales_perf_message": (
            "Record sales in this date range, or widen the range, to "
            "see per-product performance."
        ),
        "analytics.load_perf_error": (
            "Could not load product performance: {error}"
        ),
        "analytics.column_avg_per_day": "Avg units/day",
        "analytics.column_first_sale": "First sale",
        "analytics.column_last_sale": "Last sale",
        "analytics.column_trend": "Trend",
        "analytics.trend_caption": (
            "Trend compares the two calendar halves of the range "
            "(zeros count): Rising/Falling when the second half's "
            "daily average differs by ≥ 15%. Stock-warning frequency "
            "is not tracked in v1 — warnings are advisory snapshots, "
            "not logged events."
        ),
        "analytics.export_performance": "Export product performance (CSV)",
        "analytics.section_monthly": "Monthly totals",
        "analytics.column_month": "Month",
        "analytics.export_monthly": "Export monthly totals (CSV)",
        # Demand Forecast page (DEC-026/058/060).
        "forecast.title": "Demand Forecast",
        "forecast.description": (
            "Advisory demand estimates per product, based on the "
            "linked dataset item's imported sales history. Forecasts "
            "are estimates — not guaranteed outcomes."
        ),
        "forecast.load_products_error": "Could not load products: {error}",
        "forecast.empty_title": "No active products yet",
        "forecast.empty_message": (
            "Add products on the Products & Inventory page first."
        ),
        "forecast.filter_product": "Product",
        "forecast.horizon_label": "Forecast horizon",
        "forecast.horizon_7": "Next 7 days",
        "forecast.horizon_14": "Next 14 days",
        "forecast.horizon_30": "Next 30 days",
        "forecast.model_rf": (
            "Random Forest model (needs ≥ 31 days of history)"
        ),
        "forecast.model_ma7": (
            "Trailing 7-day average fallback (history under 31 days, "
            "DEC-058)"
        ),
        "forecast.button_generate": "Generate forecast",
        "forecast.section_accuracy": "How accurate is the model?",
        "forecast.eval_not_available": (
            "Evaluation metrics become available after the model is "
            "trained — run ``scripts/train_model.py`` first."
        ),
        "forecast.eval_caption": (
            "Measured during model selection on held-out evaluation "
            "data (MAE/RMSE in units per product-day — lower is "
            "better). No predictions are generated here, so the "
            "one-time 2017 test window stays untouched (DEC-056)."
        ),
        "forecast.eval_window_help": (
            "RMSE {rmse} over {predictions:,} product-days."
        ),
        "forecast.eval_baselines": (
            "Context — simple baselines on the same validation data: "
            "{baselines}. The model must beat these to be selected "
            "(DEC-027) — and it did."
        ),
        "forecast.eval_model_caption": (
            "Model: {name} v{version}, trained {trained_at}. "
            "Forecasts are estimates — actual demand can differ "
            "(prediction-logic §11)."
        ),
        "forecast.no_link_info": (
            "'{name}' has no dataset item linked yet. Set 'Linked "
            "dataset item' in the product's edit form (Replenishing → "
            "Edit product) to enable forecasting (DEC-060)."
        ),
        "forecast.linked_label": "Linked dataset item",
        "forecast.artifact_warning": (
            "The forecasting model artifact is not available — run "
            "``scripts/train_model.py`` first."
        ),
        "forecast.error_not_available": "Forecast not available: {error}",
        "forecast.error_generation_failed": (
            "Could not generate the forecast: {error}"
        ),
        "forecast.section_result": "Forecast for {name} ({sku})",
        "forecast.pill_estimate": "Estimate",
        "forecast.pill_note": (
            "These are demand estimates — actual demand can differ."
        ),
        "forecast.method_caption": "Method: {method}",
        "forecast.metric_total": "Total demand ({days} days)",
        "forecast.metric_avg_per_day": "Average per day",
        "forecast.metric_dataset_item": "Dataset item",
        "forecast.column_date": "Date",
        "forecast.column_predicted": "Predicted demand",
        "forecast.rounding_caption": (
            "Raw predictions are rounded for display only; restocking "
            "formulas use their own approved demand rule (DEC-059)."
        ),
        # Data Import page (TASK-023/024/025).
        "imports.title": "Data Import",
        "imports.description": (
            "Historical CSV import for forecasting (format: date, "
            "store, item, sales). Rows are filtered to store 1 per the "
            "project's single-store decision. Imports never change "
            "current stock — they only feed analysis and forecasting."
        ),
        "imports.uploader_label": "Historical sales CSV *",
        "imports.empty_title": "Nothing uploaded yet",
        "imports.empty_message": (
            "Upload a CSV file to validate it and preview the records "
            "before importing. Nothing is stored until you confirm."
        ),
        "imports.error_file": "The file cannot be imported: {error}",
        "imports.section_preview": "Preview",
        "imports.caption_file": (
            "{filename} — {size:,} bytes · fingerprint {fingerprint}…"
        ),
        "imports.metric_rows": "Rows in file",
        "imports.metric_valid": "Valid for store 1",
        "imports.metric_rejected": "Rejected (invalid)",
        "imports.metric_other_stores": "Other stores",
        "imports.caption_date_range": (
            "Date range of accepted rows: {first} → {last}; "
            "{duplicates:,} within-file duplicate(s)."
        ),
        "imports.caption_no_rows": "No rows are in scope for store 1.",
        "imports.warning_nothing": (
            "Nothing to import: the file contains no valid rows for "
            "store 1."
        ),
        "imports.sample_caption": "Sample of accepted records:",
        "imports.button_import": "Import {count:,} record(s)",
        "imports.button_import_help": (
            "Validated rows are stored in one transaction. Historical "
            "records never change current stock."
        ),
        "imports.error_rejected": "Nothing was imported: {error}",
        "imports.error_failed": (
            "The import failed and nothing was stored: {error}"
        ),
        "imports.success_imported": (
            "Imported {count:,} historical record(s) from '{filename}' "
            "(batch #{batch_id}). Current stock was not changed."
        ),
        "imports.result_success": (
            "Import completed — batch #{batch_id} ({created_at})."
        ),
        "imports.result_metric_stored": "Accepted and stored",
        "imports.result_metric_duplicates": "Duplicates skipped",
        "imports.result_date_note": (
            " · accepted rows span {first} → {last}"
        ),
        "imports.result_caption": (
            "Historical dataset import, store {store} · file "
            "'{filename}' ({rows:,} rows processed){date_note}. "
            "Current inventory was not changed."
        ),
        "imports.result_reupload_info": (
            "To import more data, upload a different CSV file. "
            "Re-uploading this exact file is rejected by its "
            "fingerprint (DEC-053)."
        ),
        "imports.history_title": "Previous imports",
        "imports.history_error": (
            "Import history could not be read: {error}"
        ),
        "imports.history_caption": (
            "{records:,} historical record(s) stored in total across "
            "{count} import run(s)."
        ),
        "imports.history_empty": "No imports recorded yet.",
        "imports.column_batch": "Batch",
        "imports.column_file": "File",
        "imports.column_imported": "Imported",
        "imports.column_duplicates": "Duplicates skipped",
        "imports.column_rejected": "Rejected",
        "imports.column_other_stores": "Other stores",
        "imports.column_date_range": "Date range",
        "imports.column_when": "When (UTC)",
        "imports.expander_rejected": "Rejected rows",
        "imports.expander_duplicates": "Within-file duplicates",
        "imports.shown_suffix": "({count} shown)",
        "imports.truncated_caption": (
            "Showing the first examples only — see the totals in the "
            "metrics above."
        ),
        "imports.row_line": "- Row {number}: {reason}",
    },
    "ar": {
        # Sidebar and navigation (app.py).
        "common.language": "اللغة",
        "nav.overview": "نظرة عامة",
        "nav.inventory": "المخزون",
        "nav.sales": "المبيعات",
        "nav.forecasting": "التنبؤ",
        "nav.data": "البيانات",
        "nav.dashboard": "لوحة التحكم",
        "nav.products": "المنتجات والمخزون",
        "nav.restock": "اقتراحات إعادة التخزين",
        "nav.sales_management": "إدارة المبيعات",
        "nav.analytics": "تحليلات المبيعات",
        "nav.forecast": "التنبؤ بالطلب",
        "nav.imports": "استيراد البيانات",
        # Dashboard page.
        "dashboard.title": "لوحة التحكم",
        "dashboard.description": (
            "نظرة سريعة على حالة المخزون والمبيعات الحالية. جميع الفترات "
            "تنتهي عند اليوم (بتوقيت UTC)؛ وتبقى اقتراحات إعادة التخزين "
            "استشارية فقط (DEC-031)."
        ),
        "dashboard.trend_window": "نطاق اتجاه المبيعات",
        "dashboard.last_7_days": "آخر 7 أيام",
        "dashboard.last_30_days": "آخر 30 يومًا",
        "dashboard.load_error": "تعذر تحميل لوحة التحكم: {error}",
        "dashboard.metric_active_products": "المنتجات النشطة",
        "dashboard.metric_total_stock": "إجمالي المخزون",
        "dashboard.metric_needs_reorder": "منتجات تحتاج إعادة طلب",
        "dashboard.metric_needs_reorder_help": (
            "المخزون الحالي عند نقطة إعادة الطلب أو أقل منها (BR-022). "
            "المنتجات التي لا يوجد لها سجل مبيعات لا تُحتسب بعد."
        ),
        "dashboard.metric_units_sold_7": "الوحدات المباعة (آخر 7 أيام)",
        "dashboard.metric_sales_count_7": (
            "عمليات البيع المسجلة (آخر 7 أيام)"
        ),
        "dashboard.metric_top_seller": "الأكثر مبيعًا (30 يومًا)",
        "dashboard.metric_top_seller_help": (
            "عدد الوحدات المباعة من المنتج الأكثر مبيعًا خلال آخر "
            "30 يومًا."
        ),
        "dashboard.trend_section_7": "اتجاه المبيعات — آخر 7 أيام",
        "dashboard.trend_section_30": "اتجاه المبيعات — آخر 30 يومًا",
        "dashboard.trend_empty_title": "لا مبيعات في هذه الفترة",
        "dashboard.trend_empty_message": (
            "سجّل عمليات بيع من صفحة إدارة المبيعات لتظهر الاتجاهات هنا."
        ),
        "dashboard.top_section": "الأكثر مبيعًا — آخر 30 يومًا",
        "dashboard.top_empty_title": "لا مبيعات في آخر 30 يومًا",
        "dashboard.top_empty_message": (
            "بمجرد تسجيل عمليات البيع، ستظهر المنتجات الأكثر مبيعًا هنا."
        ),
        "dashboard.column_rank": "الترتيب",
        "dashboard.column_name": "الاسم",
        "dashboard.column_sku": "SKU",
        "dashboard.column_units_sold": "الوحدات المباعة",
        "dashboard.column_stock": "المخزون",
        "dashboard.column_avg_demand": "متوسط الطلب اليومي",
        "dashboard.column_reorder_point": "نقطة إعادة الطلب",
        "dashboard.column_suggested_order": "الكمية المقترح طلبها",
        "dashboard.low_section": "نظرة على المخزون المنخفض",
        "dashboard.low_all_ok": "جميع المنتجات حالتها In Stock.",
        "dashboard.low_warning": (
            "{count} منتج حالتها Out of Stock أو Low Stock "
            "(المخزون الحالي عند نقطة إعادة الطلب أو أقل منها، BR-008)."
        ),
        "dashboard.low_caption": (
            "اقتراحات الطلب استشارية فقط (DEC-031). راجع التفاصيل في "
            "صفحة اقتراحات إعادة التخزين."
        ),
        "dashboard.readiness_section": "جاهزية التنبؤ",
        "dashboard.readiness_empty_title": "لا توجد منتجات نشطة بعد",
        "dashboard.readiness_empty_message": (
            "أضف منتجات لبدء التنبؤ."
        ),
        "dashboard.readiness_none_linked": (
            "لا يوجد منتج مرتبط بعنصر بيانات مستوردة بعد، لذا لا يمكن "
            "التنبؤ لأي منتج. اربط العناصر من صفحة المنتجات والمخزون "
            "(DEC-060)، ثم افتح صفحة التنبؤ بالطلب."
        ),
        "dashboard.readiness_caption": (
            "{linked} من {total} منتج نشط مرتبط بعنصر بيانات ويمكن "
            "التنبؤ له من صفحة التنبؤ بالطلب."
        ),
        # Sales Management page (TASK-020/021).
        "common.all": "الكل",
        "sales.title": "إدارة المبيعات",
        "sales.description": (
            "تسجيل عملية البيع يخفض المخزون تلقائيًا. يتم رفض التسجيل "
            "إذا كانت الكمية المطلوبة أكبر من المخزون المتاح — لا "
            "تُسجَّل العملية ولا يتغير المخزون."
        ),
        "sales.tab_record": "تسجيل عملية بيع",
        "sales.tab_history": "سجل المبيعات",
        "sales.record_section": "تسجيل عملية بيع",
        "sales.load_products_error": "تعذر تحميل المنتجات: {error}",
        "sales.no_products_title": "لا توجد منتجات بعد",
        "sales.no_products_entry_message": (
            "عملية البيع تحتاج منتجًا. أضف منتجًا من صفحة المنتجات "
            "والمخزون أولًا."
        ),
        "sales.no_products_history_message": (
            "سيظهر سجل المبيعات هنا بعد إضافة منتجات وتسجيل عمليات بيع."
        ),
        "sales.field_product": "المنتج *",
        "sales.product_label": "{name} ({sku}) — {stock} في المخزون",
        "sales.metric_available_stock": "المخزون المتاح",
        "sales.field_quantity": "الكمية *",
        "sales.field_sale_date": "تاريخ البيع *",
        "sales.sale_date_help": (
            "يُسمح بتسجيل مبيعات بتواريخ سابقة؛ أما التواريخ "
            "المستقبلية فمرفوضة."
        ),
        "sales.button_record": "تسجيل عملية بيع",
        "sales.error_date_required": "تاريخ البيع مطلوب.",
        "sales.error_not_recorded": "لم تُسجَّل عملية البيع: {error}",
        "sales.success_recorded": (
            "تم تسجيل بيع {quantity} وحدة من '{name}' بتاريخ {date}. "
            "المخزون المتبقي: {stock}."
        ),
        "sales.history_section": "سجل المبيعات",
        "sales.load_history_error": (
            "تعذر تحميل سجل المبيعات: {error}"
        ),
        "sales.filter_product": "المنتج",
        "sales.filter_all_time": "كل الفترات",
        "sales.filter_from": "من",
        "sales.filter_to": "إلى",
        "sales.warning_date_order": "تاريخ 'من' يأتي بعد تاريخ 'إلى'.",
        "sales.caption_all_time": (
            "{count} عملية بيع، بإجمالي {units} وحدة (كل الفترات)."
        ),
        "sales.caption_between": (
            "{count} عملية بيع، بإجمالي {units} وحدة بين {start} "
            "و{end}."
        ),
        "sales.empty_no_sales_title": "لا توجد عمليات بيع مسجلة بعد",
        "sales.empty_no_sales_message": (
            "سجّل أول عملية بيع من تبويب **تسجيل عملية بيع**."
        ),
        "sales.info_no_match": (
            "لا توجد عمليات بيع تطابق عوامل التصفية الحالية."
        ),
        "sales.column_product": "المنتج",
        "sales.column_quantity": "الكمية",
        "sales.column_sale_date": "تاريخ البيع",
        "sales.column_recorded_at": "وقت التسجيل",
        "sales.unknown_product": "منتج {id}",
        # Products & Inventory page (TASK-016/017/018).
        "products.title": "المنتجات والمخزون",
        "products.description": (
            "المنتجات النشطة مع مخزونها الحالي وحالة المخزون (نقطة "
            "إعادة الطلب = متوسط الطلب اليومي لآخر 30 يومًا × مدة "
            "الوصول + المخزون الاحتياطي)."
        ),
        "products.tab_list": "قائمة المنتجات",
        "products.tab_add": "إضافة منتج",
        "products.tab_edit": "تعديل منتج",
        "products.tab_stock": "تعديل المخزون",
        "products.load_error": "تعذر تحميل المنتجات: {error}",
        "products.no_products_title": "لا توجد منتجات بعد",
        "products.no_products_list_message": (
            "أنشئ أول منتج من تبويب **إضافة منتج** بالأعلى لبدء تتبع "
            "المخزون والطلب."
        ),
        "products.no_products_edit_title": "لا توجد منتجات للتعديل بعد",
        "products.no_products_first_message": (
            "أضف منتجًا من تبويب **إضافة منتج** أولًا."
        ),
        "products.no_match_warning": (
            "لا توجد منتجات تطابق البحث والتصفية الحالية."
        ),
        "products.search_label": "البحث في المنتجات",
        "products.search_placeholder": "اكتب اسم منتج أو SKU…",
        "products.search_help": (
            "تصفية حسب اسم المنتج أو SKU، دون حساسية لحالة الأحرف."
        ),
        "products.filter_category": "الفئة",
        "products.no_category": "(بدون فئة)",
        "products.filter_status": "حالة المخزون",
        "products.caption_showing": "عرض {shown} من {total} منتج.",
        "products.column_name": "الاسم",
        "products.column_sku": "SKU",
        "products.column_category": "الفئة",
        "products.column_stock": "المخزون",
        "products.column_lead_time": "مدة الوصول (أيام)",
        "products.column_safety_stock": "المخزون الاحتياطي",
        "products.column_reorder_point": "نقطة إعادة الطلب",
        "products.column_avg_demand": "متوسط الطلب اليومي",
        "products.column_status": "الحالة",
        "products.low_stock_warning": (
            "{count} منتج حالتها Out of Stock أو Low Stock وقد تحتاج "
            "إعادة تخزين: {names}."
        ),
        "products.add_section": "إضافة منتج",
        "products.add_caption": (
            "المطلوب: الاسم وSKU. مدة الوصول الافتراضية 3 أيام "
            "والمخزون الاحتياطي 0."
        ),
        "products.field_name": "الاسم *",
        "products.field_sku": "SKU *",
        "products.field_category": "الفئة (اختياري)",
        "products.field_initial_stock": "المخزون الأولي",
        "products.field_lead_time": "مدة الوصول (أيام)",
        "products.field_safety_stock": "المخزون الاحتياطي",
        "products.button_create": "إنشاء منتج",
        "products.error_not_created": "لم يُنشأ المنتج: {error}",
        "products.success_created": (
            "تم إنشاء '{name}' ({sku}) بكمية {stock} وحدة في المخزون."
        ),
        "products.edit_section": "تعديل منتج",
        "products.select_to_edit": "المنتج المطلوب تعديله",
        "products.product_label": "{name} ({sku}){flag}",
        "products.inactive_flag": " (غير نشط)",
        "products.field_dataset_item": (
            "عنصر بيانات مرتبط (اختياري، فارغ = بدون)"
        ),
        "products.field_link_item": "التنبؤ عبر عنصر بيانات مرتبط",
        "products.button_save": "حفظ التغييرات",
        "products.caption_soft_delete": (
            "الإزالة تعطل المنتج (حذف ناعم): يبقى السجل محفوظًا ويمكن "
            "التراجع عن الإجراء (DEC-048)."
        ),
        "products.confirm_deactivate": (
            "أفهم أن هذا الإجراء سيعطل المنتج"
        ),
        "products.button_deactivate": "تعطيل المنتج",
        "products.error_confirm_first": "علّم مربع التأكيد أولًا.",
        "products.error_not_deactivated": "لم يُعطَّل المنتج: {error}",
        "products.success_deactivated": (
            "تم تعطيل '{name}'. يبقى سجل مبيعاته محفوظًا ويمكن إعادة "
            "تنشيطه."
        ),
        "products.caption_inactive": (
            "هذا المنتج معطل حاليًا (غير مُدرج، غير قابل للبيع). يمكنك "
            "تعديله أو إعادة تنشيطه أدناه."
        ),
        "products.button_reactivate": "إعادة تنشيط المنتج",
        "products.error_not_reactivated": (
            "لم يُعَد تنشيط المنتج: {error}"
        ),
        "products.success_reactivated": "تم إعادة تنشيط '{name}'.",
        "products.error_not_saved": "لم تُحفَظ التغييرات: {error}",
        "products.success_updated": "تم تحديث '{name}' ({sku}).",
        "products.stock_section": "تعديل المخزون",
        "products.stock_caption": (
            "**إضافة / إزالة وحدات** لاستلام البضائع أو تسجيل التالف "
            "أو التغييرات اليدوية. **تحديد مخزون محدد** إجراء تصحيحي "
            "يستبدل القيمة المخزنة — استخدمه لتصحيح بيانات خاطئة."
        ),
        "products.operation_label": "العملية",
        "products.operation_change": "إضافة أو إزالة وحدات",
        "products.operation_exact": "تحديد مخزون محدد (تصحيح)",
        "products.stock_filter_product": "المنتج",
        "products.metric_current_stock": "المخزون الحالي",
        "products.field_change": "التغيير (+ استلام / − إزالة)",
        "products.button_apply": "تطبيق التعديل",
        "products.error_adjustment_rejected": "تم رفض التعديل: {error}",
        "products.success_adjusted": (
            "تم تعديل المخزون. أصبح لدى '{name}' {stock} وحدة الآن."
        ),
        "products.exact_warning": (
            "التصحيحات تستبدل المخزون المخزن دون تسجيل سبب. يُفضل "
            "استخدام 'إضافة أو إزالة وحدات' للتغييرات العادية."
        ),
        "products.field_exact": "عدد المخزون الفعلي",
        "products.button_set": "تحديد مستوى المخزون",
        "products.error_correction_rejected": "تم رفض التصحيح: {error}",
        "products.success_set": (
            "تم تحديد المخزون عند {stock} وحدة للمنتج '{name}'."
        ),
        # Restocking Recommendations page (TASK-036).
        "restock.title": "اقتراحات إعادة التخزين",
        "restock.description": (
            "استشارية فقط — لا يتم طلب أي شيء تلقائيًا. الطلب هو متوسط "
            "الكمية المباعة يوميًا حتى آخر عملية بيع (الأيام بدون "
            "مبيعات تُحتسب صفرًا)."
        ),
        "restock.load_error": "تعذر تحميل الاقتراحات: {error}",
        "restock.empty_title": "لا توجد منتجات نشطة بعد",
        "restock.empty_message": (
            "أضف منتجات من صفحة المنتجات والمخزون لتظهر اقتراحات "
            "إعادة التخزين."
        ),
        "restock.metric_needs_reorder": "منتجات تحتاج إعادة طلب",
        "restock.metric_available": "توصيات متاحة",
        "restock.metric_no_data": "بدون بيانات كافية",
        "restock.metric_no_data_help": (
            "لا يوجد سجل مبيعات أو لا توجد كمية مخزون مسجلة بعد."
        ),
        "restock.section_restock": "فكّر في إعادة التخزين",
        "restock.all_ok": (
            "لا يوجد منتج عند نقطة إعادة الطلب أو أقل منها الآن."
        ),
        "restock.section_unavailable": "غير متاحة بعد",
        "restock.column_name": "الاسم",
        "restock.column_sku": "SKU",
        "restock.column_stock": "المخزون",
        "restock.column_avg_demand": "متوسط الطلب اليومي",
        "restock.column_lead_time": "مدة الوصول (أيام)",
        "restock.column_safety_stock": "المخزون الاحتياطي",
        "restock.column_reorder_point": "نقطة إعادة الطلب",
        "restock.column_target": "المخزون المستهدف",
        "restock.column_order": "الطلب",
        "restock.export_button": "تصدير الاقتراحات (CSV)",
        "restock.expander_title": "{name} ({sku}) — طلب {count} وحدة",
        "restock.hero_label": "الطلب المقترح (وحدات) — {name} ({sku})",
        # Sales Analytics page (TASK-041).
        "common.all_products": "كل المنتجات",
        "analytics.title": "تحليلات المبيعات",
        "analytics.description": (
            "رؤى مبيعات على أساس الكميات (F-006): الوحدات المباعة "
            "والأنماط. تحليلات الإيرادات تحتاج بيانات أسعار لا يخزنها "
            "التطبيق."
        ),
        "analytics.load_products_error": "تعذر تحميل المنتجات: {error}",
        "analytics.empty_title": "لا توجد منتجات نشطة بعد",
        "analytics.empty_message": (
            "أضف منتجات من صفحة المنتجات والمخزون، ثم سجّل عمليات بيع "
            "لتظهر التحليلات."
        ),
        "analytics.filter_start": "تاريخ البداية",
        "analytics.filter_end": "تاريخ النهاية",
        "analytics.filter_product": "تصفية المنتج",
        "analytics.error_invalid_range": "نطاق غير صالح: {error}",
        "analytics.load_error": "تعذر تحميل التحليلات: {error}",
        "analytics.metric_units_sold": "الوحدات المباعة",
        "analytics.metric_sales_recorded": "عمليات البيع المسجلة",
        "analytics.metric_avg_per_day": "متوسط الوحدات يوميًا",
        "analytics.metric_avg_help": (
            "على مدار كل الـ {days} يومًا في النطاق (الأيام بدون "
            "مبيعات تُحتسب صفرًا)."
        ),
        "analytics.metric_days_with_sales": "أيام بها مبيعات",
        "analytics.metric_days_help": "من أصل {days} يومًا في النطاق.",
        "analytics.section_daily": "الوحدات المباعة يوميًا",
        "analytics.no_sales_title": "لا مبيعات في هذا النطاق",
        "analytics.no_sales_daily_message": (
            "سجّل عمليات بيع في هذا النطاق الزمني، أو وسّع النطاق، "
            "لعرض الاتجاه اليومي."
        ),
        "analytics.section_weekday": "نمط أيام الأسبوع",
        "analytics.weekday_caption": (
            "متوسط الوحدات المباعة لكل يوم من أيام الأسبوع على مدار "
            "النطاق كاملًا — الأيام بدون مبيعات تُحتسب صفرًا."
        ),
        "analytics.column_weekday": "اليوم",
        "analytics.column_avg_units": "متوسط الوحدات",
        "analytics.weekday_mon": "الاثنين",
        "analytics.weekday_tue": "الثلاثاء",
        "analytics.weekday_wed": "الأربعاء",
        "analytics.weekday_thu": "الخميس",
        "analytics.weekday_fri": "الجمعة",
        "analytics.weekday_sat": "السبت",
        "analytics.weekday_sun": "الأحد",
        "analytics.section_per_product": "المبيعات حسب المنتج",
        "analytics.no_sales_product_message": (
            "سجّل عمليات بيع في هذا النطاق الزمني، أو وسّع النطاق، "
            "لعرض ترتيب المنتجات."
        ),
        "analytics.column_rank": "الترتيب",
        "analytics.column_name": "الاسم",
        "analytics.column_sku": "SKU",
        "analytics.column_units_sold": "الوحدات المباعة",
        "analytics.column_sales": "عمليات البيع",
        "analytics.column_share": "الحصة",
        "analytics.export_per_product": "تصدير المبيعات حسب المنتج (CSV)",
        "analytics.section_performance": "أداء المنتجات",
        "analytics.no_sales_perf_message": (
            "سجّل عمليات بيع في هذا النطاق الزمني، أو وسّع النطاق، "
            "لعرض أداء المنتجات."
        ),
        "analytics.load_perf_error": (
            "تعذر تحميل أداء المنتجات: {error}"
        ),
        "analytics.column_avg_per_day": "متوسط الوحدات يوميًا",
        "analytics.column_first_sale": "أول عملية بيع",
        "analytics.column_last_sale": "آخر عملية بيع",
        "analytics.column_trend": "الاتجاه",
        "analytics.trend_caption": (
            "يقارن الاتجاه بين نصفَي النطاق الزمني (الأصفار تُحتسب): "
            "صاعد/هابط عندما يختلف متوسط النصف الثاني اليومي بمقدار "
            "15% أو أكثر. لا يتم تتبع تكرار تحذيرات المخزون في v1 — "
            "التحذيرات لقطات استشارية وليست أحداثًا مسجلة."
        ),
        "analytics.export_performance": "تصدير أداء المنتجات (CSV)",
        "analytics.section_monthly": "إجماليات شهرية",
        "analytics.column_month": "الشهر",
        "analytics.export_monthly": "تصدير الإجماليات الشهرية (CSV)",
        # Demand Forecast page (DEC-026/058/060).
        "forecast.title": "التنبؤ بالطلب",
        "forecast.description": (
            "تقديرات استشارية للطلب لكل منتج، بناءً على سجل المبيعات "
            "المستورد للعنصر المرتبط به. التوقعات تقديرات — وليست "
            "نتائج مضمونة."
        ),
        "forecast.load_products_error": "تعذر تحميل المنتجات: {error}",
        "forecast.empty_title": "لا توجد منتجات نشطة بعد",
        "forecast.empty_message": (
            "أضف منتجات من صفحة المنتجات والمخزون أولًا."
        ),
        "forecast.filter_product": "المنتج",
        "forecast.horizon_label": "أفق التنبؤ",
        "forecast.horizon_7": "الأيام السبعة القادمة",
        "forecast.horizon_14": "الأيام الأربعة عشرة القادمة",
        "forecast.horizon_30": "الثلاثون يومًا القادمة",
        "forecast.model_rf": (
            "نموذج Random Forest (يحتاج 31 يومًا من السجل أو أكثر)"
        ),
        "forecast.model_ma7": (
            "متوسط آخر 7 أيام (السجل أقل من 31 يومًا، DEC-058)"
        ),
        "forecast.button_generate": "توليد التنبؤ",
        "forecast.section_accuracy": "ما مدى دقة النموذج؟",
        "forecast.eval_not_available": (
            "تتوفر مقاييس التقييم بعد تدريب النموذج — شغّل "
            "``scripts/train_model.py`` أولًا."
        ),
        "forecast.eval_caption": (
            "قِيست أثناء اختيار النموذج على بيانات تقييم محجوزة "
            "(MAE/RMSE بوحدة لكل منتج-يوم — الأقل أفضل). لا يتم "
            "توليد أي تنبؤات هنا، لذا تبقى نافذة اختبار 2017 لمرة "
            "واحدة دون مساس (DEC-056)."
        ),
        "forecast.eval_window_help": (
            "RMSE {rmse} على مدى {predictions:,} منتج-يوم."
        ),
        "forecast.eval_baselines": (
            "للمقارنة — خطوط أساس بسيطة على بيانات التحقق نفسها: "
            "{baselines}. كان على النموذج أن يتفوق عليها ليُختار "
            "(DEC-027) — وقد فعل."
        ),
        "forecast.eval_model_caption": (
            "النموذج: {name} إصدار {version}، دُرّب في {trained_at}. "
            "التوقعات تقديرات — قد يختلف الطلب الفعلي (prediction-logic §11)."
        ),
        "forecast.no_link_info": (
            "'{name}' ليس مرتبطًا بعنصر بيانات بعد. حدد 'عنصر بيانات "
            "مرتبط' في نموذج تعديل المنتج (المخزون ← تعديل منتج) "
            "لتمكين التنبؤ (DEC-060)."
        ),
        "forecast.linked_label": "عنصر بيانات مرتبط",
        "forecast.artifact_warning": (
            "ملف نموذج التنبؤ غير متوفر — شغّل "
            "``scripts/train_model.py`` أولًا."
        ),
        "forecast.error_not_available": "التنبؤ غير متاح: {error}",
        "forecast.error_generation_failed": (
            "تعذر توليد التنبؤ: {error}"
        ),
        "forecast.section_result": "التنبؤ لـ {name} ({sku})",
        "forecast.pill_estimate": "تقديري",
        "forecast.pill_note": (
            "هذه تقديرات للطلب — قد يختلف الطلب الفعلي."
        ),
        "forecast.method_caption": "الطريقة: {method}",
        "forecast.metric_total": "إجمالي الطلب ({days} أيام)",
        "forecast.metric_avg_per_day": "المتوسط يوميًا",
        "forecast.metric_dataset_item": "عنصر البيانات",
        "forecast.column_date": "التاريخ",
        "forecast.column_predicted": "الطلب المتوقع",
        "forecast.rounding_caption": (
            "تُقرَّب التنبؤات الخام للعرض فقط؛ وتستخدم معادلات إعادة "
            "التخزين قاعدة الطلب المعتمدة الخاصة بها (DEC-059)."
        ),
        # Data Import page (TASK-023/024/025).
        "imports.title": "استيراد البيانات",
        "imports.description": (
            "استيراد مبيعات تاريخية من CSV للتنبؤ (التنسيق: date، "
            "store، item، sales). تُفلتر الصفوف على المتجر 1 وفق قرار "
            "المتجر الواحد. الاستيراد لا يغير المخزون الحالي أبدًا — "
            "بل يغذي التحليل والتنبؤ فقط."
        ),
        "imports.uploader_label": "ملف CSV للمبيعات التاريخية *",
        "imports.empty_title": "لم يُرفع أي ملف بعد",
        "imports.empty_message": (
            "ارفع ملف CSV للتحقق منه ومعاينة السجلات قبل الاستيراد. "
            "لا يُخزَّن أي شيء حتى تؤكد."
        ),
        "imports.error_file": "لا يمكن استيراد الملف: {error}",
        "imports.section_preview": "معاينة",
        "imports.caption_file": (
            "{filename} — {size:,} بايت · بصمة {fingerprint}…"
        ),
        "imports.metric_rows": "صفوف الملف",
        "imports.metric_valid": "صالح للمتجر 1",
        "imports.metric_rejected": "مرفوض (غير صالح)",
        "imports.metric_other_stores": "متاجر أخرى",
        "imports.caption_date_range": (
            "نطاق تواريخ الصفوف المقبولة: {first} ← {last}؛ "
            "{duplicates:,} مكرر داخل الملف."
        ),
        "imports.caption_no_rows": "لا توجد صفوف في نطاق المتجر 1.",
        "imports.warning_nothing": (
            "لا يوجد ما يُستورد: الملف لا يحتوي صفوفًا صالحة للمتجر 1."
        ),
        "imports.sample_caption": "عينة من السجلات المقبولة:",
        "imports.button_import": "استيراد {count:,} سجل",
        "imports.button_import_help": (
            "تُخزَّن الصفوف المتحقق منها في معاملة واحدة. السجلات "
            "التاريخية لا تغير المخزون الحالي أبدًا."
        ),
        "imports.error_rejected": "لم يُستورد أي شيء: {error}",
        "imports.error_failed": (
            "فشل الاستيراد ولم يُخزَّن أي شيء: {error}"
        ),
        "imports.success_imported": (
            "تم استيراد {count:,} سجل تاريخي من '{filename}' "
            "(الدفعة #{batch_id}). لم يتغير المخزون الحالي."
        ),
        "imports.result_success": (
            "اكتمل الاستيراد — الدفعة #{batch_id} ({created_at})."
        ),
        "imports.result_metric_stored": "مقبول ومخزن",
        "imports.result_metric_duplicates": "مكررات تم تخطيها",
        "imports.result_date_note": (
            " · تمتد الصفوف المقبولة من {first} إلى {last}"
        ),
        "imports.result_caption": (
            "استيراد بيانات تاريخية، المتجر {store} · الملف "
            "'{filename}' ({rows:,} صفوف معالجة){date_note}. لم يتغير "
            "المخزون الحالي."
        ),
        "imports.result_reupload_info": (
            "لاستيراد بيانات أخرى، ارفع ملف CSV مختلف. إعادة رفع هذا "
            "الملف نفسه تُرفض عبر بصمته (DEC-053)."
        ),
        "imports.history_title": "الاستيرادات السابقة",
        "imports.history_error": "تعذرت قراءة سجل الاستيراد: {error}",
        "imports.history_caption": (
            "{records:,} سجل تاريخي مخزن إجمالًا عبر {count} عمليات "
            "استيراد."
        ),
        "imports.history_empty": "لا توجد عمليات استيراد مسجلة بعد.",
        "imports.column_batch": "الدفعة",
        "imports.column_file": "الملف",
        "imports.column_imported": "المستورد",
        "imports.column_duplicates": "مكررات تم تخطيها",
        "imports.column_rejected": "مرفوض",
        "imports.column_other_stores": "متاجر أخرى",
        "imports.column_date_range": "نطاق التواريخ",
        "imports.column_when": "الوقت (UTC)",
        "imports.expander_rejected": "صفوف مرفوضة",
        "imports.expander_duplicates": "مكررات داخل الملف",
        "imports.shown_suffix": "({count} معروض)",
        "imports.truncated_caption": (
            "عرض الأمثلة الأولى فقط — راجع الإجماليات في المقاييس "
            "بالأعلى."
        ),
        "imports.row_line": "- صف {number}: {reason}",
    },
}
