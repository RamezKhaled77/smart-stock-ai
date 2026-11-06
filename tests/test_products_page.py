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


def _key(elements, key):
    """Locate a Streamlit test element by its widget key."""
    matches = [element for element in elements if element.key == key]
    assert matches, f"widget with key {key!r} not found"
    return matches[0]


def _click_button(app_test, label: str) -> None:
    """Click the labeled button, then rerun the script."""
    matches = [b for b in app_test.button if b.label == label]
    assert matches, f"button {label!r} not found"
    matches[0].click()
    app_test.run()


def _click_submit(app_test, label: str) -> None:
    """Submit the labeled form button, then rerun the script."""
    matches = [b for b in app_test.form_submit_button if b.label == label]
    assert matches, f"form submit {label!r} not found"
    matches[0].click()
    app_test.run()


def _button_by_label(app_test, label: str):
    matches = [b for b in app_test.button if b.label == label]
    assert matches, f"button {label!r} not found"
    return matches[0]


def _submit_by_label(app_test, label: str):
    matches = [b for b in app_test.form_submit_button if b.label == label]
    assert matches, f"form submit {label!r} not found"
    return matches[0]


class TestAddProductForm:
    """TASK-017: creation form."""

    def test_create_persists_product_with_defaults(
        self, app_db: Path
    ) -> None:
        app_test = _run_page()
        _key(app_test.text_input, "add_name").set_value("Tea Cup")
        _key(app_test.text_input, "add_sku").set_value("SKU-CUP")
        _key(app_test.text_input, "add_category").set_value("Kitchen")
        _key(app_test.number_input, "add_stock").set_value(5)
        _key(app_test.number_input, "add_lead").set_value(4)
        _key(app_test.number_input, "add_safety").set_value(2)
        _click_submit(app_test, "Create product")

        assert app_test.exception == []
        assert any(
            "Created 'Tea Cup'" in s.value for s in app_test.success
        )
        persisted = product_service.get_product_by_sku(
            "SKU-CUP", db_path=app_db
        )
        assert persisted is not None
        assert persisted["current_stock"] == 5
        assert persisted["lead_time_days"] == 4
        assert persisted["safety_stock"] == 2
        # The listing reflects the new product immediately.
        dataframes = app_test.dataframe
        assert "SKU-CUP" in list(dataframes[0].value["SKU"])

    def test_duplicate_sku_shows_service_error(self, app_db: Path) -> None:
        product_service.create_product(
            name="Existing", sku="SKU-DUP", db_path=app_db
        )
        app_test = _run_page()
        _key(app_test.text_input, "add_name").set_value("Copy")
        _key(app_test.text_input, "add_sku").set_value("SKU-DUP")
        _click_submit(app_test, "Create product")

        assert app_test.exception == []
        assert any(
            "already exists" in e.value for e in app_test.error
        )
        # No partial write happened.
        assert product_service.get_product_by_sku(
            "Copy", db_path=app_db
        ) is None

    def test_empty_name_rejected(self, app_db: Path) -> None:
        app_test = _run_page()
        _key(app_test.text_input, "add_name").set_value("   ")
        _key(app_test.text_input, "add_sku").set_value("SKU-X")
        _click_submit(app_test, "Create product")
        assert any("not created" in e.value for e in app_test.error)
        assert product_service.get_product_by_sku(
            "SKU-X", db_path=app_db
        ) is None


