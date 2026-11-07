"""Data Import page (TASK-023 preview; TASK-024 persistence).

Historical dataset import per DEC-052/DEC-055: uploads are validated
and previewed before anything is stored, and historical imports never
modify operational inventory (BR-014, DEC-016). The page contains no
business rules and no SQL.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.domain.csv_import import CsvFileError, CsvStructureError
from smartstock.pages.ui import flash, show_flash
from smartstock.services import import_service
from smartstock.services.import_service import (
    DuplicateImportError,
    ImportRejectedError,
)


def render() -> None:
    """Render the Data Import page."""
    st.title("📥 Data Import")
    st.caption(
        "Historical CSV import for forecasting (format: date, store, "
        "item, sales). Rows are filtered to store 1 per the project's "
        "single-store decision. Imports never change current stock — "
        "they only feed analysis and forecasting."
    )

    show_flash()

    uploaded = st.file_uploader(
        "Historical sales CSV *",
        type=["csv"],
        key="import_file",
    )
    if uploaded is None:
        st.info(
            "Upload a CSV file to validate it and preview the records "
            "before importing. Nothing is stored until you confirm."
        )
        return

    try:
        preview = import_service.preview_import(uploaded)
    except (CsvFileError, CsvStructureError) as error:
        st.error(f"The file cannot be imported: {error}")
        return

    _render_preview(uploaded, preview)


def _render_preview(uploaded, preview) -> None:
    """Render the validation summary for one uploaded file (spec §8)."""
    st.subheader("📋 Preview")
    st.caption(
        f"{preview.filename} — {preview.file_size_bytes:,} bytes · "
        f"fingerprint {preview.sha256_fingerprint[:16]}…"
    )

    store_rows = st.columns(4)
    store_rows[0].metric("Rows in file", f"{preview.total_rows:,}")
    store_rows[1].metric(
        "Valid for store 1", f"{preview.valid_row_count:,}"
    )
    store_rows[2].metric(
        "Rejected (invalid)", f"{preview.invalid_in_scope_rows:,}"
    )
    store_rows[3].metric(
        "Other stores", f"{preview.out_of_store_rows:,}"
    )

    if preview.date_range is not None:
        first_date, last_date = preview.date_range
        st.caption(
            f"Date range of accepted rows: {first_date} → {last_date}; "
            f"{preview.duplicate_row_count:,} within-file duplicate(s)."
        )
    else:
        st.caption("No rows are in scope for store 1.")

    _render_validation_examples(preview)

    if not preview.importable:
        st.warning(
            "Nothing to import: the file contains no valid rows for "
            "store 1."
        )
        return

    if preview.sample_rows:
        import pandas as pd

        st.write("Sample of accepted records:")
        st.dataframe(
            pd.DataFrame(preview.sample_rows),
            hide_index=True,
            width="stretch",
        )

    # TASK-025 adds the detailed import summary display.
    _render_confirm_import(uploaded, preview)


def _render_confirm_import(uploaded, preview) -> None:
    """Confirm step: persist the accepted rows (DEC-054)."""
    if st.button(
        f"Import {preview.valid_row_count:,} record(s)",
        key="import_confirm",
        type="primary",
        help="Validated rows are stored in one transaction. Historical "
        "records never change current stock.",
    ):
        try:
            result = import_service.execute_import(uploaded)
        except import_service.DuplicateImportError as error:
            # DEC-053: the exact same file is already recorded.
            st.error(str(error))
            return
        except ImportRejectedError as error:
            st.error(f"Nothing was imported: {error}")
            return
        except DatabaseError as error:
            # DEC-054: a failed import leaves no partial data behind.
            st.error(f"The import failed and nothing was stored: {error}")
            return
        added = f"{result.imported_rows:,}"
        flash(
            "success",
            f"Imported {added} historical record(s) from "
            f"'{result.filename}' into import #{result.batch_id}. "
            "Current stock was not changed.",
        )
        st.rerun()


def _render_validation_examples(preview) -> None:
    """Show capped lists of rejected and duplicate rows (spec §13)."""
    sections = [
        (
            "❌ Rejected rows",
            preview.rejected_rows,
            preview.rejected_truncated,
        ),
        (
            "🔁 Within-file duplicates",
            preview.duplicate_rows,
            preview.duplicate_truncated,
        ),
    ]
    expanders = [col.container() for col in st.columns(len(sections))]
    for container, (title, rows, truncated) in zip(expanders, sections):
        if not rows:
            continue
        with container:
            with st.expander(f"{title} ({len(rows)} shown)"):
                if truncated:
                    st.caption(
                        "Showing the first examples only — see the "
                        "totals in the metrics above."
                    )
                for number, reason in rows:
                    st.markdown(f"- Row {number}: {reason}")
