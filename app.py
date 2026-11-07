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

from smartstock.pages.imports import render as imports_render
from smartstock.pages.products import render as products_render
from smartstock.pages.sales import render as sales_render

st.set_page_config(
    page_title="SmartStock AI",
    page_icon="📦",
    layout="wide",
)


def dashboard() -> None:
    """Dashboard placeholder (built in a later phase)."""
    st.title("🏠 Dashboard")
    st.info(
        "The dashboard (inventory summary, low-stock review, sales "
        "trends) will be built in a later development phase. Use "
        "Products & Inventory in the navigation to manage stock today."
    )


page = st.navigation(
    {
        "Overview": [
            st.Page(dashboard, title="Dashboard", icon="🏠", default=True),
        ],
        "Inventory": [
            st.Page(
                products_render,
                title="Products & Inventory",
                icon="🏷️",
                url_path="products-and-inventory",
            ),
        ],
        "Sales": [
            st.Page(
                sales_render,
                title="Sales Management",
                icon="🧾",
                url_path="sales-management",
            ),
        ],
        "Data": [
            st.Page(
                imports_render,
                title="Data Import",
                icon="📥",
                url_path="data-import",
            ),
        ],
    }
)
page.run()
