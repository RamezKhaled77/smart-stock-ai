"""Shared UI helpers for Streamlit pages.

Keeps page code free of duplicated interaction patterns and gives every
page one consistent presentation layer:

- :func:`page_header` — standard title with a Material icon and a
  one-line description.
- :func:`section` — standard section heading with a Material icon.
- :func:`empty_state` — standard empty state that explains why an area
  is empty and what to do next.
- :func:`hero_stat` — the one most important number on a page, extra
  large (DEC-065).
- :func:`pill` — small semantic badge (green/orange/red/yellow/blue)
  for statuses and cautions (DEC-065).
- :func:`strong` — an inline emphasized number or value for sentences
  (DEC-065).
- :func:`formula_box` — a monospace panel for formula walk-throughs
  (DEC-065).

Icons come from the Material Symbols (Rounded) font that Streamlit ships
and render through the framework's own ``":material/<icon>:"`` handling
— no emoji and no extra dependency (UI design system, DEC-064).

The native theme engine in ``.streamlit/config.toml`` remains the
foundation (DEC-064). On top of it, :func:`inject_design_system` adds a
small, centrally-managed CSS layer for the pieces the theme engine
cannot express — sizes of heading icons and the semantic utility classes
above (DEC-065). The layer reads the active theme variant (light/dark)
via ``st.context.theme`` so its colors always match ``config.toml``.
All helpers hold no business rules — pages stay responsible for their
own content, and every helper escapes user-provided text before it is
placed into HTML.
"""

import html

import streamlit as st

from smartstock.i18n import apply_direction

# Reused alert icons so every page signals state the same way.
SUCCESS_ICON = ":material/check_circle:"
INFO_ICON = ":material/info:"
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"

STATUS_ICON = {
    "success": SUCCESS_ICON,
    "error": ERROR_ICON,
}

# ---------------------------------------------------------------------------
# Semantic color tokens (DEC-065).
#
# Colors carry meaning, never decoration:
#   green  = healthy / success (In Stock, an action was accepted)
#   red    = danger (Out of Stock, an action was rejected — no data changed)
#   orange = attention (Low Stock, needs reorder, setup step missing)
#   yellow = caution / estimate (forecast values, advisory numbers)
#   blue   = information / neutral guidance
#   gray   = muted secondary context
#
# These mirror the semantic palette in ``.streamlit/config.toml``, which
# stays the source of truth for native widgets; this map exists because
# the injected CSS needs the same values per theme variant.
# ---------------------------------------------------------------------------

_TONE_TOKENS = {
    "light": {
        "ok": "#16a34a", "ok-bg": "#f0fdf4", "ok-text": "#14532d",
        "danger": "#dc2626", "danger-bg": "#fef2f2", "danger-text": "#7f1d1d",
        "warn": "#ea580c", "warn-bg": "#fff7ed", "warn-text": "#7c2d12",
        "caution": "#ca8a04", "caution-bg": "#fefce8",
        "caution-text": "#713f12",
        "brand": "#2563eb", "brand-bg": "#eff6ff", "brand-text": "#1e3a8a",
        "muted": "#64748b", "muted-bg": "#f1f5f9", "muted-text": "#334155",
        "line": "#d3dbe7",
        "text": "#0f172a",
    },
    "dark": {
        "ok": "#4ade80", "ok-bg": "#052e16", "ok-text": "#bbf7d0",
        "danger": "#f87171", "danger-bg": "#450a0a", "danger-text": "#fecaca",
        "warn": "#fb923c", "warn-bg": "#431407", "warn-text": "#fed7aa",
        "caution": "#facc15", "caution-bg": "#422006",
        "caution-text": "#fef08a",
        "brand": "#60a5fa", "brand-bg": "#172554", "brand-text": "#bfdbfe",
        "muted": "#94a3b8", "muted-bg": "#1e293b", "muted-text": "#cbd5e1",
        "line": "#334155",
        "text": "#e2e8f0",
    },
}

