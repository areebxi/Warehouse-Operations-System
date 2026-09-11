"""
GUI file selection helper functions.
"""

import os
from tkinter import filedialog, messagebox

from src.system.logging.run_logger import log_run_event

from gui_helpers.common import gui_theme
from gui_helpers.common.gui_common import (
    select_folder_common,
    update_label_with_path,
)


def _sync_legacy_input_file_path(gui):
    """Keep input_file_path as the sole path when exactly one file is selected."""
    paths = getattr(gui, "input_file_paths", None) or []
    gui.input_file_path = paths[0] if len(paths) == 1 else None
    gui.input_folder_path = None
    gui.df = None


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


def remove_all_input_files(gui):
    """Clear all selected input files."""
    gui.input_file_paths = []
    _sync_legacy_input_file_path(gui)
    refresh_input_listbox(gui)
    gui.save_settings()


def select_input_file(gui):
    """Compatibility alias — multi-select Add files…"""
    return add_input_files(gui)


def select_cl_csv(gui):
    """Select Custom Label Database CSV for print sizes."""
    initial = gui.cl_csv_var.get() if hasattr(gui, "cl_csv_var") else ""
    file_path = filedialog.askopenfilename(
        title="Select Custom Label Database (CSV)",
        initialdir=os.path.dirname(initial) if initial else None,
        initialfile=os.path.basename(initial) if initial else None,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        return None
    gui.cl_csv_var.set(file_path)
    gui._reload_data_sources()
    gui.save_settings()
    messagebox.showinfo("Success", f"CL database set to:\n{file_path}")
    return file_path


def select_size_reference_file(gui):
    """Legacy alias — select Configuration Workbook."""
    select_config_workbook(gui)


def select_config_workbook(gui):
    """Select Configuration Workbook."""
    initial = gui.config_workbook_var.get() if hasattr(gui, "config_workbook_var") else ""
    file_path = filedialog.askopenfilename(
        title="Select Configuration Workbook",
        initialdir=os.path.dirname(initial) if initial else None,
        initialfile=os.path.basename(initial) if initial else None,
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
    )
    if not file_path:
        return None
    gui.config_workbook_var.set(file_path)
    gui._reload_data_sources()
    gui.save_settings()
    messagebox.showinfo("Success", f"Configuration Workbook set to:\n{file_path}")
    return file_path


def select_designs_folder(gui):
    """Select designs folder"""
    select_folder_common(
        gui,
        setting_key="designs_folder",
        gui_attr="designs_folder",
        label_attr="folder_label",
        title="Select Designs Folder",
    )


def select_single_designs_folder(gui):
    """Select single design folder for personalised processing"""
    select_folder_common(
        gui,
        setting_key="single_designs_folder",
        gui_attr="single_designs_folder",
        label_attr="single_folder_label",
        title="Select Single Design Folder",
        fallback_setting_key="designs_folder",
    )


def select_double_designs_folder(gui):
    """Select double design folder for personalised processing"""
    select_folder_common(
        gui,
        setting_key="double_designs_folder",
        gui_attr="double_designs_folder",
        label_attr="double_folder_label",
        title="Select Double Design Folder",
        fallback_setting_key="designs_folder",
    )


def select_dtf_queues_folder(gui):
    """Select DTF Queues folder for RAR upload"""
    import queue_app

    app_dir = os.path.dirname(os.path.abspath(queue_app.__file__))

    initialdir = gui.saved_settings.get("dtf_queues_folder") or app_dir

    folder_path = filedialog.askdirectory(
        title="Select DTF Queues Folder", initialdir=initialdir
    )
    if folder_path:
        gui.dtf_queues_folder = folder_path
        update_label_with_path(gui, "dtf_queues_label", folder_path)
        gui.save_settings()
        return folder_path
    return None


def remove_dtf_queues_folder(gui):
    """Remove/clear DTF Queues folder directory"""
    gui.dtf_queues_folder = None
    gui.dtf_queues_label.config(
        text="No folder selected",
        foreground=gui_theme.MUTED,
    )
    gui.save_settings()
    messagebox.showinfo(
        "Success",
        "DTF Queues folder has been removed. Files will no longer be sent to DTF Queues folder.",
    )
