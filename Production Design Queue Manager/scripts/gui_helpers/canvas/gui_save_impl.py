from __future__ import annotations
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
    get_output_folder,
)
from src.system.logging.run_logger import log_run_event

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