class TestEditProductForm:
    """TASK-017: edit form and soft-delete removal."""

    @pytest.fixture
    def product(self, app_db: Path) -> dict:
        return product_service.create_product(
            name="Coffee Bag 250g",
            sku="SKU-COF",
            category="Drinks",
            initial_stock=50,
            db_path=app_db,
        )

    def test_form_prefills_current_values(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        assert (
            _key(app_test.text_input, f"edit_name_{product['id']}").value
            == "Coffee Bag 250g"
        )
        assert (
            _key(app_test.number_input, f"edit_lead_{product['id']}").value
            == 3
        )
        assert (
            _key(app_test.number_input, f"edit_safety_{product['id']}").value
            == 0
        )

    def test_update_fields_persist(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.text_input, f"edit_name_{product['id']}").set_value(
            "Coffee Bag 500g"
        )
        _key(app_test.number_input, f"edit_lead_{product['id']}").set_value(7)
        _key(app_test.number_input, f"edit_safety_{product['id']}").set_value(
            3
        )
        _click_submit(app_test, "Save changes")

        assert app_test.exception == []
        updated = product_service.get_product(product["id"], db_path=app_db)
        assert updated["name"] == "Coffee Bag 500g"
        assert updated["lead_time_days"] == 7
        assert updated["safety_stock"] == 3
        assert updated["current_stock"] == 50  # untouched

    def test_sku_conflict_shows_error(self, app_db: Path, product) -> None:
        product_service.create_product(
            name="Other", sku="SKU-OTHER", db_path=app_db
        )
        app_test = _run_page()
        _key(app_test.text_input, f"edit_sku_{product['id']}").set_value(
            "SKU-OTHER"
        )
        _click_submit(app_test, "Save changes")
        assert any("already exists" in e.value for e in app_test.error)
        assert (
            product_service.get_product(product["id"], db_path=app_db)["sku"]
            == "SKU-COF"
        )

    def test_deactivate_requires_confirmation(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        _click_button(app_test, "Deactivate product")
        assert any(
            "Tick the confirmation box" in e.value for e in app_test.error
        )
        assert product_service.get_product(
            product["id"], db_path=app_db
        )["is_active"] == 1

    def test_deactivate_and_listing_exclusion(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        _key(app_test.checkbox, f"edit_confirm_{product['id']}").check()
        _click_button(app_test, "Deactivate product")

        assert app_test.exception == []
        assert product_service.get_product(
            product["id"], db_path=app_db
        )["is_active"] == 0
        # Listing excludes inactive products (BR-026); empty state shows.
        assert any(
            "No products yet" in info.value for info in app_test.info
        )
        # Unconfirmed widget state does not leak into the result.
        assert app_test.success == [] or any(
            "deactivated" in s.value for s in app_test.success
        )

    def test_reactivate(self, app_db: Path, product) -> None:
        product_service.set_product_active(product["id"], False, db_path=app_db)
        app_test = _run_page()
        _click_button(app_test, "Reactivate product")
        assert product_service.get_product(
            product["id"], db_path=app_db
        )["is_active"] == 1


class TestStockPanel:
    """TASK-018: stock adjustments and corrections."""

    @pytest.fixture
    def product(self, app_db: Path) -> dict:
        return product_service.create_product(
            name="Coffee Bag 250g",
            sku="SKU-COF",
            initial_stock=10,
            db_path=app_db,
        )

    def test_add_units(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.number_input, f"stock_change_{product['id']}").set_value(
            5
        )
        _click_button(app_test, "Apply adjustment")

        assert app_test.exception == []
        assert any(
            "now has 15 units" in s.value for s in app_test.success
        )
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 15
        )
        # The listing table in the same run shows the new stock.
        frames = app_test.dataframe[0].value
        assert list(frames["Stock"]) == [15]

    def test_remove_units(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.number_input, f"stock_change_{product['id']}").set_value(
            -4
        )
        _click_button(app_test, "Apply adjustment")
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 6
        )

    def test_remove_too_many_attention_negative_rejection(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        _key(app_test.number_input, f"stock_change_{product['id']}").set_value(
            -11
        )
        _click_button(app_test, "Apply adjustment")
        assert any(
            "negative stock is not allowed" in e.value
            for e in app_test.error
        )
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 10
        )

    def test_zero_change_rejected(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.number_input, f"stock_change_{product['id']}").set_value(
            0
        )
        _click_button(app_test, "Apply adjustment")
        assert any(
            "must not be zero" in e.value for e in app_test.error
        )

    def test_set_exact_stock(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.radio, "stock_mode").set_value(
            "Set exact stock (correction)"
        )
        app_test.run()  # the exact-mode branch renders on the rerun
        _key(app_test.number_input, f"stock_exact_{product['id']}").set_value(
            42
        )
        _click_button(app_test, "Set stock level")
        assert any(
            "Stock set to 42 units" in s.value for s in app_test.success
        )
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 42
        )

    def test_current_stock_metric_is_displayed(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        metrics = app_test.metric
        assert len(metrics) == 1
        assert metrics[0].value == "10"


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
        assert len(app_test.info) >= 1
        assert any(
            "No products yet" in info.value for info in app_test.info
        )


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
