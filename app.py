"""SmartStock AI — Streamlit entry point.

Startup and navigation only. All product, inventory, sales, forecasting,
and recommendation behavior lives in services/domain/ML layers that will
be connected in later phases (see docs/02-architecture/system-architecture.md).
"""

import streamlit as st

st.set_page_config(
    page_title="SmartStock AI",
    page_icon="📦",
    layout="wide",
)

st.title("📦 SmartStock AI")
st.markdown(
    "Smart inventory and demand forecasting for small businesses. "
    "The application pages (Dashboard, Products & Inventory, Sales, "
    "Analytics, Forecasting, CSV Import) will be added in the next "
    "development phases."
)

st.info(
    "Phase 0 scaffold: environment, project structure, and version control "
    "are in place. Documentation lives in `docs/`."
)
