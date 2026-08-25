"""
GUI file selection helper functions.
"""

import os
from tkinter import filedialog, messagebox

import pandas as pd
from src.system.logging.run_logger import log_run_event

from gui_helpers.common import gui_theme
from gui_helpers.common.gui_common import (
    select_file_common,
    select_folder_common,
    update_label_with_path,
)


def select_input_file(gui):
    """Select a DTF Des file (Excel Worksheet containing order information)"""

    def load_input_file(file_path):
        """Load the input file into gui.df"""
        if file_path.endswith(".csv"):
            gui.df = pd.read_csv(file_path)
        else:
            gui.df = pd.read_excel(file_path)
        log_run_event(
            "file_loaded",
            mode="single_file",
            file_path=file_path,
            rows_total=len(gui.df),
            columns_total=len(gui.df.columns),
        )
        messagebox.showinfo("Success", f"File loaded successfully!\nRows: {len(gui.df)}")

    select_file_common(
        gui,
        setting_key="input_file",
        gui_attr="input_file_path",
        label_attr="file_label",
        title="Select Input File",
        filetypes=[("DTF Des files", "*.xlsx *.xls *.csv"), ("All files", "*.*")],
        on_selected=load_input_file,
        clear_attrs=[("input_folder_path", None)],
    )


def select_input_folder(gui):
    """Select a folder containing DTF Des files"""

    def after_folder_selected(folder_path):
        """Handle folder selection - find DTF Des files and show message"""
        excel_files = []
        for file in os.listdir(folder_path):
            # Check if file has "DTF Des" in name and is a valid Excel/CSV file
            if (
                "dtf des" in file.lower()
                and file.endswith((".xlsx", ".xls", ".csv"))
                and not file.startswith("~$")
            ):
                excel_files.append(os.path.join(folder_path, file))

        if excel_files:
            log_run_event(
                "folder_selected",
                folder_path=folder_path,
                dtf_files_count=len(excel_files),
            )
            messagebox.showinfo(
                "Folder Selected",
                f"Found {len(excel_files)} DTF Des file(s) in folder.\n\nClick 'Normal' or 'Personalised' to process all files.",
            )
        else:
            log_run_event(
                "folder_selected",
                level="warning",
                folder_path=folder_path,
                dtf_files_count=0,
            )
            messagebox.showwarning("Warning", "No DTF Des file(s) found in selected folder!")

    folder_path = select_folder_common(
        gui,
        setting_key="input_file",
        gui_attr="input_folder_path",
        label_attr="file_label",
        title="Select Input Folder",
        fallback_setting_key=None,
        clear_attrs=[("input_file_path", None), ("df", None)],
    )

    if folder_path:
        # Update label with "Folder: " prefix
        update_label_with_path(gui, "file_label", folder_path, prefix="Folder: ")
        after_folder_selected(folder_path)


def select_size_reference_file(gui):
    """Select size reference file"""

    from src.io.file_loaders import _prepare_size_reference_df

    def load_size_reference(file_path):
        """Load the size reference file"""
        gui.size_reference_df = _prepare_size_reference_df(pd.read_excel(file_path))
        gui.size_reference_path = file_path

        messagebox.showinfo(
            "Success", f"Size Reference loaded!\n{len(gui.size_reference_df)} entries found."
        )

    from gui_helpers.common.gui_common import select_file_common

    select_file_common(
        gui,
        setting_key="size_reference_file",
        gui_attr="size_reference_path",
        label_attr=None,  # No label in GUI since auto-loaded
        title="Select Size Reference File",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        on_selected=load_size_reference,
    )


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

