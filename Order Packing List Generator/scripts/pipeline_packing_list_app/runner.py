"""Packing List GUI run/validate helpers — stable façade."""

from __future__ import annotations

import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import END, messagebox

from pipeline_runtime.runner_utils import _FILENAME_UNSAFE
from pipeline_split_by_process_item.common import pin_batch_shift

from .config import logs_directory
from .runner_log import (
    _make_pipeline_log_for_file,
    append_log,
    drain_log_queue,
    poll_log_queue,
    replace_log_step,
    set_buttons_running,
)
from .runner_success import on_pipeline_error, on_pipeline_success
from .runner_validate import (
    get_input_paths,
    resolve_cl_csv_path,
    resolve_selected_tag_processes,
    validate_image_folders,
    validate_inputs,
    validate_tag_mode,
)
from .runner_worker import pipeline_worker

__all__ = [
    "get_input_paths",
    "resolve_cl_csv_path",
    "append_log",
    "replace_log_step",
    "drain_log_queue",
    "poll_log_queue",
    "validate_image_folders",
    "resolve_selected_tag_processes",
    "validate_tag_mode",
    "validate_inputs",
    "set_buttons_running",
    "_make_pipeline_log_for_file",
    "on_run_clicked",
    "on_pipeline_success",
    "on_pipeline_error",
]


def on_run_clicked(app) -> None:
    app._pipeline_results = None
    app._session_log_files = []
    ml_process_name = None
    tag_mode = False
    if app.run_missing_logo_pipeline_var.get():
        input_path_str = (app.input_csv_var.get() or "").strip()
        if ";" in input_path_str or not input_path_str or not Path(input_path_str).is_file():
            messagebox.showerror("Error", "Please select a single valid Missing file (Excel/CSV).")
            return
        ext = Path(input_path_str).suffix.lower()
        if ext not in (".xlsx", ".xlsm", ".csv"):
            messagebox.showerror(
                "Error", "Missing pipeline supports only Excel (.xlsx, .xlsm) or CSV (.csv) files."
            )
            return
        try:
            datetime.strptime(app.date_var.get().strip(), "%d-%m-%Y")
        except Exception:
            messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
            return
        if not app.shift_var.get():
            messagebox.showerror("Error", "Please select a shift.")
            return
        if not validate_image_folders(app):
            return
        process_name = pin_batch_shift(
            (app.fixed_process_number_var.get() or "").strip() or Path(input_path_str).stem
        )
        if _FILENAME_UNSAFE.search(process_name):
            messagebox.showerror(
                "Error", 'Fixed process number (from filename) cannot contain / \\ : * ? " < > |'
            )
            return
        ml_process_name = process_name
    elif not validate_inputs(app):
        return
    else:
        tag_mode = bool(hasattr(app, "is_tag_mode") and app.is_tag_mode())

    try:
        logs_root = logs_directory()
        logs_root.mkdir(parents=True, exist_ok=True)
        probe = logs_root / ".write_probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        messagebox.showerror(
            "Cannot create logs folder",
            f"The app could not create or write to the logs directory:\n{logs_directory()}\n\n{exc}",
        )
        return

    set_buttons_running(app, True)
    if app.run_missing_logo_pipeline_var.get():
        app.unmatched_path = None
        app.missing_logo_path = None
        start_banner = "Starting missing pipeline..."
    elif tag_mode:
        start_banner = "Fetching ShipStation orders…"
    else:
        start_banner = "Starting pipeline..."
    app.log.delete("1.0", END)
    replace_log_step(app, start_banner)
    app._log_queue = queue.Queue()
    app.root.after(200, app._poll_log_queue)

    threading.Thread(
        target=pipeline_worker,
        kwargs={
            "app": app,
            "ml_name": ml_process_name,
            "use_tag": tag_mode,
            "start_banner": start_banner,
        },
        daemon=True,
    ).start()
