"""
GUI save helper functions.

This module contains save methods extracted from QueueAppGUI
to reduce the main GUI file size.
"""
import os
import re
import time
import threading
from tkinter import messagebox

from src.core.canvas_creation import save_canvas_image as save_canvas_image_to_file
from src.io.file_handlers import extract_text_after_des
from src.core.image_utils import create_canvas_image
from gui_helpers.common.gui_progress import update_progress, reset_progress
from gui_helpers.processing.gui_processing_helpers_save import (
    extract_input_file_name,
    get_output_folder,
    create_output_folder_safe,
    generate_save_file_paths,
    check_and_confirm_file_overwrite,
    create_rar_and_copy,
)
from src.system.logging.run_logger import log_run_event


def _ui(gui, fn):
    """Run a callable on the Tk main thread."""
    if threading.current_thread() is threading.main_thread():
        fn()
    else:
        gui.root.after(0, fn)


def create_and_save_canvas(
    gui,
    arranged_designs,
    save_path,
    batch_num=None,
    total_batches=None,
    source_file_path=None,
):
    """Create and save canvas image with arranged designs"""
    if not arranged_designs:
        raise ValueError("No designs to save!")

    # Get text to display at top
    des_text = None
    input_file_name = None
    if source_file_path:
        input_file_name = os.path.basename(source_file_path)
    elif hasattr(gui, "input_file_path") and gui.input_file_path:
        input_file_name = os.path.basename(gui.input_file_path)

    if input_file_name:
        des_text = extract_text_after_des(input_file_name)

    # Add PART number if multiple batches
    part_text = None
    if total_batches and total_batches > 1 and batch_num:
        part_text = f"PART {batch_num}"

    # Create canvas image using imported function
    canvas_image = create_canvas_image(
        arranged_designs,
        gui.canvas_width_mm,
        gui.canvas_height_mm,
        gui.mm_to_pixel,
        gui.dpi,
        color_bar_image=gui.color_bar_image,
        des_text=des_text,
        part_text=part_text,
    )

    # Save the canvas image
    save_canvas_image_to_file(canvas_image, save_path, gui.dpi)


def save_canvas_for_file(gui, batches, file_path):
    """Save canvas for a specific file (used in folder processing)
    batches: list of batches, each batch is a list of arranged designs
    """
    try:
        # Get DTF Des file name without extension
        excel_file_name = os.path.splitext(os.path.basename(file_path))[0]
        # Remove "DTF Des-" from filename (case-insensitive)
        excel_file_name = re.sub(
            r"^DTF\s*Des-",
            "",
            excel_file_name,
            flags=re.IGNORECASE,
        ).strip()

        output_folder = get_output_folder()

        # Create folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Save each batch with Part number
        for batch_num, batch in enumerate(batches, 1):
            if len(batches) > 1:
                # Multiple batches: add Part number
                save_path = os.path.join(
                    output_folder,
                    f"{excel_file_name}_Part {batch_num}.png",
                )
            else:
                # Single batch: no Part number needed
                save_path = os.path.join(output_folder, f"{excel_file_name}.png")

            # Create and save canvas (pass batch info for text and source file path)
            create_and_save_canvas(
                gui,
                batch,
                save_path,
                batch_num=batch_num,
                total_batches=len(batches),
                source_file_path=file_path,
            )

    except Exception as e:
        print(f"Error saving canvas for {file_path}: {e}")


def save_canvas_image(gui):
    """Save the arranged canvas as an image file (heavy work runs off the UI thread)."""
    # Check if folder was processed - save each file separately
    if hasattr(gui, "folder_file_batches") and gui.folder_file_batches:
        from gui_helpers.canvas.gui_save_folder import save_folder_files_separately
        save_folder_files_separately(gui)
        return

    # Single file processing - save normally
    if hasattr(gui, "all_batches") and gui.all_batches and len(gui.all_batches) > 0:
        batches = gui.all_batches
    elif gui.arranged_designs:
        batches = [gui.arranged_designs]
    else:
        messagebox.showwarning("Warning", "No designs arranged to save!")
        return

    if getattr(gui, "_save_in_progress", False):
        messagebox.showinfo("Save in progress", "A save is already running. Please wait.")
        return

    input_file_name = extract_input_file_name(gui)
    output_folder = get_output_folder()

    if not create_output_folder_safe(output_folder):
        messagebox.showerror(
            "Error", f"Failed to create Output folder:\n{output_folder}"
        )
        return

    files_to_save = generate_save_file_paths(
        batches, input_file_name, output_folder
    )

    if not check_and_confirm_file_overwrite(files_to_save):
        return

    source_path = getattr(gui, "input_file_path", None)
    dtf_queues_folder = getattr(gui, "dtf_queues_folder", None)
    total_to_save = len(files_to_save)
    batch_count = len(batches)

    gui._save_in_progress = True
    update_progress(gui, 0, f"Preparing to save {total_to_save} image(s)...")

    def _worker():
        started_at = time.perf_counter()
        saved_files = []
        saved_file_paths = []
        try:
            for batch, file_path, batch_num, total_batches in files_to_save:
                progress = int((batch_num / total_batches) * 90)
                update_progress(
                    gui, progress, f"Saving batch {batch_num}/{total_batches}..."
                )
                create_and_save_canvas(
                    gui,
                    batch,
                    file_path,
                    batch_num=batch_num,
                    total_batches=total_batches,
                    source_file_path=source_path,
                )
                saved_files.append(os.path.basename(file_path))
                saved_file_paths.append(file_path)

            rar_info = create_rar_and_copy(
                gui,
                saved_file_paths,
                source_path,
                output_folder,
                dtf_queues_folder,
            )

            duration_ms = int((time.perf_counter() - started_at) * 1000)
            update_progress(gui, 100, "Save complete!")
            log_run_event(
                "save_completed",
                mode="single_file" if source_path else "folder",
                output_folder=output_folder,
                files_saved_total=len(saved_file_paths),
                first_file=saved_file_paths[0] if saved_file_paths else None,
                dtf_queues_folder=dtf_queues_folder,
                duration_ms=duration_ms,
            )

            if batch_count > 1:
                msg = (
                    f"Saved {batch_count} canvas images successfully!\n\n"
                    f"Folder: {output_folder}\n\nFiles:\n"
                    + "\n".join(saved_files)
                    + rar_info
                )
            else:
                msg = (
                    f"Canvas image saved successfully!\n\n"
                    f"Folder: {output_folder}\nFile: {saved_files[0]}"
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
                messagebox.showerror("Error", f"Failed to save image:\n{err}")
                log_run_event(
                    "save_failed",
                    level="error",
                    output_folder=output_folder,
                    error=err,
                )
                reset_progress(gui)

            _ui(gui, _fail)

    threading.Thread(target=_worker, name="SaveWorker", daemon=True).start()
