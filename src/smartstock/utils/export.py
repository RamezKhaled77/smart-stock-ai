"""CSV export helpers (TASK-049, DEC-063).

v1 exports are CSV only: the format every spreadsheet opens natively,
produced with Python's built-in ``csv`` module — no new dependency.
PDF export was considered and deferred (F-012) because it needs a
report library and adds little value for v1's tables.

Exports always serialize the raw service rows (the same dictionaries
the pages render), so a downloaded file always matches source data —
not a re-parsed display table.
"""

import csv
import io


def to_csv(rows: list, columns: list) -> str:
    """Serialize rows as CSV text with a header line.

    Args:
        rows: List of dictionaries (service output rows). Missing
            values become empty cells.
        columns: Column names in output order; also the header.

    Returns:
        CSV text with ``\\r\\n`` line endings per RFC 4180. An empty
        ``rows`` list yields just the header line.
    """
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="ignore"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue()
