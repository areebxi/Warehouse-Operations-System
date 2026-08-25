import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, messagebox

from scripts.gui_theme import show_scrollable_message
from scripts.pipeline_runtime.pipeline_log import PipelineLog
from scripts.pipeline_runtime.runner import run_missing_logos_pipeline, run_pipeline
from scripts.pipeline_runtime.runner_utils import _FILENAME_UNSAFE, _sanitize_process_for_filename
from scripts.pipeline_shipstation.client import ShipStationError
from scripts.pipeline_shipstation.orders_to_csv import fetch_tag_orders_to_csv
from scripts.pipeline_shipstation.sync_tags_xlsx import DEFAULT_XLSX_PATH
from scripts.pipeline_shipstation.tags_process_lookup import resolve_tag_list_processes
from .config import DEFAULT_OUTPUT_DIR, PROJECT_ROOT, logs_directory


def get_input_paths(app) -> list[Path]:
    paths = getattr(app, "input_paths", None)
    if isinstance(paths, list):
        return list(paths)
    raw = (app.input_csv_var.get() or "").strip()
    return [Path(p.strip()) for p in raw.split(";") if p.strip()] if raw else []


def append_log(app, msg: str) -> None:
    app.log.insert(END, msg + "\n")
    app.log.see(END)


def replace_log_step(app, msg: str) -> None:
    app.log.delete("1.0", END)
    app.log.insert(END, msg)
    app.log.see(END)


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
    app.root.after(200, app._poll_log_queue)


def validate_image_folders(app) -> bool:
    """Require any non-empty image folder path to be an existing directory."""
    folders = (
        ("Apparel Image folder", app.apparel_dir_var.get()),
        ("Normal Logo/Design folder", app.logo_normal_dir_var.get()),
        ("Customise Single Position Logo/Design folder", app.logo_custom_single_dir_var.get()),
        ("Customise Double Position Logo/Design folder", app.logo_custom_double_dir_var.get()),
    )
    for label, raw in folders:
        path_str = (raw or "").strip()
        if not path_str:
            continue
        if not Path(path_str).is_dir():
            messagebox.showerror("Error", f"{label} is not a valid directory:\n{path_str}")
            return False
    return True


def resolve_selected_tag_processes(app) -> list[tuple[int, str, str]] | None:
    """
    Resolve process numbers for all selected tags.

    Returns None (and shows a messagebox) on failure.
    On success for a single tag with blank GUI, fills the process field from the sheet.
    """
    tags = (
        app.selected_shipstation_tags()
        if hasattr(app, "selected_shipstation_tags")
        else ([app.selected_shipstation_tag()] if app.selected_shipstation_tag() else [])
    )
    tags = [t for t in tags if t]
    multi = len(tags) > 1
    gui_value = "" if multi else (app.fixed_process_number_var.get() or "").strip()
    resolved, err = resolve_tag_list_processes(
        tags,
        shift_label=(app.shift_var.get() or "").strip(),
        gui_value=gui_value,
    )
    if err:
        messagebox.showerror("Error", err)
        return None
    for _tag_id, _tag_name, process_name in resolved:
        if _FILENAME_UNSAFE.search(process_name):
            messagebox.showerror(
                "Error", 'Fixed process number cannot contain / \\ : * ? " < > |'
            )
            return None
    if len(resolved) == 1 and not gui_value:
        app.fixed_process_number_var.set(resolved[0][2])
    return resolved


def validate_tag_mode(app) -> bool:
    """Validate date/shift/tag/process for ShipStation tag fetch."""
    tags = (
        app.selected_shipstation_tags()
        if hasattr(app, "selected_shipstation_tags")
        else ([app.selected_shipstation_tag()] if app.selected_shipstation_tag() else [])
    )
    tags = [t for t in tags if t]
    if not tags:
        messagebox.showerror("Error", "Please select at least one ShipStation tag.")
        return False
    try:
        datetime.strptime(app.date_var.get().strip(), "%d-%m-%Y")
    except Exception:
        messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
        return False
    shift = (app.shift_var.get() or "").strip()
    if not shift:
        messagebox.showerror("Error", "Please select a shift.")
        return False
    if resolve_selected_tag_processes(app) is None:
        return False
    workbook = Path(app.workbook_var.get())
    if not workbook.is_file():
        messagebox.showerror("Error", f"Workbook not found: {workbook}")
        return False
    if not validate_image_folders(app):
        return False
    return True