# Shared utility classes; ``{tokens}`` is the per-variant ``:root`` block.
_CSS_TEMPLATE = """
:root {{
  --ss-ok: {ok}; --ss-ok-bg: {ok-bg}; --ss-ok-text: {ok-text};
  --ss-danger: {danger}; --ss-danger-bg: {danger-bg};
  --ss-danger-text: {danger-text};
  --ss-warn: {warn}; --ss-warn-bg: {warn-bg}; --ss-warn-text: {warn-text};
  --ss-caution: {caution}; --ss-caution-bg: {caution-bg};
  --ss-caution-text: {caution-text};
  --ss-brand: {brand}; --ss-brand-bg: {brand-bg};
  --ss-brand-text: {brand-text};
  --ss-muted: {muted}; --ss-muted-bg: {muted-bg};
  --ss-muted-text: {muted-text};
  --ss-line: {line}; --ss-text: {text};
  --ss-mono: ui-monospace, "Roboto Mono", "Cascadia Mono", Menlo,
    Consolas, monospace;
}}

/* Hero stat: the single most important number on a page. */
.ss-hero-label {{
  font-size: 0.875rem; font-weight: 600; color: var(--ss-muted);
  margin: 0 0 0.1rem 0;
}}
.ss-hero {{
  font-size: 2.6rem; font-weight: 800; line-height: 1.15;
  letter-spacing: -0.02em; color: var(--ss-brand); margin: 0;
}}
.ss-hero--ok {{ color: var(--ss-ok); }}
.ss-hero--warn {{ color: var(--ss-warn); }}
.ss-hero--danger {{ color: var(--ss-danger); }}
.ss-hero--caution {{ color: var(--ss-caution); }}
.ss-hero--muted {{ color: var(--ss-muted); }}

/* Inline emphasis for numbers and values inside sentences. */
.ss-num {{ font-weight: 700; font-size: 1.05em; }}
.ss-ok {{ color: var(--ss-ok); font-weight: 600; }}
.ss-danger {{ color: var(--ss-danger); font-weight: 600; }}
.ss-warn {{ color: var(--ss-warn); font-weight: 600; }}
.ss-caution {{ color: var(--ss-caution); font-weight: 600; }}
.ss-info {{ color: var(--ss-brand); font-weight: 600; }}

/* Small semantic badges. */
.ss-pill {{
  display: inline-block; padding: 0.15em 0.65em; border-radius: 999px;
  font-size: 0.85em; font-weight: 600; line-height: 1.5;
  background: var(--ss-muted-bg); color: var(--ss-muted-text);
}}
.ss-pill--ok {{ background: var(--ss-ok-bg); color: var(--ss-ok-text); }}
.ss-pill--danger {{
  background: var(--ss-danger-bg); color: var(--ss-danger-text);
}}
.ss-pill--warn {{ background: var(--ss-warn-bg); color: var(--ss-warn-text); }}
.ss-pill--caution {{
  background: var(--ss-caution-bg); color: var(--ss-caution-text);
}}
.ss-pill--brand {{ background: var(--ss-brand-bg); color: var(--ss-brand-text); }}

/* Formula walk-through panel: monospace, quietly boxed. */
.ss-formula {{
  font-family: var(--ss-mono); font-size: 0.9rem; line-height: 1.55;
  background: var(--ss-muted-bg); border: 1px solid var(--ss-line);
  border-radius: 0.5rem; padding: 0.85rem 1rem; color: var(--ss-text);
}}

/* Heading icons: explicit sizes so page titles and section headings
   read as icon + text pairs instead of a single mixed-size line. */
[data-testid="stHeadingIcon"] {{
  font-size: 1.45rem !important;
  width: 1.5rem !important;
  height: 1.5rem !important;
}}
[data-testid="stHeading"]:has(h1) [data-testid="stHeadingIcon"] {{
  font-size: 2.5rem !important;
  width: 2.6rem !important;
  height: 2.6rem !important;
}}
"""

_TONE_CLASS = {
    "brand": "",
    "ok": "--ok",
    "warn": "--warn",
    "danger": "--danger",
    "caution": "--caution",
    "muted": "--muted",
}

_PILL_CLASS = {
    "muted": "",
    "ok": "--ok",
    "warn": "--warn",
    "danger": "--danger",
    "caution": "--caution",
    "brand": "--brand",
}


