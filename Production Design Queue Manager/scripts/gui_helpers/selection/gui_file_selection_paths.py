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
