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


# Storage format for operational dates (ISO 8601 calendar date).
DATE_FORMAT = "%Y-%m-%d"


def utc_today_iso() -> str:
    """Return the current UTC date as an ISO ``YYYY-MM-DD`` string.

    Used for date validations such as rejecting future sale dates.
    """
    return datetime.now(timezone.utc).strftime(DATE_FORMAT)
