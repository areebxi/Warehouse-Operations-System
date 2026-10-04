"""
GUI settings management helper functions.
"""

from gui_helpers.common.gui_common import load_path_setting, update_label_with_path
from gui_helpers.selection.gui_file_selection import refresh_input_listbox


def _persist_folder(gui, attr: str, key: str, *, keep_prev_when_demo: bool) -> object:
    """Folder value to write: never clobber saved paths with demo/None mid-load."""
    prev = gui.saved_settings or {}
    if keep_prev_when_demo:
        return prev.get(key)
    val = getattr(gui, attr, None)
    return val if val is not None else prev.get(key)


def save_settings(gui):
    """Save current settings to file"""
    try:
        from gui_helpers.common.gui_demo_mode import use_demo

        paths = getattr(gui, "input_file_paths", None) or []
        input_file = ";".join(paths) if paths else None
        demo = bool(use_demo(gui))

        designs = _persist_folder(gui, "designs_folder", "designs_folder", keep_prev_when_demo=demo)
        single = _persist_folder(
            gui, "single_designs_folder", "single_designs_folder", keep_prev_when_demo=demo
        )
        double = _persist_folder(
            gui, "double_designs_folder", "double_designs_folder", keep_prev_when_demo=demo
        )
        # DTF queues may be intentionally cleared to None
        dtf = gui.dtf_queues_folder if not demo else (gui.saved_settings or {}).get(
            "dtf_queues_folder"
        )

        gui.settings_manager.save_settings(
            input_file=input_file,
            input_folder_path=None,
            cl_csv_path=gui.cl_csv_var.get().strip() or None,
            config_workbook_path=gui.config_workbook_var.get().strip() or None,
            designs_folder=designs,
            single_designs_folder=single,
            double_designs_folder=double,
            dtf_queues_folder=dtf,
            use_demo_images=demo,
        )
        gui.saved_settings = gui.settings_manager.saved_settings
    except Exception as e:
        print(f"Error saving settings: {e}")


def auto_load_settings(gui):
    """Auto-load saved file and folder paths"""
    try:
        if hasattr(gui, "use_demo_images_var"):
            gui.use_demo_images_var.set(bool(gui.saved_settings.get("use_demo_images")))

        # Folders first so a mid-load save cannot wipe them with None
        load_path_setting(gui, "designs_folder", "designs_folder", "folder_label")
        load_path_setting(gui, "single_designs_folder", "single_designs_folder", "single_folder_label")
        load_path_setting(gui, "double_designs_folder", "double_designs_folder", "double_folder_label")
        load_path_setting(gui, "dtf_queues_folder", "dtf_queues_folder", "dtf_queues_label")

        raw = (gui.saved_settings.get("input_file") or "").strip()
        gui.input_file_paths = []
        if raw:
            import os

            for part in raw.split(";"):
                path = part.strip()
                if path and os.path.isfile(path):
                    gui.input_file_paths.append(path)
        gui.input_file_path = (
            gui.input_file_paths[0] if len(gui.input_file_paths) == 1 else None
        )
        gui.input_folder_path = None
        gui.df = None
        refresh_input_listbox(gui)

        if hasattr(gui, "cl_csv_var"):
            gui.cl_csv_var.set(
                gui.saved_settings.get("cl_csv_path")
                or gui.cl_csv_var.get()
            )
        if hasattr(gui, "config_workbook_var"):
            gui.config_workbook_var.set(
                gui.saved_settings.get("config_workbook_path")
                or gui.config_workbook_var.get()
            )
        if hasattr(gui, "_reload_data_sources"):
            gui._reload_data_sources()

        from gui_helpers.common.gui_demo_mode import apply_resolved_folders, use_demo

        apply_resolved_folders(gui)
        if use_demo(gui):
            update_label_with_path(
                gui, "folder_label", gui.designs_folder, prefix="Normal (demo): "
            )
            update_label_with_path(
                gui, "single_folder_label", gui.single_designs_folder, prefix="Single (demo): "
            )
            update_label_with_path(
                gui, "double_folder_label", gui.double_designs_folder, prefix="Double (demo): "
            )
    except Exception as e:
        print(f"Error auto-loading settings: {e}")


def on_offline_testing_toggle(gui):
    """Apply demo folders when Testing is enabled; save preference."""
    from gui_helpers.common.gui_demo_mode import apply_resolved_folders, use_demo
    from gui_helpers.common.gui_common import update_label_with_path

    # Save flag first without writing demo paths into JSON
    save_settings(gui)

    if use_demo(gui):
        apply_resolved_folders(gui)
        update_label_with_path(
            gui, "folder_label", gui.designs_folder, prefix="Normal (demo): "
        )
        update_label_with_path(
            gui, "single_folder_label", gui.single_designs_folder, prefix="Single (demo): "
        )
        update_label_with_path(
            gui, "double_folder_label", gui.double_designs_folder, prefix="Double (demo): "
        )
    else:
        # Restore user folders from persisted settings into attrs + labels
        load_path_setting(gui, "designs_folder", "designs_folder", "folder_label")
        load_path_setting(gui, "single_designs_folder", "single_designs_folder", "single_folder_label")
        load_path_setting(gui, "double_designs_folder", "double_designs_folder", "double_folder_label")
        apply_resolved_folders(gui)
