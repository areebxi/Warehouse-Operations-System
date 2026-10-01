from __future__ import annotations

import os
from datetime import datetime

from .config import logs_directory
from .runner_worker_files import run_file_mode_pipelines
from .runner_worker_helpers import make_run_one_pipeline, make_run_with_log_file
from .runner_worker_missing import run_missing_logo_worker
from .runner_worker_tag import run_tag_mode_pipelines


def pipeline_worker(app, *, ml_name: str | None, use_tag: bool, start_banner: str) -> None:
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
    run_with_log_file = make_run_with_log_file(
        app, logs_root=logs_root, ts=ts, used_log_bases=used_log_bases, open_files=open_files
    )
    run_one_pipeline = make_run_one_pipeline(app)

    try:
        if app.run_missing_logo_pipeline_var.get():
            run_missing_logo_worker(
                app,
                ml_name=ml_name or "",
                start_banner=start_banner,
                run_with_log_file=run_with_log_file,
            )
        elif use_tag:
            output_root, unmatched, missing_logo, results = run_tag_mode_pipelines(
                app, run_with_log_file=run_with_log_file, run_one_pipeline=run_one_pipeline
            )
            app.output_root, app.unmatched_path, app.missing_logo_path, app._pipeline_results = (
                output_root,
                unmatched,
                missing_logo,
                results,
            )
        else:
            output_root, unmatched, missing_logo, results = run_file_mode_pipelines(
                app, run_with_log_file=run_with_log_file, run_one_pipeline=run_one_pipeline
            )
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
