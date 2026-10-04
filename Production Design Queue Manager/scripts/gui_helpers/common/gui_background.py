"""
Run slow, Tk-free work on a worker thread while the window stays responsive.

Design images and workbooks live on Google Drive (I:/G:), where a single file
read can take seconds to minutes. Doing that on the Tk main thread stops the
window from processing messages and Windows marks it "Not Responding".
"""

import threading
import tkinter as tk
from typing import Any, Callable

_POLL_SECONDS = 0.02


def run_keeping_ui_alive(gui, fn: Callable[..., Any], *args, **kwargs) -> Any:
    """Run ``fn(*args, **kwargs)`` on a worker thread and pump Tk events until done.

    ``fn`` must not touch Tk widgets. Returns fn's result or re-raises its error.
    Callers must guard re-entry (see ``DesignArrangerGUI._run_exclusive``),
    because button clicks are processed while this waits.
    """
    if threading.current_thread() is not threading.main_thread():
        return fn(*args, **kwargs)

    outcome = {}

    def _worker():
        try:
            outcome["value"] = fn(*args, **kwargs)
        except BaseException as exc:  # re-raised on the main thread
            outcome["error"] = exc

    worker = threading.Thread(target=_worker, name="UIBackgroundWork", daemon=True)
    worker.start()
    while worker.is_alive():
        try:
            gui.root.update()
        except tk.TclError:
            # Window was destroyed; finish the work without pumping.
            worker.join()
            break
        worker.join(_POLL_SECONDS)

    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("value")
