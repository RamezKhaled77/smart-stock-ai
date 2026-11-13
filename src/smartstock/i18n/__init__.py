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
    },
}
