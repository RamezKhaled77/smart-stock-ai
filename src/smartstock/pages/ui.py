"""Small shared UI helpers for Streamlit pages.

Keeps page code free of duplicated interaction patterns. These helpers
hold no business rules — pages stay responsible for their own content.
"""

import streamlit as st


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
        st.error(message)
    else:
        st.success(message)