def validate_inputs(app) -> bool:
    if hasattr(app, "is_tag_mode") and app.is_tag_mode():
        return validate_tag_mode(app)
    paths = get_input_paths(app)
    if not paths or any(not p.is_file() for p in paths):
        messagebox.showerror("Error", "Please select an Input CSV file (or switch Input source to ShipStation tag).")
        return False
    if not app.use_fixed_process_number_var.get() and len(paths) > 1:
        messagebox.showerror(
            "Error", "Multiple input files are only supported when 'Use fixed process number' is enabled."
        )
        return False
    try:
        datetime.strptime(app.date_var.get().strip(), "%d-%m-%Y")
    except Exception:
        messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
        return False
    if not app.shift_var.get():
        messagebox.showerror("Error", "Please select a shift.")
        return False
    workbook = Path(app.workbook_var.get())
    if not workbook.is_file():
        messagebox.showerror("Error", f"Workbook not found: {workbook}")
        return False
    if not validate_image_folders(app):
        return False
    return True


def set_buttons_running(app, running: bool) -> None:
    app.run_btn.config(state=DISABLED if running else NORMAL)


def _make_pipeline_log_for_file(
    app,
    *,
    log_file_path: Path,
    stdout_prefix: str,
) -> tuple[PipelineLog, object]:
    """Open one detail log file and build PipelineLog (detail -> file+stdout, step -> GUI queue)."""
    path = Path(log_file_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(path, "a", encoding="utf-8", buffering=1)

    def detail_fn(msg: str) -> None:
        now = datetime.now()
        line = f"{now:%Y-%m-%d %H:%M:%S},{now.microsecond // 1000:03d} | INFO | {stdout_prefix}{msg}"
        try:
            fp.write(line + "\n")
            fp.flush()
        except OSError as exc:
            print(f"[pipeline log] write failed ({path}): {exc}", file=sys.stderr, flush=True)
        print(line, flush=True)

    def on_step(msg: str) -> None:
        disp = f"{stdout_prefix}{msg}" if stdout_prefix else msg
        if app._log_queue is not None:
            app._log_queue.put(disp)

    return PipelineLog(detail_fn, on_step), fp


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
        process_name = (app.fixed_process_number_var.get() or "").strip() or Path(input_path_str).stem
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
    if app.run_missing_logo_pipeline_var.get():
        start_banner = "Starting missing pipeline..."
    elif tag_mode:
        start_banner = "Fetching ShipStation orders…"
    else:
        start_banner = "Starting pipeline..."
    app.log.delete("1.0", END)
    replace_log_step(app, start_banner)
    app._log_queue = queue.Queue()
    app.root.after(200, app._poll_log_queue)

    def worker(ml_name: str | None = ml_process_name, use_tag: bool = tag_mode) -> None:
        logs_root = logs_directory()
        logs_root.mkdir(parents=True, exist_ok=True)
        try:
            (logs_root / "LAST_SESSION_DIR.txt").unlink(missing_ok=True)
        except OSError:
            pass
        ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        app._session_log_files = []
        used_log_bases: set[str] = set()
        open_files: list[object] = []

        def run_with_log_file(rel_stem: str, stdout_prefix: str) -> PipelineLog:
            safe = _sanitize_process_for_filename(rel_stem)
            base = f"{safe}_{ts}"
            name_base = base
            n = 2
            while name_base in used_log_bases:
                name_base = f"{base}_{n}"
                n += 1
            used_log_bases.add(name_base)
            log_path = (logs_root / f"{name_base}.log").resolve()
            pl, fp = _make_pipeline_log_for_file(app, log_file_path=log_path, stdout_prefix=stdout_prefix)
            open_files.append(fp)
            app._session_log_files.append(str(log_path))
            pl.detail(f"Full pipeline transcript (this run): {log_path}")
            return pl

        try:
            if app.run_missing_logo_pipeline_var.get():
                inp = (app.input_csv_var.get() or "").strip()
                stem = Path(inp).stem if inp else "missing"
                pl = run_with_log_file(stem, "")
                pl.detail(start_banner)
                output_root = run_missing_logos_pipeline(
                    app.input_csv_var.get().strip(),
                    ml_name or "",
                    app.output_dir_var.get() or str(DEFAULT_OUTPUT_DIR),
                    app.date_var.get().strip(),
                    app.apparel_dir_var.get() or None,
                    app.logo_custom_single_dir_var.get() or None,
                    app.logo_custom_double_dir_var.get() or None,
                    app.logo_normal_dir_var.get() or None,
                    shift=app.shift_var.get().strip(),
                    pdf_copy_dir=(app.pdf_copy_dir_var.get() or "").strip() or None,
                    excel_copy_dir=(app.excel_copy_dir_var.get() or "").strip() or None,
                    log=pl,
                )
                app.output_root, app.unmatched_path, app.missing_logo_path, app._pipeline_results = (
                    output_root,
                    None,
                    None,
                    None,
                )
            else:
                pl: PipelineLog | None = None
                output_root = unmatched = missing_logo = None
                results: list[dict] = []

                def _logo_id_threshold() -> int:
                    return (
                        int(app.logo_id_threshold_var.get())
                        if str(app.logo_id_threshold_var.get()).strip().isdigit()
                        else 5
                    )

                def _run_one_pipeline(
                    csv_path: Path | str,
                    *,
                    pl: PipelineLog,
                    use_fixed: bool,
                    fixed_process: str | None,
                    phases: str = "all",
                ):
                    return run_pipeline(
                        str(csv_path),
                        app.date_var.get().strip(),
                        app.shift_var.get().strip(),
                        app.output_dir_var.get() or str(DEFAULT_OUTPUT_DIR),
                        app.workbook_var.get(),
                        app.apparel_dir_var.get() or None,
                        app.logo_custom_single_dir_var.get() or None,
                        app.logo_custom_double_dir_var.get() or None,
                        app.logo_normal_dir_var.get() or None,
                        separate_by_logo_id=app.separate_by_logo_id_var.get(),
                        logo_id_threshold=_logo_id_threshold(),
                        use_fixed_process_number=use_fixed,
                        fixed_process_number=fixed_process,
                        pdf_copy_dir=(app.pdf_copy_dir_var.get() or "").strip() or None,
                        excel_copy_dir=(app.excel_copy_dir_var.get() or "").strip() or None,
                        log=pl,
                        phases=phases,  # type: ignore[arg-type]
                    )

                def _emit_batch_banner(message: str, logs: list[PipelineLog]) -> None:
                    if app._log_queue is not None:
                        app._log_queue.put(message)
                    for _pl in logs:
                        _pl.detail(message)

                if use_tag:
                    tags = (
                        app.selected_shipstation_tags()
                        if hasattr(app, "selected_shipstation_tags")
                        else (
                            [app.selected_shipstation_tag()]
                            if app.selected_shipstation_tag()
                            else []
                        )
                    )
                    tags = [t for t in tags if t]
                    if not tags:
                        raise ShipStationError("No ShipStation tag selected.")
                    multi_tags = len(tags) > 1
                    gui_value = (
                        ""
                        if multi_tags
                        else (app.fixed_process_number_var.get() or "").strip()
                    )
                    resolved, err = resolve_tag_list_processes(
                        tags,
                        shift_label=app.shift_var.get().strip(),
                        gui_value=gui_value,
                    )
                    if err or not resolved:
                        raise ShipStationError(err or "Could not resolve process numbers.")
                    if len(resolved) == 1 and not gui_value:
                        app.root.after(0, app.fixed_process_number_var.set, resolved[0][2])

                    batch_phase = "excel" if multi_tags else "all"
                    pdf_jobs: list[dict] = []

                    for tag_id, tag_name, process_name in resolved:
                        prefix = f"[{process_name}] " if multi_tags else ""
                        pl = run_with_log_file(process_name or tag_name or "shipstation", prefix)

                        def _fetch_log(msg: str, _pl=pl) -> None:
                            _pl.detail(msg)
                            if app._log_queue is not None:
                                app._log_queue.put(msg)

                        if multi_tags or not gui_value:
                            pl.detail(
                                f"Using process {process_name} from {DEFAULT_XLSX_PATH.name} "
                                f"for tag '{tag_name}' / shift '{app.shift_var.get().strip()}'."
                            )
                        csv_path = fetch_tag_orders_to_csv(
                            tag_id=tag_id,
                            tag_name=tag_name,
                            date_dd_mm_yyyy=app.date_var.get().strip(),
                            shift_label=app.shift_var.get().strip(),
                            process_number=process_name,
                            input_root=PROJECT_ROOT / "Input",
                            log=_fetch_log,
                        )
                        start_msg = (
                            "Starting Excel phase (batch)…"
                            if multi_tags
                            else "Starting pipeline…"
                        )
                        pl.detail(start_msg)
                        if app._log_queue is not None:
                            app._log_queue.put(f"{prefix}{start_msg}")
                        output_root, unmatched, missing_logo, missing_logos_report = _run_one_pipeline(
                            csv_path,
                            pl=pl,
                            use_fixed=True,
                            fixed_process=process_name,
                            phases=batch_phase,
                        )
                        entry = {
                            "input": csv_path,
                            "output_root": output_root,
                            "unmatched": unmatched,
                            "missing_logo": missing_logo,
                            "process_name": output_root.name if output_root else process_name,
                            "missing_logos_report": missing_logos_report,
                        }
                        results.append(entry)
                        if multi_tags:
                            pdf_jobs.append(
                                {
                                    "csv_path": csv_path,
                                    "pl": pl,
                                    "prefix": prefix,
                                    "process_name": process_name,
                                    "entry": entry,
                                }
                            )

                    if pdf_jobs:
                        banner = (
                            f"Batch: Excel complete for {len(pdf_jobs)} inputs — starting PDF phase…"
                        )
                        _emit_batch_banner(banner, [j["pl"] for j in pdf_jobs])
                        for job in pdf_jobs:
                            job["pl"].detail(f"{job['prefix']}Starting PDF phase…")
                            if app._log_queue is not None:
                                app._log_queue.put(f"{job['prefix']}Starting PDF phase…")
                            _, _, _, missing_logos_report = _run_one_pipeline(
                                job["csv_path"],
                                pl=job["pl"],
                                use_fixed=True,
                                fixed_process=job["process_name"],
                                phases="pdf",
                            )
                            job["entry"]["missing_logos_report"] = missing_logos_report
                            output_root = job["entry"]["output_root"]
                            unmatched = job["entry"]["unmatched"]
                            missing_logo = job["entry"]["missing_logo"]
                else:
                    paths = get_input_paths(app)
                    use_fixed = app.use_fixed_process_number_var.get()
                    fixed_gui = (app.fixed_process_number_var.get() or "").strip()
                    multi = len(paths) > 1
                    batch_phase = "excel" if multi else "all"
                    pdf_jobs = []

                    for csv_path in paths:
                        prefix = f"[{csv_path.stem}] " if multi else ""
                        pl = run_with_log_file(csv_path.stem, prefix)
                        fixed_for_this = (
                            (fixed_gui or csv_path.stem)
                            if use_fixed and len(paths) == 1
                            else (csv_path.stem if use_fixed else None)
                        )
                        start_msg = (
                            "Starting Excel phase (batch)…"
                            if multi
                            else "Starting pipeline…"
                        )
                        pl.detail(start_msg)
                        if app._log_queue is not None:
                            app._log_queue.put(f"{prefix}{start_msg}")
                        output_root, unmatched, missing_logo, missing_logos_report = _run_one_pipeline(
                            csv_path,
                            pl=pl,
                            use_fixed=use_fixed,
                            fixed_process=fixed_for_this,
                            phases=batch_phase,
                        )
                        entry = {
                            "input": csv_path,
                            "output_root": output_root,
                            "unmatched": unmatched,
                            "missing_logo": missing_logo,
                            "process_name": output_root.name if output_root else csv_path.stem,
                            "missing_logos_report": missing_logos_report,
                        }
                        results.append(entry)
                        if multi:
                            pdf_jobs.append(
                                {
                                    "csv_path": csv_path,
                                    "pl": pl,
                                    "prefix": prefix,
                                    "fixed_for_this": fixed_for_this,
                                    "use_fixed": use_fixed,
                                    "entry": entry,
                                }
                            )

                    if pdf_jobs:
                        banner = (
                            f"Batch: Excel complete for {len(pdf_jobs)} inputs — starting PDF phase…"
                        )
                        _emit_batch_banner(banner, [j["pl"] for j in pdf_jobs])
                        for job in pdf_jobs:
                            job["pl"].detail(f"{job['prefix']}Starting PDF phase…")
                            if app._log_queue is not None:
                                app._log_queue.put(f"{job['prefix']}Starting PDF phase…")
                            _, _, _, missing_logos_report = _run_one_pipeline(
                                job["csv_path"],
                                pl=job["pl"],
                                use_fixed=job["use_fixed"],
                                fixed_process=job["fixed_for_this"],
                                phases="pdf",
                            )
                            job["entry"]["missing_logos_report"] = missing_logos_report
                            output_root = job["entry"]["output_root"]
                            unmatched = job["entry"]["unmatched"]
                            missing_logo = job["entry"]["missing_logo"]

                app.output_root, app.unmatched_path, app.missing_logo_path, app._pipeline_results = (
                    output_root,
                    unmatched,
                    missing_logo,
                    results,
                )
            app._log_queue.put(None)
            app.root.after(0, app._on_pipeline_success)
        except Exception as exc:
            app._log_queue.put(None)
            app.root.after(0, app._on_pipeline_error, str(exc))
        finally:
            for fp in open_files:
                try:
                    fp.flush()
                    fd = fp.fileno()
                    if fd >= 0:
                        os.fsync(fd)
                except (OSError, AttributeError, ValueError):
                    pass
                try:
                    fp.close()
                except OSError:
                    pass

    threading.Thread(target=worker, daemon=True).start()


def on_pipeline_success(app) -> None:
    drain_log_queue(app)
    append_log(app, "Pipeline completed successfully.")
    msg_parts = ["Pipeline completed successfully."]
    for log_fp in getattr(app, "_session_log_files", None) or []:
        append_log(app, f"Log file: {log_fp}")
        msg_parts.append(f"\nLog file:\n{log_fp}")
    results = app._pipeline_results
    if results and len(results) > 1:
        processes_made = [
            str(e.get("process_name") or "").strip() for e in results if str(e.get("process_name") or "").strip()
        ]
        unmatched_processes = [
            str(e.get("process_name"))
            for e in results
            if isinstance(e.get("unmatched"), Path) and e.get("unmatched").exists()
        ]
        missing_logo_processes = [
            str(e.get("process_name"))
            for e in results
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
    else:
        if app.output_root and app.output_root.exists():
            append_log(app, f"Output folder: {app.output_root}")
            msg_parts.append(f"\nOutput folder: {app.output_root}")
        if app.unmatched_path and app.unmatched_path.exists():
            append_log(app, f"Unmatched orders file: {app.unmatched_path}")
            msg_parts.append(f"\nUnmatched orders file: {app.unmatched_path}")
        if app.missing_logo_path and app.missing_logo_path.exists():
            append_log(app, f"Missing logo orders file: {app.missing_logo_path}")
            msg_parts.append(f"\nMissing logo orders file: {app.missing_logo_path}")
    missing_reports = [r.get("missing_logos_report") for r in (results or []) if r.get("missing_logos_report")]
    for report in missing_reports:
        msg_parts += ["", report]
    set_buttons_running(app, False)
    app._save_config()
    show_scrollable_message(app.root, "Finished", "\n".join(msg_parts))


def on_pipeline_error(app, message: str) -> None:
    drain_log_queue(app)
    append_log(app, f"Error: {message}")
    for log_fp in getattr(app, "_session_log_files", None) or []:
        append_log(app, f"Log file (partial): {log_fp}")
    messagebox.showerror("Pipeline error", message)
    set_buttons_running(app, False)
