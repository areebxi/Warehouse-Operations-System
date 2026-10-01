from __future__ import annotations
import os
from tkinter import filedialog, messagebox
from src.system.logging.run_logger import log_run_event
from gui_helpers.common import gui_theme
from gui_helpers.common.gui_common import (
    select_folder_common,
    update_label_with_path,
)

def add_input_files(gui):
    """Add one or more DTF Des files (multi-select dialog)."""
    initialdir = None
    paths = getattr(gui, "input_file_paths", None) or []
    if paths:
        initialdir = os.path.dirname(paths[-1])
    elif gui.saved_settings.get("input_file"):
        first = str(gui.saved_settings.get("input_file") or "").split(";")[0].strip()
        if first:
            initialdir = os.path.dirname(first)

    selected = filedialog.askopenfilenames(
        title="Select DTF Des File(s)",
        initialdir=initialdir,
        filetypes=[("DTF Des files", "*.xlsx *.xls *.csv"), ("All files", "*.*")],
    )
    if not selected:
        return None

    if not hasattr(gui, "input_file_paths") or gui.input_file_paths is None:
        gui.input_file_paths = []

    added = 0
    for path in selected:
        if path and path not in gui.input_file_paths:
            gui.input_file_paths.append(path)
            added += 1

    _sync_legacy_input_file_path(gui)
    refresh_input_listbox(gui)
    gui.save_settings()
    log_run_event(
        "files_selected",
        mode="multi_file",
        files_count=len(gui.input_file_paths),
        added=added,
    )
    return list(selected)
def refresh_input_listbox(gui):
    """Refresh the input listbox and summary label from gui.input_file_paths."""
    paths = getattr(gui, "input_file_paths", None) or []
    if hasattr(gui, "input_listbox"):
        gui.input_listbox.delete(0, "end")
        for path in paths:
            gui.input_listbox.insert("end", path)
    if hasattr(gui, "file_label"):
        if not paths:
            gui.file_label.config(text="No files selected", foreground=gui_theme.MUTED)
        elif len(paths) == 1:
            update_label_with_path(gui, "file_label", paths[0])
        else:
            gui.file_label.config(
                text=f"{len(paths)} files selected",
                foreground=gui_theme.FG,
            )
def remove_selected_input_files(gui):
    """Remove highlighted files from the input list."""
    if not hasattr(gui, "input_listbox"):
        return
    sel = set(gui.input_listbox.curselection())
    if not sel:
        return
    gui.input_file_paths = [
        p for i, p in enumerate(gui.input_file_paths or []) if i not in sel
    ]
    _sync_legacy_input_file_path(gui)
    refresh_input_listbox(gui)
    gui.save_settings()
def _sync_legacy_input_file_path(gui):
    """Keep input_file_path as the sole path when exactly one file is selected."""
    paths = getattr(gui, "input_file_paths", None) or []
    gui.input_file_path = paths[0] if len(paths) == 1 else None
    gui.input_folder_path = None
    gui.df = None
def remove_all_input_files(gui):
    """Clear all selected input files."""
    gui.input_file_paths = []
    _sync_legacy_input_file_path(gui)
    refresh_input_listbox(gui)
    gui.save_settings()
def select_input_file(gui):
    """Compatibility alias — multi-select Add files…"""
    return add_input_files(gui)
