"""Shared UI helpers for Streamlit pages.

Keeps page code free of duplicated interaction patterns and gives every
page one consistent presentation layer:

- :func:`page_header` — standard title with a Material icon and a
  one-line description.
- :func:`section` — standard section heading with a Material icon.
- :func:`empty_state` — standard empty state that explains why an area
  is empty and what to do next.

Icons come from the Material Symbols (Rounded) font that Streamlit ships
and render through the framework's own ``":material/<icon>:"`` handling
— no custom CSS and no extra dependency (UI design system, DEC-064).

These helpers hold no business rules — pages stay responsible for their
own content.
"""

import streamlit as st

# Reused alert icons so every page signals state the same way.
SUCCESS_ICON = ":material/check_circle:"
INFO_ICON = ":material/info:"
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"

STATUS_ICON = {
    "success": SUCCESS_ICON,
    "error": ERROR_ICON,
}


def page_header(icon: str, title: str, description: str = "") -> None:
    """Standard page header: icon, title, and a short description."""
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
