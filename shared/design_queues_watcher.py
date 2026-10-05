"""Ensure the Queue SharedInbox Design Queues watcher is running.

Packing List starts this on launch so operators do not need run_design_queues_watcher.bat.
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from shared import paths as wh

_MARKER = "design_queues_watcher"
_CREATE_NO_WINDOW = 0x08000000
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def watcher_script_path(from_path: object | None = None) -> Path:
    return wh.queue_app_dir(from_path) / "scripts" / "design_queues_watcher.py"


def pid_file_path(from_path: object | None = None) -> Path:
    # ponytail: PID file under SharedInbox root — ceiling is rare PID reuse after crash;
    # upgrade: also match process image/cmdline if that becomes a problem.
    return wh.shared_inbox_dtf_des_root(from_path) / ".design_queues_watcher.pid"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_pid(from_path: object | None = None) -> Optional[int]:
    path = pid_file_path(from_path)
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return None
    if not lines:
        return None
    try:
        pid = int(lines[0].strip())
    except ValueError:
        return None
    if len(lines) > 1 and lines[1].strip() and lines[1].strip() != _MARKER:
        return None
    return pid


def is_running(from_path: object | None = None) -> bool:
    pid = read_pid(from_path)
    if pid is None:
        return False
    if _pid_alive(pid):
        return True
    clear_pid(from_path)
    return False


def write_pid(pid: int | None = None, from_path: object | None = None) -> Path:
    path = pid_file_path(from_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{pid if pid is not None else os.getpid()}\n{_MARKER}\n", encoding="utf-8")
    return path


def clear_pid(from_path: object | None = None) -> None:
    path = pid_file_path(from_path)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def claim_this_process(from_path: object | None = None) -> None:
    """Call from the long-running watcher process only."""
    write_pid(os.getpid(), from_path=from_path)
    atexit.register(clear_pid, from_path)


def ensure_running(from_path: object | None = None) -> tuple[str, str]:
    """
    Start the watcher if needed.

    Returns (status, message) where status is already_running | started | failed.
    """
    if is_running(from_path):
        pid = read_pid(from_path)
        return "already_running", f"Design Queues watcher already running (pid {pid})"

    script = watcher_script_path(from_path)
    if not script.is_file():
        return "failed", f"Watcher script not found: {script}"

    app_dir = wh.queue_app_dir(from_path)
    cmd = [sys.executable, str(script)]
    try:
        kwargs: dict = {
            "cwd": str(app_dir),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if sys.platform == "win32":
            # Watcher already logs to Queue Logs/; no console window needed.
            kwargs["creationflags"] = (
                _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW
            )
        else:
            kwargs["start_new_session"] = True

        proc = subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        return "failed", f"Could not start Design Queues watcher: {exc}"

    # Parent writes PID immediately so a second Packing launch won't double-start
    # before the child claims via claim_this_process().
    if proc.pid and _pid_alive(proc.pid):
        write_pid(proc.pid, from_path=from_path)
        return "started", f"Started Design Queues watcher (pid {proc.pid})"
    return "failed", "Design Queues watcher exited immediately after start"