def _theme_variant() -> str:
    """Return the active theme variant: ``"dark"`` or ``"light"``.

    Theme info can be unavailable in bare test runners and during a
    theme switch, in which case light is used as the safe default.
    """
    try:
        return "dark" if st.context.theme["type"] == "dark" else "light"
    except (KeyError, AttributeError, RuntimeError):
        return "light"


def inject_design_system() -> None:
    """Inject the DEC-065 emphasis CSS once at the top of every page.

    Called from :func:`page_header` so each page render carries exactly
    one style block. The block is re-emitted every run (Streamlit
    elements do not persist between runs) and re-reads the active theme
    variant, so toggling light/dark in the app menu restyles the layer
    immediately.
    """
    tokens = _TONE_TOKENS[_theme_variant()]
    css = _CSS_TEMPLATE.format(**tokens)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    # The Arabic interface flips the app to right-to-left (DEC-066);
    # English sessions emit nothing.
    apply_direction()


def page_header(icon: str, title: str, description: str = "") -> None:
    """Standard page header: icon, title, and a short description."""
    inject_design_system()
    st.title(title, icon=f":material/{icon}:")
    if description:
        st.caption(description)


def section(icon: str, title: str) -> None:
    """Standard section heading with a Material icon."""
    st.subheader(title, icon=f":material/{icon}:")


def empty_state(title: str, message: str, icon: str = "info") -> None:
    """Standard empty state: what is missing and what to do next.

    ``icon`` is a Material icon name (without the ``:material/`` wrapper)
    chosen to fit the situation, e.g. ``"inventory_2"``.
    """
    st.info(f"**{title}**\n\n{message}", icon=f":material/{icon}:")


def hero_stat(value: str, label: str, tone: str = "brand") -> None:
    """Render the page's most important number, extra large (DEC-065).

    ``tone`` picks the semantic color: ``"brand"`` (blue, neutral), or
    a state color — ``"ok"``, ``"warn"``, ``"danger"``, ``"caution"``,
    ``"muted"``. Both ``value`` and ``label`` are escaped, so user data
    such as product names is safe to pass through.
    """
    suffix = _TONE_CLASS.get(tone, "")
    st.markdown(
        f'<p class="ss-hero-label">{html.escape(label)}</p>'
        f'<p class="ss-hero{suffix}">{html.escape(value)}</p>',
        unsafe_allow_html=True,
    )


def pill(text: str, tone: str = "muted") -> str:
    """Return a small semantic badge as an HTML string (DEC-065).

    Embed the result inside a ``st.markdown`` call with
    ``unsafe_allow_html=True``. ``tone``: ``"ok"``, ``"danger"``,
    ``"warn"``, ``"caution"``, ``"brand"``, or ``"muted"``.
    """
    suffix = _PILL_CLASS.get(tone, "")
    class_name = f"ss-pill{suffix}" if suffix else "ss-pill"
    return f'<span class="{class_name}">{html.escape(text)}</span>'


def strong(text: str, tone: str | None = None) -> str:
    """Return an inline emphasized value as an HTML string (DEC-065).

    Optional ``tone`` adds a semantic text color (``"ok"``, ``"danger"``,
    ``"warn"``, ``"caution"``, ``"info"``).
    """
    tone_class = f" ss-{tone}" if tone else ""
    return f'<span class="ss-num{tone_class}">{html.escape(text)}</span>'


def formula_box(text: str) -> None:
    """Render text in a monospace formula panel (DEC-065).

    Used for calculation walk-throughs. ``text`` is escaped, so plain
    prose with numbers is rendered exactly as written.
    """
    st.markdown(
        f'<div class="ss-formula">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def flash(kind: str, message: str) -> None:
    """Queue a feedback message shown after the next rerun.

    Pages typically call ``st.rerun()`` after a successful write so all
    data refreshes; ``st.success`` emitted immediately before that would
    be discarded by the re-render, so the message rides through session
    state and is rendered by :func:`show_flash` at the top of the page.
    """
    st.session_state["flash"] = (kind, message)


def show_flash() -> None:
    """Render (and clear) any queued feedback message."""
    flash_message = st.session_state.pop("flash", None)
    if flash_message is None:
        return
    kind, message = flash_message
    if kind == "error":
        st.error(message, icon=ERROR_ICON)
    else:
        st.success(message, icon=SUCCESS_ICON)
