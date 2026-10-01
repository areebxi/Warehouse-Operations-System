from __future__ import annotations

import queue
import sys
from datetime import datetime
from pathlib import Path
from tkinter import DISABLED, END, NORMAL

from pipeline_runtime.pipeline_log import PipelineLog


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
