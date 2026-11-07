"""Data Import page (TASK-023 preview, TASK-024 persistence, TASK-025
import summary).

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

# Session-state key holding the last import outcome for the currently
# uploaded file: {"result": ImportResult, "fingerprint": sha256}.
LAST_IMPORT_KEY = "import_last_result"


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
        _render_import_history()
        return

    try:
        preview = import_service.preview_import(uploaded)
    except (CsvFileError, CsvStructureError) as error:
        st.error(f"The file cannot be imported: {error}")
        return

    _render_preview(uploaded, preview)
    _render_import_history()


def _render_preview(uploaded, preview) -> None:
    """Render the validation summary for one uploaded file (spec §8)."""
    already_imported = _is_current_file_imported(preview)

    st.subheader("📋 Preview")
    st.caption(
        f"{preview.filename} — {preview.file_size_bytes:,} bytes · "
        f"fingerprint {preview.sha256_fingerprint[:16]}…"
    )

    if already_imported:
        # TASK-025: the uploaded file's batch result summary instead of
        # a second confirm button (an identical re-import is rejected
        # anyway, DEC-053).
        _render_import_result(
            st.session_state[LAST_IMPORT_KEY]["result"]
        )
        return

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

    _render_confirm_import(uploaded, preview)


def _is_current_file_imported(preview) -> bool:
    """Whether the uploaded file is the one of the last import run."""
    summary_state = st.session_state.get(LAST_IMPORT_KEY)
    if not summary_state:
        return False
    return summary_state.get("fingerprint") == preview.sha256_fingerprint


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
        except DuplicateImportError as error:
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
        st.session_state[LAST_IMPORT_KEY] = {
            "result": result,
            "fingerprint": preview.sha256_fingerprint,
        }
        flash(
            "success",
            f"Imported {result.imported_rows:,} historical record(s) "
            f"from '{result.filename}' (batch #{result.batch_id}). "
            "Current stock was not changed.",
        )
        st.rerun()


def _render_import_result(result) -> None:
    """Show the spec §14 summary for the file's stored import batch."""
    st.success(
        f"✅ Import completed — batch #{result.batch_id} "
        f"({result.created_at})."
    )
    metric_columns = st.columns(4)
    metric_columns[0].metric("Accepted and stored", f"{result.imported_rows:,}")
    metric_columns[1].metric(
        "Rejected (invalid)", f"{result.rejected_rows:,}"
    )
    metric_columns[2].metric(
        "Duplicates skipped", f"{result.duplicate_rows:,}"
    )
    metric_columns[3].metric(
        "Other stores", f"{result.out_of_store_rows:,}"
    )
    date_note = (
        f" · accepted rows span {result.date_range[0]} → "
        f"{result.date_range[1]}"
        if result.date_range is not None
        else ""
    )
    st.caption(
        f"Historical dataset import, store {result.store} · file "
        f"'{result.filename}' ({result.total_rows:,} rows "
        f"processed){date_note}. Current inventory was not changed."
    )
    st.info(
        "To import more data, upload a different CSV file. Re-uploading "
        "this exact file is rejected by its fingerprint (DEC-053)."
    )


def _render_import_history() -> None:
    """Expandable overview of all recorded import batches (TASK-025)."""
    with st.expander("📚 Previous imports", expanded=False):
        try:
            summary = import_service.get_import_summary()
        except DatabaseError as error:
            st.error(f"Import history could not be read: {error}")
            return
        st.caption(
            f"{summary['total_records']:,} historical record(s) stored "
            f"in total across {len(summary['batches'])} import run(s)."
        )
        if not summary["batches"]:
            st.info("No imports recorded yet.")
            return
        import pandas as pd

        rows = [
            {
                "Batch": batch["id"],
                "File": batch["source_filename"],
                "Imported": batch["imported_rows"],
                "Duplicates skipped": batch["duplicate_rows"],
                "Rejected": batch["rejected_rows"],
                "Other stores": batch["out_of_store_rows"],
                "Date range": (
                    f"{batch['first_date']} → {batch['last_date']}"
                    if batch["first_date"]
                    else "—"
                ),
                "When (UTC)": batch["created_at"],
            }
            for batch in summary["batches"]
        ]
        st.dataframe(
            pd.DataFrame(rows), hide_index=True, width="stretch"
        )


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
