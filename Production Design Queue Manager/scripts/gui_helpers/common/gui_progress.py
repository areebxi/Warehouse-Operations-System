"""
GUI progress bar helper functions.
"""

import threading

from gui_helpers.common import gui_theme


def update_progress(gui, value, text=""):
    """Update progress bar and label (safe from worker threads)."""

    def _apply():
        if gui.progress_var:
            gui.progress_var.set(value)
        if gui.progress_label and text:
            # Clear then set so shorter text does not leave leftover glyphs
            gui.progress_label.config(text="")
            gui.progress_label.config(text=text, foreground=gui_theme.FG)
        try:
            gui.root.update_idletasks()
        except Exception:
            pass

    if threading.current_thread() is threading.main_thread():
        _apply()
    else:
        try:
            gui.root.after(0, _apply)
        except Exception:
            pass


def reset_progress(gui):
    """Reset progress bar"""

    def _apply():
        if gui.progress_var:
            gui.progress_var.set(0)
        if gui.progress_label:
            gui.progress_label.config(text="Ready", foreground=gui_theme.MUTED)

    if threading.current_thread() is threading.main_thread():
        _apply()
    else:
        try:
            gui.root.after(0, _apply)
        except Exception:
            pass
