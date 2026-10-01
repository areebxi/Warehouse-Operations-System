from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

from scripts.gui_theme import show_scrollable_message

from .runner_log import append_log, drain_log_queue, set_buttons_running


def on_pipeline_success(app) -> None:
    drain_log_queue(app)
    results = app._pipeline_results
    skipped = [r for r in (results or []) if r.get("skipped")]
    pdf_skipped = [r for r in (results or []) if r.get("pdf_skipped") and not r.get("skipped")]
    completed = [r for r in (results or []) if not r.get("skipped")]

    if skipped and completed:
        title = "Finished (with skips)"
        headline = "Pipeline completed with skipped inputs."
    elif skipped and not completed:
        title = "Finished (with skips)"
        headline = "Pipeline finished — all selected inputs were skipped."
    else:
        title = "Finished"
        headline = "Pipeline completed successfully."

    append_log(app, headline)
    msg_parts = [headline]
    for log_fp in getattr(app, "_session_log_files", None) or []:
        append_log(app, f"Log file: {log_fp}")
        msg_parts.append(f"\nLog file:\n{log_fp}")

    if skipped:
        append_log(app, "Skipped (input CSV missing / unavailable):")
        msg_parts += ["", "Skipped (input CSV missing / unavailable):"]
        for r in skipped:
            name = str(r.get("process_name") or "").strip() or "?"
            reason = str(r.get("skip_reason") or "Input CSV not found")
            line = f"Process {name} — {reason}"
            append_log(app, line)
            msg_parts.append(line)

    if pdf_skipped:
        append_log(app, "Skipped PDF (input CSV missing / unavailable):")
        msg_parts += ["", "Skipped PDF (input CSV missing / unavailable):"]
        for r in pdf_skipped:
            name = str(r.get("process_name") or "").strip() or "?"
            reason = str(r.get("pdf_skip_reason") or "Input CSV not found")
            line = f"Process {name} — {reason}"
            append_log(app, line)
            msg_parts.append(line)

    if results and (len(completed) > 1 or (skipped and completed)):
        processes_made = [
            str(e.get("process_name") or "").strip()
            for e in completed
            if str(e.get("process_name") or "").strip()
        ]
        unmatched_processes = [
            str(e.get("process_name"))
            for e in completed
            if isinstance(e.get("unmatched"), Path) and e.get("unmatched").exists()
        ]
        missing_logo_processes = [
            str(e.get("process_name"))
            for e in completed
            if isinstance(e.get("missing_logo"), Path) and e.get("missing_logo").exists()
        ]
        if processes_made:
            append_log(app, "Processes made:")
            for n in processes_made:
                append_log(app, f"Process {n}")
            msg_parts += ["", "Processes made:"] + [f"Process {n}" for n in processes_made]
        if unmatched_processes:
            append_log(app, "Unmatched orders file:")
            for n in unmatched_processes:
                append_log(app, f"Process {n}")
            msg_parts += ["", "Unmatched orders file:"] + [f"Process {n}" for n in unmatched_processes]
        if missing_logo_processes:
            append_log(app, "Missing logo orders file:")
            for n in missing_logo_processes:
                append_log(app, f"Process {n}")
            msg_parts += ["", "Missing logo orders file:"] + [f"Process {n}" for n in missing_logo_processes]
    elif not skipped:
        if app.output_root and app.output_root.exists():
            append_log(app, f"Output folder: {app.output_root}")
            msg_parts.append(f"\nOutput folder: {app.output_root}")
        if app.unmatched_path and app.unmatched_path.exists():
            append_log(app, f"Unmatched orders file: {app.unmatched_path}")
            msg_parts.append(f"\nUnmatched orders file: {app.unmatched_path}")
        if app.missing_logo_path and app.missing_logo_path.exists():
            append_log(app, f"Missing logo orders file: {app.missing_logo_path}")
            msg_parts.append(f"\nMissing logo orders file: {app.missing_logo_path}")
    elif len(completed) == 1:
        only = completed[0]
        out = only.get("output_root")
        if isinstance(out, Path) and out.exists():
            append_log(app, f"Output folder: {out}")
            msg_parts.append(f"\nOutput folder: {out}")

    missing_reports = [
        r.get("missing_logos_report")
        for r in completed
        if r.get("missing_logos_report")
    ]
    for report in missing_reports:
        msg_parts += ["", report]
    set_buttons_running(app, False)
    app._save_config()
    show_scrollable_message(app.root, title, "\n".join(msg_parts))


def on_pipeline_error(app, message: str) -> None:
    drain_log_queue(app)
    append_log(app, f"Error: {message}")
    for log_fp in getattr(app, "_session_log_files", None) or []:
        append_log(app, f"Log file (partial): {log_fp}")
    messagebox.showerror("Pipeline error", message)
    set_buttons_running(app, False)
