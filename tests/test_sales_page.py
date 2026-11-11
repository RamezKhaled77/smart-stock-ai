"""Tests for the Sales Management page (TASK-020, TASK-021).

Runs the real page with Streamlit AppTest against a temporary database
(the services resolve ``config.DATABASE_PATH`` at call time). The real
``data/smartstock.db`` is never touched.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest

from smartstock.database.initialization import initialize_database
from smartstock.services import (
    inventory_service,
    product_service,
    sales_service,
)


@pytest.fixture
def app_db(tmp_path: Path, monkeypatch) -> Path:
    import config

    db_path = tmp_path / "sales_app_test.db"
    initialize_database(db_path)
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    return db_path


@pytest.fixture
def product(app_db: Path) -> dict:
    return product_service.create_product(
        name="Coffee Bag 250g",
        sku="SKU-COF",
        initial_stock=20,
        db_path=app_db,
    )


def _key(elements, key):
    matches = [element for element in elements if element.key == key]
    assert matches, f"widget with key {key!r} not found"
    return matches[0]


def _utc_today() -> date:
    """Today as the services validate it (UTC, DEC-051)."""
    return date.fromisoformat(
        __import__("smartstock.utils.dates", fromlist=["utc_today_iso"])
        .utc_today_iso()
    )


def _future_date_in_widget_window() -> date:
    """A near-future date the date widget still accepts.

    Streamlit's date_input clamps beyond about +10 years; a near-future
    date ensures the service-layer rejection (DEC-051) is what fires.
    """
    return _utc_today() + timedelta(days=3)


def _button_by_label(app_test, label: str):
    matches = [button for button in app_test.button if button.label == label]
    assert matches, f"button {label!r} not found"
    return matches[0]


def _click_button(app_test, label: str) -> None:
    _button_by_label(app_test, label).click()
    app_test.run()


def _run_page():
    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_string(
        "from smartstock.pages.sales import render\nrender()",
        default_timeout=30,
    )
    app_test.run()
    return app_test


def _table_rows(app_test) -> list:
    dataframes = app_test.dataframe
    assert len(dataframes) == 1
    return dataframes[0].value.to_dict(orient="records")


class TestRecordSaleForm:
    """TASK-020: manual sales entry."""

    def test_no_products_shows_empty_state(self, app_db: Path) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        assert any(
            "No products yet" in info.value for info in app_test.info
        )

    def test_stock_metric_displayed(self, app_db: Path, product) -> None:
        app_test = _run_page()
        metrics = app_test.metric
        assert len(metrics) == 1
        assert metrics[0].value == "20"

    def test_valid_sale_persists_and_reduces_stock(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        _key(app_test.number_input, "sale_quantity").set_value(3)
        _click_button(app_test, "Record sale")

        assert app_test.exception == []
        assert any(
            "Recorded sale of 3 unit(s)" in s.value
            for s in app_test.success
        )
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 17
        )
        rows = _table_rows(app_test)
        assert len(rows) == 1
        assert rows[0]["Quantity"] == 3
        assert "SKU-COF" in rows[0]["Product"]

    def test_insufficient_stock_rejected_with_clear_message(
        self, app_db: Path, product
    ) -> None:
        app_test = _run_page()
        _key(app_test.number_input, "sale_quantity").set_value(25)
        _click_button(app_test, "Record sale")

        assert app_test.exception == []
        errors = [error.value for error in app_test.error]
        assert any("requested 25" in value for value in errors)
        assert any("only 20 available" in value for value in errors)
        # DEC-035 atomicity at the UI level: nothing recorded.
        assert sales_service.list_sales(product["id"], db_path=app_db) == []
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 20
        )
        assert app_test.success == []

    def test_future_date_rejected(self, app_db: Path, product) -> None:
        # Within the widget's window (+10 years) so the service-layer
        # DEC-051 rejection is what fires.
        future = _future_date_in_widget_window()
        app_test = _run_page()
        _key(app_test.date_input, "sale_date").set_value(future)
        _click_button(app_test, "Record sale")

        assert any("future" in error.value for error in app_test.error)
        assert sales_service.list_sales(product["id"], db_path=app_db) == []
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 20
        )

    def test_inactive_product_not_sellable(
        self, app_db: Path, product
    ) -> None:
        product_service.set_product_active(
            product["id"], False, db_path=app_db
        )
        app_test = _run_page()
        # The only product is inactive: no product selector renders in
        # the record tab (DEC-050), with a helpful message instead.
        assert any(
            "No products yet" in info.value for info in app_test.info
        )
        assert [e for e in app_test.selectbox if e.key == "sale_product"] == []

    def test_backdated_sale_allowed(self, app_db: Path, product) -> None:
        app_test = _run_page()
        _key(app_test.number_input, "sale_quantity").set_value(2)
        _key(app_test.date_input, "sale_date").set_value(
            date(2026, 10, 15)
        )
        _click_button(app_test, "Record sale")

        assert any(
            "on 2026-10-15" in s.value for s in app_test.success
        )
        sales = sales_service.list_sales(product["id"], db_path=app_db)
        assert [sale["sale_date"] for sale in sales] == ["2026-10-15"]
        assert (
            inventory_service.get_current_stock(
                product["id"], db_path=app_db
            )
            == 18
        )


class TestSalesHistory:
    """TASK-021: history display and filters."""

    def test_database_failure_shows_friendly_error(
        self, app_db: Path, monkeypatch
    ) -> None:
        # TASK-045: a read failure degrades to a message, not a crash.
        from smartstock.database.connection import DatabaseError

        def broken(**kwargs):
            raise DatabaseError("disk unavailable")

        monkeypatch.setattr(sales_service, "list_sales", broken)
        product_service.create_product(
            name="Coffee", sku="SKU-C", db_path=app_db
        )
        app_test = _run_page()
        assert app_test.exception == []
        assert any(
            "Could not load sales history" in e.value
            for e in app_test.error
        )

    @pytest.fixture
    def two_products_with_sales(self, app_db: Path, product) -> dict:
        other = product_service.create_product(
            name="Tea Box", sku="SKU-TEA", initial_stock=5, db_path=app_db
        )
        sales_service.record_sale(
            product["id"], 3, "2026-11-01", db_path=app_db
        )
        sales_service.record_sale(
            product["id"], 2, "2026-11-03", db_path=app_db
        )
        sales_service.record_sale(
            other["id"], 5, "2026-10-20", db_path=app_db
        )
        return {"coffee": product, "tea": other}

    def test_all_time_history_by_default(
        self, app_db: Path, two_products_with_sales
    ) -> None:
        app_test = _run_page()
        assert app_test.exception == []
        rows = _table_rows(app_test)
        assert len(rows) == 3
        quantities = {row["Quantity"] for row in rows}
        assert quantities == {3, 2, 5}
        labels = {row["Product"] for row in rows}
        assert any("Coffee Bag 250g" in label for label in labels)
        assert any("Tea Box" in label for label in labels)
        # Totals caption present.
        assert any("3 sale(s), 10 unit(s)" in c.value for c in app_test.caption)

    def test_no_sales_empty_state(self, app_db: Path, product) -> None:
        app_test = _run_page()
        assert any(
            "No sales recorded yet" in info.value for info in app_test.info
        )

    def test_product_filter(self, app_db: Path, two_products_with_sales) -> None:
        app_test = _run_page()
        _key(app_test.selectbox, "history_product").set_value("SKU-COF")
        app_test.run()
        rows = _table_rows(app_test)
        assert len(rows) == 2
        assert {row["Quantity"] for row in rows} == {3, 2}

    def test_date_window_filter(
        self, app_db: Path, two_products_with_sales
    ) -> None:
        app_test = _run_page()
        _key(app_test.checkbox, "history_all_time").uncheck()
        app_test.run()  # date widgets enable on the rerun
        _key(app_test.date_input, "history_start").set_value(
            date(2026, 11, 1)
        )
        _key(app_test.date_input, "history_end").set_value(
            date(2026, 11, 30)
        )
        app_test.run()
        rows = _table_rows(app_test)
        assert len(rows) == 2  # the October tea sale is excluded
        assert {row["Quantity"] for row in rows} == {3, 2}

    def test_filters_matching_nothing(
        self, app_db: Path, two_products_with_sales
    ) -> None:
        app_test = _run_page()
        _key(app_test.checkbox, "history_all_time").uncheck()
        app_test.run()
        _key(app_test.date_input, "history_start").set_value(
            date(2025, 1, 1)
        )
        _key(app_test.date_input, "history_end").set_value(
            date(2025, 1, 2)
        )
        app_test.run()
        assert any(
            "No sales match the current filters" in info.value
            for info in app_test.info
        )
        assert app_test.exception == []

    def test_inactive_product_stays_reviewable(
        self, app_db: Path, two_products_with_sales
    ) -> None:
        # Deactivate with sales history: the history filter still lists
        # the product (DEC-048), the record tab does not (DEC-050).
        product_service.set_product_active(
            two_products_with_sales["tea"]["id"], False, db_path=app_db
        )
        app_test = _run_page()
        history_options = _key(
            app_test.selectbox, "history_product"
        ).options
        # The selectbox exposes formatted labels; the inactive product
        # must still be selectable (DEC-048).
        assert any("SKU-TEA" in option for option in history_options)
        rows = _table_rows(app_test)
        assert len(rows) == 3

        # Re-selecting the deactivated product in the filter keeps its
        # sales visible.
        _key(app_test.selectbox, "history_product").set_value("SKU-TEA")
        app_test.run()
        rows = _table_rows(app_test)
        assert len(rows) == 1
        assert rows[0]["Quantity"] == 5
