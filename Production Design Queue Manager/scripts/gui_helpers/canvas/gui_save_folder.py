"""Folder-processing save flow for canvas exports."""

import os
import re
import threading
from tkinter import messagebox

from src.io.rar_utils import create_rar_from_pngs, generate_rar_name, copy_rar_to_dtf_queues
from gui_helpers.common.gui_progress import update_progress, reset_progress
from gui_helpers.canvas.gui_save import create_and_save_canvas, _ui
from gui_helpers.processing.gui_processing_helpers_save import get_output_folder


def save_folder_files_separately(gui):
    """Save each file from folder processing separately with its own filename."""
    if not gui.folder_file_batches:
        messagebox.showwarning("Warning", "No files to save!")
        return

    if getattr(gui, "_save_in_progress", False):
        messagebox.showinfo("Save in progress", "A save is already running. Please wait.")
        return

    output_folder = get_output_folder()

    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create Output folder:\n{str(e)}")
        return

    all_files_to_save = []
    for file_path, batches in gui.folder_file_batches.items():
        excel_file_name = os.path.splitext(os.path.basename(file_path))[0]
        excel_file_name = re.sub(r"^DTF\s*Des-", "", excel_file_name, flags=re.IGNORECASE).strip()

        for batch_num, batch in enumerate(batches, 1):
            if len(batches) > 1:
                save_path = os.path.join(output_folder, f"{excel_file_name}_Part {batch_num}.png")
            else:
                save_path = os.path.join(output_folder, f"{excel_file_name}.png")

            all_files_to_save.append(
                (batch, save_path, batch_num, len(batches), excel_file_name, file_path)
            )

    existing_files = [fp for _, fp, _, _, _, _ in all_files_to_save if os.path.exists(fp)]
    if existing_files:
        response = messagebox.askyesno(
            "File Exists",
            f"{len(existing_files)} file(s) already exist(s).\n\nDo you want to overwrite them?",
        )
        if not response:
            return

    total_to_save = len(all_files_to_save)
    total_source_files = len(gui.folder_file_batches)
    dtf_queues_folder = gui.dtf_queues_folder

    gui._save_in_progress = True
    update_progress(gui, 0, f"Preparing to save {total_to_save} image(s)...")

    def _worker():
        saved_files = []
        saved_file_paths = []
        saved_files_info = []
        try:
            for idx, (batch, save_path, batch_num, total_batches, _file_name, source_file_path) in enumerate(
                all_files_to_save, 1
            ):
                progress = int((idx / total_to_save) * 90)
                update_progress(
                    gui,
                    progress,
                    f"Saving file {idx}/{total_to_save}: {os.path.basename(save_path)}",
                )
                create_and_save_canvas(
                    gui,
                    batch,
                    save_path,
                    batch_num=batch_num,
                    total_batches=total_batches,
                    source_file_path=source_file_path,
                )
                saved_files.append(os.path.basename(save_path))
                saved_file_paths.append(save_path)
                saved_files_info.append((save_path, source_file_path))

            rar_info = ""
            if dtf_queues_folder:
                try:
                    update_progress(gui, 90, "Creating RAR archive...")
                    rar_name = generate_rar_name(saved_files_info, is_folder_processing=True)
                    rar_path = os.path.join(output_folder, rar_name)
                    success, result = create_rar_from_pngs(saved_file_paths, rar_path)
                    if success:
                        update_progress(gui, 95, "Copying RAR to DTF Queues folder...")
                        copy_success, copy_result = copy_rar_to_dtf_queues(
                            result, dtf_queues_folder
                        )
                        if copy_success:
                            rar_info = (
                                f"\n\nRAR created and copied to DTF Queues folder:\n"
                                f"{os.path.basename(result)}"
                            )
                        else:
                            rar_info = f"\n\nRAR created but copy failed:\n{copy_result}"
                    else:
                        rar_info = f"\n\nRAR creation failed:\n{result}"
                except Exception as e:
                    rar_info = f"\n\nRAR creation error: {str(e)}"

            update_progress(gui, 100, "Save complete!")
            msg = (
                f"Saved {len(saved_files)} canvas image(s) from {total_source_files} "
                f"file(s) successfully!\n\nFolder: {output_folder}\n\nFiles:\n"
                + "\n".join(saved_files[:20])
                + ("\n..." if len(saved_files) > 20 else "")
                + rar_info
            )

            def _done():
                gui._save_in_progress = False
                messagebox.showinfo("Success", msg)
                gui.root.after(1000, lambda: reset_progress(gui))

            _ui(gui, _done)
        except Exception as e:
            err = str(e)

            def _fail():
                gui._save_in_progress = False
                update_progress(gui, 0, "Save failed")
                messagebox.showerror("Error", f"Failed to save images:\n{err}")
                reset_progress(gui)

            _ui(gui, _fail)

    threading.Thread(target=_worker, name="SaveWorker", daemon=True).start()
