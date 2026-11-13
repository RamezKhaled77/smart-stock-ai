"""Data Import page (TASK-023 preview, TASK-024 persistence, TASK-025
import summary).

Historical dataset import per DEC-052/DEC-055: uploads are validated
and previewed before anything is stored, and historical imports never
modify operational inventory (BR-014, DEC-016). The page contains no
business rules and no SQL.

Interface text comes from the bilingual string table via
:func:`smartstock.i18n.t` (F-020, DEC-066); English remains the
default language. Row-level validation reasons come from the CSV
import validator and the service layer's duplicate/rejection messages
stay in English in v1.
"""

import streamlit as st

from smartstock.database.connection import DatabaseError
from smartstock.domain.csv_import import CsvFileError, CsvStructureError
from smartstock.i18n import t
from smartstock.pages.ui import (
    empty_state,
    flash,
    page_header,
    section,
    show_flash,
)
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
    page_header(
        "upload_file",
        t("imports.title"),
        t("imports.description"),
    )

    show_flash()

    uploaded = st.file_uploader(
        t("imports.uploader_label"),
        type=["csv"],
        key="import_file",
    )
    if uploaded is None:
        empty_state(
            t("imports.empty_title"),
            t("imports.empty_message"),
            icon="upload",
        )
        _render_import_history()
        return

    try:
        preview = import_service.preview_import(uploaded)
    except (CsvFileError, CsvStructureError) as error:
        st.error(
            t("imports.error_file", error=error),
            icon=":material/error:",
        )
        return

    _render_preview(uploaded, preview)
    _render_import_history()


def _render_preview(uploaded, preview) -> None:
    """Render the validation summary for one uploaded file (spec §8)."""
    already_imported = _is_current_file_imported(preview)

    section("fact_check", t("imports.section_preview"))
    st.caption(
        t(
            "imports.caption_file",
            filename=preview.filename,
            size=preview.file_size_bytes,
            fingerprint=preview.sha256_fingerprint[:16],
        )
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
    store_rows[0].metric(
        t("imports.metric_rows"),
        f"{preview.total_rows:,}",
        icon=":material/description:",
        border=True,
    )
    store_rows[1].metric(
        t("imports.metric_valid"),
        f"{preview.valid_row_count:,}",
        icon=":material/check_circle:",
        border=True,
    )
    store_rows[2].metric(
        t("imports.metric_rejected"),
        f"{preview.invalid_in_scope_rows:,}",
        icon=":material/cancel:",
        border=True,
    )
    store_rows[3].metric(
        t("imports.metric_other_stores"),
        f"{preview.out_of_store_rows:,}",
        icon=":material/filter_alt:",
        border=True,
    )

    if preview.date_range is not None:
        first_date, last_date = preview.date_range
        st.caption(
            t(
                "imports.caption_date_range",
                first=first_date,
                last=last_date,
                duplicates=preview.duplicate_row_count,
            )
        )
    else:
        st.caption(t("imports.caption_no_rows"))

    _render_validation_examples(preview)

    if not preview.importable:
        st.warning(
            t("imports.warning_nothing"),
            icon=":material/warning:",
        )
        return

    if preview.sample_rows:
        import pandas as pd

        st.write(t("imports.sample_caption"))
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
        t("imports.button_import", count=preview.valid_row_count),
        key="import_confirm",
        type="primary",
        icon=":material/upload_2:",
        help=t("imports.button_import_help"),
    ):
        try:
            result = import_service.execute_import(uploaded)
        except DuplicateImportError as error:
            # DEC-053: the exact same file is already recorded.
            st.error(str(error))
            return
        except ImportRejectedError as error:
            st.error(t("imports.error_rejected", error=error))
            return
        except DatabaseError as error:
            # DEC-054: a failed import leaves no partial data behind.
            st.error(t("imports.error_failed", error=error))
            return
        st.session_state[LAST_IMPORT_KEY] = {
            "result": result,
            "fingerprint": preview.sha256_fingerprint,
        }
        flash(
            "success",
            t(
                "imports.success_imported",
                count=result.imported_rows,
                filename=result.filename,
                batch_id=result.batch_id,
            ),
        )
        st.rerun()


def _render_import_result(result) -> None:
    """Show the spec §14 summary for the file's stored import batch."""
    st.success(
        t(
            "imports.result_success",
            batch_id=result.batch_id,
            created_at=result.created_at,
        ),
        icon=":material/task_alt:",
    )
    metric_columns = st.columns(4)
    metric_columns[0].metric(
        t("imports.result_metric_stored"),
        f"{result.imported_rows:,}",
        icon=":material/check_circle:",
        border=True,
    )
    metric_columns[1].metric(
        t("imports.metric_rejected"),
        f"{result.rejected_rows:,}",
        icon=":material/cancel:",
        border=True,
    )
    metric_columns[2].metric(
        t("imports.result_metric_duplicates"),
        f"{result.duplicate_rows:,}",
        icon=":material/compare_arrows:",
        border=True,
    )
    metric_columns[3].metric(
        t("imports.metric_other_stores"),
        f"{result.out_of_store_rows:,}",
        icon=":material/filter_alt:",
        border=True,
    )
    date_note = (
        t(
            "imports.result_date_note",
            first=result.date_range[0],
            last=result.date_range[1],
        )
        if result.date_range is not None
        else ""
    )
    st.caption(
        t(
            "imports.result_caption",
            store=result.store,
            filename=result.filename,
            rows=result.total_rows,
            date_note=date_note,
        )
    )
    st.info(
        t("imports.result_reupload_info"),
        icon=":material/sync:",
    )


def _render_import_history() -> None:
    """Expandable overview of all recorded import batches (TASK-025)."""
    with st.expander(
        t("imports.history_title"), icon=":material/history:"
    ):
        try:
            summary = import_service.get_import_summary()
        except DatabaseError as error:
            st.error(t("imports.history_error", error=error))
            return
        st.caption(
            t(
                "imports.history_caption",
                records=summary["total_records"],
                count=len(summary["batches"]),
            )
        )
        if not summary["batches"]:
            st.info(
                t("imports.history_empty"),
                icon=":material/history:",
            )
            return
        import pandas as pd

        rows = [
            {
                t("imports.column_batch"): batch["id"],
                t("imports.column_file"): batch["source_filename"],
                t("imports.column_imported"): batch["imported_rows"],
                t("imports.column_duplicates"): batch["duplicate_rows"],
                t("imports.column_rejected"): batch["rejected_rows"],
                t("imports.column_other_stores"): batch[
                    "out_of_store_rows"
                ],
                t("imports.column_date_range"): (
                    f"{batch['first_date']} → {batch['last_date']}"
                    if batch["first_date"]
                    else "—"
                ),
                t("imports.column_when"): batch["created_at"],
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
            t("imports.expander_rejected"),
            ":material/cancel:",
            preview.rejected_rows,
            preview.rejected_truncated,
        ),
        (
            t("imports.expander_duplicates"),
            ":material/compare_arrows:",
            preview.duplicate_rows,
            preview.duplicate_truncated,
        ),
    ]
    expanders = [col.container() for col in st.columns(len(sections))]
    for container, (title, icon, rows, truncated) in zip(
        expanders, sections
    ):
        if not rows:
            continue
        with container:
            with st.expander(
                f"{title} {t('imports.shown_suffix', count=len(rows))}",
                icon=icon,
            ):
                if truncated:
                    st.caption(t("imports.truncated_caption"))
                for number, reason in rows:
                    st.markdown(
                        t("imports.row_line", number=number, reason=reason)
                    )
