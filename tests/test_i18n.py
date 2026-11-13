"""Tests for the bilingual interface layer (F-020, DEC-066).

Unit checks run the plain functions; the Arabic rendering check uses
Streamlit AppTest with the language pre-set in session state, so the
approved English-pinned page tests are never affected.
"""

import pytest

# Streamlit 1.66's own chart internals trip a pandas-4 deprecation
# (upstream issue, not project code); the suite stays warning-free.
# Same filter as tests/test_dashboard_page.py, which renders the same
# page.
pytestmark = pytest.mark.filterwarnings(
    "ignore:The inplace keyword:Warning"
)


class TestStringTable:
    def test_every_key_exists_in_both_languages(self) -> None:
        from smartstock.i18n import DEFAULT_LANGUAGE, STRINGS

        en_keys = set(STRINGS[DEFAULT_LANGUAGE])
        for code in STRINGS:
            missing_in_this_language = en_keys - set(STRINGS[code])
            extra_keys = set(STRINGS[code]) - en_keys
            assert not missing_in_this_language, (
                f"{code} lacks keys: {sorted(missing_in_this_language)}"
            )
            assert not extra_keys, (
                f"{code} has unknown keys: {sorted(extra_keys)}"
            )

    def test_no_placeholder_mismatches_between_languages(self) -> None:
        import re

        from smartstock.i18n import DEFAULT_LANGUAGE, STRINGS

        def placeholders(text: str) -> set:
            return set(re.findall(r"\{(\w+)\}", text))

        for key, en_text in STRINGS[DEFAULT_LANGUAGE].items():
            for code in STRINGS:
                assert placeholders(STRINGS[code][key]) == placeholders(
                    en_text
                ), f"placeholder drift in {code}.{key}"

    def test_t_translates_explicit_language(self) -> None:
        from smartstock.i18n import t

        assert t("nav.dashboard", lang="en") == "Dashboard"
        assert t("nav.dashboard", lang="ar") != "Dashboard"
        assert t("nav.dashboard", lang="ar") == "لوحة التحكم"

    def test_t_falls_back_to_english_then_key(self) -> None:
        from smartstock.i18n import STRINGS, t

        # A key only English knows falls back to the English string in
        # an Arabic session (the parity test keeps this hypothetical —
        # real keys exist in both).
        STRINGS["ar"].pop("nav.dashboard")
        try:
            assert t("nav.dashboard", lang="ar") == "Dashboard"
        finally:
            STRINGS["ar"]["nav.dashboard"] = "لوحة التحكم"
        assert t("no_such_key", lang="en") == "no_such_key"

    def test_t_fills_placeholders(self) -> None:
        from smartstock.i18n import t

        text = t(
            "dashboard.readiness_caption", lang="en", linked=1, total=2
        )
        assert "1 of 2" in text

    def test_set_language_rejects_unknown_codes(self) -> None:
        from smartstock.i18n import set_language

        with pytest.raises(ValueError):
            set_language("fr")


class TestArabicRendering:
    def test_dashboard_renders_in_arabic_when_language_is_ar(
        self,
    ) -> None:
        # Session state starts at English (the approved page tests pin
        # English labels); here the language is switched explicitly and
        # the page must come back fully Arabic.
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.dashboard import render\nrender()",
            default_timeout=30,
        )
        app_test.session_state["language"] = "ar"
        app_test.run()
        assert not app_test.exception
        labels = [metric.label for metric in app_test.metric]
        assert "المنتجات النشطة" in labels
        assert "Active products" not in labels

    def test_rtl_direction_css_applied_for_arabic(self) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.dashboard import render\nrender()",
            default_timeout=30,
        )
        app_test.session_state["language"] = "ar"
        app_test.run()
        styles = [
            value for value in
            (m.value for m in app_test.markdown)
            if "direction: rtl" in value
        ]
        assert styles, "Arabic session must emit the RTL style block"
        # The block must target Streamlit's own heading containers
        # explicitly (bare html inheritance left headings LTR in the
        # owner's visual review), right-align text, and keep
        # numeric inputs and charts LTR.
        block = "\n".join(styles)
        assert 'stHeading' in block
        assert "text-align: right" in block
        assert "direction: ltr" in block  # inputs/charts stay LTR

    def test_english_session_emits_no_rtl_block(self) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_string(
            "from smartstock.pages.dashboard import render\nrender()",
            default_timeout=30,
        )
        app_test.run()
        rtl = [
            m.value for m in app_test.markdown if "direction: rtl" in m.value
        ]
        assert rtl == []
