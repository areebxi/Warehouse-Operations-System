"""
GUI settings management helper functions.
"""

import pandas as pd

from gui_helpers.common.gui_common import load_path_setting, update_label_with_path


def save_settings(gui):
    """Save current settings to file"""
    try:
        # Only save the active input method (file or folder), clear the other
        input_file = None
        input_folder_path = None
        if hasattr(gui, "input_file_path") and gui.input_file_path:
            input_file = gui.input_file_path
        elif gui.input_folder_path:
            input_folder_path = gui.input_folder_path

        gui.settings_manager.save_settings(
            input_file=input_file,
            input_folder_path=input_folder_path,
            size_reference_file=gui.size_reference_path,
            designs_folder=gui.designs_folder,
            single_designs_folder=gui.single_designs_folder,
            double_designs_folder=gui.double_designs_folder,
            dtf_queues_folder=gui.dtf_queues_folder,
        )
        gui.saved_settings = gui.settings_manager.saved_settings
    except Exception as e:
        print(f"Error saving settings: {e}")


def auto_load_settings(gui):
    """Auto-load saved file and folder paths"""
    try:
        def load_input_file(file_path):
            if file_path.endswith(".csv"):
                gui.df = pd.read_csv(file_path)
            else:
                gui.df = pd.read_excel(file_path)
            gui.input_file_path = file_path

        load_path_setting(
            gui,
            setting_key="input_file",
            gui_attr="input_file_path",
            label_attr="file_label",
            loader_func=load_input_file,
        )

        # Load input folder if exists
        if load_path_setting(
            gui,
            setting_key="input_folder_path",
            gui_attr="input_folder_path",
            label_attr="file_label",
        ):
            update_label_with_path(gui, "file_label", gui.input_folder_path, prefix="Folder: ")

        # Skip loading size reference from saved settings - it's auto-loaded from Configuration Workbook
        load_path_setting(gui, "designs_folder", "designs_folder", "folder_label")
        load_path_setting(gui, "single_designs_folder", "single_designs_folder", "single_folder_label")
        load_path_setting(gui, "double_designs_folder", "double_designs_folder", "double_folder_label")
        load_path_setting(gui, "dtf_queues_folder", "dtf_queues_folder", "dtf_queues_label")
    except Exception as e:
        print(f"Error auto-loading settings: {e}")

