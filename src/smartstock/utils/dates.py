"""Small date and timestamp helpers.

Used by database layers that need consistent ISO 8601 formatting.
Kept independent of Streamlit, the database implementation, and the UI.
"""

from datetime import datetime, timezone

# Storage format for operational timestamps (ISO 8601, UTC).
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 timestamp string.

    Example: ``2026-11-04T12:34:56Z``
    """
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
