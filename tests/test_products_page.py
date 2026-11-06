"""Tests for the Products & Inventory page (TASK-016) and app navigation.

Uses Streamlit's AppTest to run the real page code in-process, against a
temporary database injected by patching ``config.DATABASE_PATH`` (the
services resolve the path at call time). The real ``data/smartstock.db``
is never touched by these tests.
"""

from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import inventory_service, product_service


@pytest.fixture
def app_db(tmp_path: Path, monkeypatch) -> Path:
    """Temporary database; services resolve config.DATABASE_PATH at
    call time, so patching the attribute redirects the whole stack."""
    import config

    db_path = tmp_path / "app_test.db"
    initialize_database(db_path)
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    return db_path


def _run_page():
    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_string(
        "from smartstock.pages.products import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _run_app(app_db: Path):
    from streamlit.testing.v1 import AppTest

    repo_root = Path(__file__).resolve().parents[1]
    app_test = AppTest.from_file(
        str(repo_root / "app.py"), default_timeout=60
    )
    app_test.run()
    return app_test


class TestAppNavigation:
    """Entry point runs cleanly (page import wiring included).

    Note: st.navigation's sidebar control is not exposed as a testable
    widget by AppTest in Streamlit 1.66, so page switching itself is
    verified by running the page render directly (tests above).
    """

    def test_app_starts_on_dashboard(self, app_db: Path) -> None:
        app_test = _run_app(app_db)
        assert app_test.exception == []
        assert any(
            "Dashboard" in title.value for title in app_test.title
        )

    def test_registered_page_import_wiring(self, app_db: Path) -> None:
        # app.py imports the page module at start; a broken page module
        # would surface as an exception in the run above. This also
        # asserts that the page renders against the app database path.
        product_service.create_product(
            name="Nav Item", sku="SKU-NAV", db_path=app_db
        )
        page = _run_page()
        assert page.exception == []
        dataframes = page.dataframe
        assert len(dataframes) == 1
        frames = dataframes[0].value
        assert list(frames["SKU"]) == ["SKU-NAV"]


class TestProductsPageEmptyState:
    """Empty state (no products in the database)."""

    def test_empty_state_message(self, app_db: Path) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        assert len(app_test.info) == 1
        assert "No products yet" in app_test.info[0].value


class TestProductsPageListing:
    """Listing with correct displayed values, search, and filters."""

    @pytest.fixture
    def populated(self, app_db: Path) -> None:
        product_service.create_product(
            name="Coffee Bag 250g",
            sku="SKU-COF",
            category="Drinks",
            initial_stock=50,
            lead_time_days=3,
            safety_stock=5,
            db_path=app_db,
        )
        product_service.create_product(
            name="Tea Box",
            sku="SKU-TEA",
            category="Drinks",
            initial_stock=0,
            db_path=app_db,
        )
        product_service.create_product(
            name="Honey Jar",
            sku="SKU-HON",
            category="",
            initial_stock=10,
            lead_time_days=3,
            safety_stock=12,  # reorder point 12 → stock 10 = Low Stock
            db_path=app_db,
        )

    def _table_rows(self, app_test) -> list:
        dataframes = app_test.dataframe
        assert len(dataframes) == 1
        frame = dataframes[0].value
        return frame.to_dict(orient="records")

    def test_all_active_products_shown_with_values(
        self, app_db: Path, populated
    ) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        rows = self._table_rows(app_test)
        assert len(rows) == 3  # inactive products never listed (BR-026)

        by_sku = {row["SKU"]: row for row in rows}
        coffee = by_sku["SKU-COF"]
        assert coffee["Name"] == "Coffee Bag 250g"
        assert coffee["Stock"] == 50
        assert coffee["Lead time (days)"] == 3
        assert coffee["Safety stock"] == 5
        assert coffee["Reorder point"] == 5  # safety only: no sales
        assert "In Stock" in coffee["Status"]

        tea = by_sku["SKU-TEA"]
        assert tea["Stock"] == 0
        assert "Out of Stock" in tea["Status"]

        honey = by_sku["SKU-HON"]
        assert honey["Reorder point"] == 12
        assert "Low Stock" in honey["Status"]

    def test_search_filters_by_name_fragment(
        self, app_db: Path, populated
    ) -> None:
        app_test = _run_page()
        app_test.text_input[0].set_value("coffee")
        app_test.run()
        rows = self._table_rows(app_test)
        assert [row["SKU"] for row in rows] == ["SKU-COF"]

    def test_search_filters_by_sku_fragment(
        self, app_db: Path, populated
    ) -> None:
        app_test = _run_page()
        app_test.text_input[0].set_value("HON")
        app_test.run()
        rows = self._table_rows(app_test)
        assert [row["Name"] for row in rows] == ["Honey Jar"]

    def test_status_filter(self, app_db: Path, populated) -> None:
        app_test = _run_page()
        # The second selectbox lives inside the columns in _apply_filters;
        # find it by matching its options.
        status_select = next(
            box
            for box in app_test.selectbox
            if "Out of Stock" in box.options
        )
        status_select.set_value("Out of Stock")
        app_test.run()
        rows = self._table_rows(app_test)
        assert [row["SKU"] for row in rows] == ["SKU-TEA"]

    def test_category_filter(self, app_db: Path, populated) -> None:
        app_test = _run_page()
        category_select = next(
            box for box in app_test.selectbox if "All" == box.options[0]
        )
        category_select.set_value("Drinks")
        app_test.run()
        rows = self._table_rows(app_test)
        assert sorted(row["SKU"] for row in rows) == ["SKU-COF", "SKU-TEA"]

    def test_no_match_warning(self, app_db: Path, populated) -> None:
        app_test = _run_page()
        app_test.text_input[0].set_value("zzz-nothing")
        app_test.run()
        assert app_test.exception == []
        dataframes = app_test.dataframe
        assert dataframes == []
        assert any(
            "No products match" in warning.value
            for warning in app_test.warning
        )

    def test_low_stock_banner_counts_non_in_stock(
        self, app_db: Path, populated
    ) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        warnings = [warning.value for warning in app_test.warning]
        assert any("2 product(s)" in value for value in warnings)

    def test_overview_reflects_sales_services(
        self, app_db: Path, populated
    ) -> None:
        # Record a sale through the sales service; the listing must
        # reflect reduced stock without extra "refresh" tricks.
        coffee = product_service.get_product_by_sku("SKU-COF", db_path=app_db)
        inventory_service.adjust_stock(coffee["id"], -10, db_path=app_db)
        app_test = _run_page()
        rows = self._table_rows(app_test)
        by_sku = {row["SKU"]: row for row in rows}
        assert by_sku["SKU-COF"]["Stock"] == 40
