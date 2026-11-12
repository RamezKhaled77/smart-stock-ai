"""SmartStock AI — Streamlit entry point.

Startup and navigation only. All product, inventory, sales, forecasting,
and recommendation behavior lives in services/domain/ML layers (see
docs/02-architecture/system-architecture.md).

Reliable development command (from the repository root):

    streamlit run app.py
"""

import sys
from pathlib import Path

# Make the src-layout package importable for plain `streamlit run app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st

from smartstock.pages.analytics import render as analytics_render
from smartstock.pages.dashboard import render as dashboard_render
from smartstock.pages.forecast import render as forecast_render
from smartstock.pages.imports import render as imports_render
from smartstock.pages.products import render as products_render
from smartstock.pages.restock import render as restock_render
from smartstock.pages.sales import render as sales_render

APP_ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="SmartStock AI",
    # Streamlit accepts a path to an image as the browser-tab icon; the
    # SVG brand mark avoids an emoji favicon.
    page_icon=str(APP_ROOT / "assets" / "favicon.svg"),
    layout="wide",
)


def dashboard() -> None:
    """Placeholder retained for compatibility; the real page lives in
    ``smartstock.pages.dashboard``."""
    dashboard_render()


page = st.navigation(
    {
        "Overview": [
            st.Page(
                dashboard,
                title="Dashboard",
                icon=":material/home:",
                default=True,
            ),
        ],
        "Inventory": [
            st.Page(
                products_render,
                title="Products & Inventory",
                icon=":material/inventory_2:",
                url_path="products-and-inventory",
            ),
            st.Page(
                restock_render,
                title="Restocking Recommendations",
                icon=":material/package_2:",
                url_path="restocking-recommendations",
            ),
        ],
        "Sales": [
            st.Page(
                sales_render,
                title="Sales Management",
                icon=":material/receipt_long:",
                url_path="sales-management",
            ),
            st.Page(
                analytics_render,
                title="Sales Analytics",
                icon=":material/insights:",
                url_path="sales-analytics",
            ),
        ],
        "Forecasting": [
            st.Page(
                forecast_render,
                title="Demand Forecast",
                icon=":material/query_stats:",
                url_path="demand-forecast",
            ),
        ],
        "Data": [
            st.Page(
                imports_render,
                title="Data Import",
                icon=":material/upload_file:",
                url_path="data-import",
            ),
        ],
    }
)
page.run()
