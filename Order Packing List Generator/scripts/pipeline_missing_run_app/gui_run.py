"""Missing Run GUI: pipeline worker + log drain."""

from __future__ import annotations

import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, StringVar, filedialog, messagebox

from pipeline_packing_list_app.config import logs_directory
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import _sanitize_process_for_filename

from .core import (
    DEFAULT_MISSING_TYPE,
    MISSING_PDF_SUBDIRS,
    PROJECT_ROOT,
    resolve_missing_pdf_copy_dir,
    run_missing_run_from_all_orders,
)


def browse_missing_input(app) -> None:
    path = filedialog.askopenfilename(
        title="Select Missing Input CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if path:
        app.missing_input_var.set(path)


def browse_all_orders(app) -> None:
    path = filedialog.askopenfilename(
        title="Select All Orders CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if path:
        app.all_orders_var.set(path)


def browse_directory(var: StringVar) -> None:
    dirname = filedialog.askdirectory()
    if dirname:
        var.set(dirname)


def append_log_ui(app, msg: str) -> None:
    app.log.configure(state=NORMAL)
    app.log.insert(END, "\n" + msg)
    app.log.see(END)
    app.log.configure(state=DISABLED)


def replace_log_step(app, msg: str) -> None:
    app.log.configure(state=NORMAL)
    app.log.delete("1.0", END)
    app.log.insert(END, msg)
    app.log.see(END)
    app.log.configure(state=DISABLED)


def drain_log_queue(app) -> bool:
    if app._log_queue is None:
        return False
    last_step: str | None = None
    while True:
        try:
            msg = app._log_queue.get_nowait()
        except queue.Empty:
            if last_step is not None:
                replace_log_step(app, last_step)
            return False
        if msg is None:
            if last_step is not None:
                replace_log_step(app, last_step)
            return True
        last_step = msg


def poll_log_queue(app) -> None:
    if drain_log_queue(app):
        return
    app.root.after(200, lambda: poll_log_queue(app))


def on_run(app) -> None:
    date_str = app.date_var.get().strip()
    process_name = app.process_name_var.get().strip()
    if not date_str or not process_name:
        messagebox.showerror("Error", "Date and Process name are required.")
        return
    missing_input = Path(app.missing_input_var.get().strip() or "")
    all_orders = Path(app.all_orders_var.get().strip() or "")
    if not missing_input.is_file():
        messagebox.showerror("Error", f"Missing Input CSV not found:\n{missing_input}")
        return
    if not all_orders.is_file():
        messagebox.showerror("Error", f"All Orders CSV not found:\n{all_orders}")
        return
    if not app.shift_var.get().strip():
        messagebox.showerror("Error", "Please select a shift.")
        return
    if (
        not app.use_demo_images_var.get()
        and not (app.apparel_dir_var.get() or "").strip()
        and not (app.logo_normal_dir_var.get() or "").strip()
        and not (app.logo_custom_single_dir_var.get() or "").strip()
        and not (app.logo_custom_double_dir_var.get() or "").strip()
    ):
        messagebox.showwarning(
            "No image directories",
            "Apparel/Design folders are empty. PDFs will show placeholders.",
        )

    shift = app.shift_var.get().strip()
    missing_type = app.missing_type_var.get().strip() or DEFAULT_MISSING_TYPE
    if missing_type not in MISSING_PDF_SUBDIRS:
        messagebox.showerror("Error", "Please choose Missing Logo or Missing Apparel.")
        return
    apparel_dir = (app.apparel_dir_var.get() or "").strip() or None
    logo_custom_single_dir = (app.logo_custom_single_dir_var.get() or "").strip() or None
    logo_custom_double_dir = (app.logo_custom_double_dir_var.get() or "").strip() or None
    logo_normal_dir = (app.logo_normal_dir_var.get() or "").strip() or None
    pdf_copy_dir = resolve_missing_pdf_copy_dir(
        (app.pdf_copy_dir_var.get() or "").strip() or None,
        missing_type,
    )
    excel_copy_dir = (app.excel_copy_dir_var.get() or "").strip() or None

    app.run_btn.configure(state=DISABLED)
    replace_log_step(
        app, f"Running missing pipeline for {date_str}, {process_name} ({missing_type})..."
    )
    app._log_queue = queue.Queue()
    app.root.after(200, lambda: poll_log_queue(app))

    def worker() -> None:
        logs_root = logs_directory()
        logs_root.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        safe = _sanitize_process_for_filename(process_name)
        log_path = (logs_root / f"{safe}_{ts}.log").resolve()
        fp = open(log_path, "a", encoding="utf-8", buffering=1)

        def detail_fn(msg: str) -> None:
            now = datetime.now()
            line = f"{now:%Y-%m-%d %H:%M:%S},{now.microsecond // 1000:03d} | INFO | {msg}"
            try:
                fp.write(line + "\n")
                fp.flush()
            except OSError as exc:
                print(f"[pipeline log] write failed ({log_path}): {exc}", file=sys.stderr, flush=True)
            print(line, flush=True)

        def on_step(msg: str) -> None:
            if app._log_queue is not None:
                app._log_queue.put(msg)

        pl = PipelineLog(detail_fn, on_step)
        try:
            pl.detail(f"Full pipeline transcript (this run): {log_path}")
            if pdf_copy_dir:
                pl.detail(f"PDF copy directory: {pdf_copy_dir}")
            output_root = run_missing_run_from_all_orders(
                missing_input_path=missing_input,
                all_orders_path=all_orders,
                process_name=process_name,
                date_dd_mm_yyyy=date_str,
                shift=shift,
                output_dir=PROJECT_ROOT / "Output",
                apparel_dir=apparel_dir,
                logo_custom_single_dir=logo_custom_single_dir,
                logo_custom_double_dir=logo_custom_double_dir,
                logo_normal_dir=logo_normal_dir,
                pdf_copy_dir=pdf_copy_dir,
                excel_copy_dir=excel_copy_dir,
                log=pl,
                use_demo_images=app.use_demo_images_var.get(),
            )
            app._run_output_root = output_root
            if app._log_queue is not None:
                app._log_queue.put(None)
            app.root.after(0, app._on_run_success)
        except Exception as exc:
            if app._log_queue is not None:
                app._log_queue.put(None)
            app.root.after(0, app._on_run_error, str(exc))
        finally:
            try:
                fp.close()
            except OSError:
                pass

    threading.Thread(target=worker, daemon=True).start()
