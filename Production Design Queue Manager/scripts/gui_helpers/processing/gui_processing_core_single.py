"""Single-file core folder processing flow."""

import os
from datetime import datetime
from tkinter import messagebox

from src.core.canvas_arranger import pack_designs
from src.core.design_processor import process_single_designs
from src.system.logging.utils import (
    finish_size_determination_log,
    log_size_determination,
    save_error_to_file,
    start_size_determination_log,
)
from .gui_processing_helpers import (
    auto_detect_customise_column,
    create_design_log_entry,
    handle_missing_sizes_warning,
    is_customise_yes,
    is_plainlg_sku,
    track_missing_size_reference,
)


def process_single_file_for_folder(gui, df, column, file_path):
    """Process a single DTF Des file for folder processing."""
    try:
        gui.is_personalised = False
        start_size_determination_log(file_path, "standard")
        log_stats = {"total_designs": 0, "size_reference_used": 0, "original_dimensions_used": 0, "resized": 0}
        customise_col = auto_detect_customise_column(df)
        mask = df[column].notna()
        skus = df.loc[mask, column].tolist()
        customise_vals = (
            df.loc[mask, customise_col].tolist()
            if customise_col else [None] * len(skus)
        )
        if not skus:
            finish_size_determination_log()
            return [], [], []

        designs = []
        missing_skus = []
        missing_sizes = []
        missing_size_row_indices = []

        for sku, customise in zip(skus, customise_vals):
            if is_plainlg_sku(sku):
                continue
            design_items = process_single_designs(
                sku,
                gui.designs_folder,
                gui.size_reference_df,
                gui.mm_to_pixel,
                getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set,
                canvas_width_mm=gui.canvas_width_mm,
                canvas_height_mm=gui.canvas_height_mm,
                design_padding=gui.design_padding,
                force_single=is_customise_yes(customise),
            )

            if design_items:
                for design_data in design_items:
                    log_entry = create_design_log_entry(sku, "Standard", design_data)
                    log_size_determination(log_entry)
                    if design_data.get("size_info"):
                        log_stats["size_reference_used"] += 1
                    else:
                        log_stats["original_dimensions_used"] += 1
                    log_stats["total_designs"] += 1

                    size_code = design_data.get("size_code")
                    size_info = design_data.get("size_info")
                    if size_code and not size_info:
                        missing_entry = f"{sku} ({size_code})"
                        if missing_entry not in missing_sizes:
                            missing_sizes.append(missing_entry)
                            track_missing_size_reference(df, column, sku, missing_size_row_indices)

                    designs.append(
                        {
                            "sku": design_data["sku"],
                            "image": design_data["image"],
                            "path": design_data["path"],
                            "width": design_data["width"],
                            "height": design_data["height"],
                            "width_mm": design_data["width_mm"],
                            "height_mm": design_data["height_mm"],
                            "size_code": design_data.get("size_code"),
                        }
                    )
            else:
                missing_skus.append(sku)

        if not designs:
            finish_size_determination_log(log_stats)
            return [], [], missing_size_row_indices

        if missing_skus:
            messagebox.showwarning(
                "Warning",
                f"Could not find designs for {len(missing_skus)} SKUs in {os.path.basename(file_path) if file_path else 'file'}:\n"
                + ", ".join(str(s) for s in missing_skus[:10])
                + ("..." if len(missing_skus) > 10 else ""),
            )

        handle_missing_sizes_warning(
            missing_sizes, missing_size_row_indices, df, file_path, gui, save_rows=False
        )
        finish_size_determination_log(log_stats)
        batches = pack_designs(
            designs, gui.canvas_width_mm, gui.canvas_height_mm, gui.mm_to_pixel, gui.design_padding
        )
        all_designs = []
        for batch in batches:
            all_designs.extend(batch)
        return all_designs, batches, missing_size_row_indices

    except Exception as e:
        try:
            finish_size_determination_log()
        except Exception:
            pass
        import traceback

        traceback.print_exc()
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        content = "Error Processing File\n"
        content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
        content += f"Error: {e}\n"
        content += f"\n{'='*80}\n"
        content += f"Full Traceback:\n{error_traceback}\n"
        save_error_to_file(content, "error")
        return [], [], []
