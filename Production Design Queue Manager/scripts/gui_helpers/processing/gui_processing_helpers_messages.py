"""Message and size-tracking helpers for processing flows."""

import os
from typing import List, Dict, Any, Optional
from tkinter import messagebox


def create_design_log_entry(design_key: str, design_type: str, design_data: Dict[str, Any], item_sku: Optional[str] = None) -> str:
    log_entry = f"\n{'='*80}\n"
    log_entry += "DESIGN\n"
    log_entry += f"{'='*80}\n"
    log_entry += f"Design Type:     {design_type}\n"
    # Personalised/missing-logo pass order_number as design_key with item_sku set.
    # Standard mode passes SKU as design_key without a separate item_sku.
    if item_sku:
        log_entry += f"Order Number:    {design_key}\n"
        log_entry += f"Item SKU:        {item_sku}\n"
    else:
        log_entry += f"Item SKU:        {design_key}\n"
        log_entry += "Order Number:    N/A\n"
    log_entry += (
        f"Original Size:   {design_data.get('width', 0)}px × "
        f"{design_data.get('height', 0)}px\n"
    )
    size_code = design_data.get('size_code', 'N/A')
    size_info = design_data.get('size_info') or {}
    match_type = size_info.get('match_type', 'N/A')
    width_src = size_info.get('width_col_name') or 'N/A'
    height_src = size_info.get('height_col_name') or 'N/A'
    merge_entry = size_info.get('merge_entry') or size_code
    ref_width_mm = size_info.get('width_mm')
    ref_height_mm = size_info.get('height_mm')
    ref_width_px = size_info.get('width_px')
    ref_height_px = size_info.get('height_px')
    if size_info:
        log_entry += f"Size Reference:  {merge_entry}\n"
        log_entry += f"  Size Code:     {size_code}\n"
        log_entry += f"  Match Type:    {match_type}\n"
        log_entry += f"  Width Column:  {width_src}\n"
        log_entry += f"  Height Column: {height_src}\n"
        if ref_width_mm is not None and ref_height_mm is not None and ref_width_px is not None and ref_height_px is not None:
            log_entry += (
                f"  Reference:     {ref_width_mm:.2f}mm × {ref_height_mm:.2f}mm "
                f"({int(ref_width_px)}px × {int(ref_height_px)}px)\n"
            )
        if size_info.get("a3_landscape_applied"):
            log_entry += (
                "  Note:          A3 landscape applied "
                "(rotated 90°; size box swapped; IronOn auto-orientation skipped)\n"
            )
    else:
        log_entry += "Size Reference:  N/A (no match — used original image size)\n"
        log_entry += f"  Size Code:     {size_code}\n"
    log_entry += (
        f"Final Size:      {design_data['width']}px × {design_data['height']}px "
        f"({design_data['width_mm']:.2f}mm × {design_data['height_mm']:.2f}mm)\n"
    )
    return log_entry


def track_missing_size_reference(df, column: str, key: str, missing_size_row_indices: List[int]) -> None:
    matching_rows = df[df[column] == key]
    if not matching_rows.empty:
        row_idx = matching_rows.index[0]
        if row_idx not in missing_size_row_indices:
            missing_size_row_indices.append(row_idx)


def track_missing_size_reference_multi(df, order_column: str, sku_column: str, order_number: str, item_sku: str, missing_size_row_indices: List[int]) -> None:
    matching_rows = df[(df[order_column] == order_number) & (df[sku_column] == item_sku)]
    if not matching_rows.empty:
        row_idx = matching_rows.index[0]
        if row_idx not in missing_size_row_indices:
            missing_size_row_indices.append(row_idx)


def format_missing_items_list(items: List[str], max_display: int = 20) -> str:
    if not items:
        return ""
    missing_list = ", ".join(str(s) for s in items[:max_display])
    if len(items) > max_display:
        missing_list += f" ... and {len(items) - max_display} more"
    return missing_list


def is_plainlg_sku(item_sku: object) -> bool:
    return item_sku is not None and "plainlg" in str(item_sku).lower()


def is_customise_yes(value: object) -> bool:
    return str(value).strip().lower() == "yes"


def handle_missing_designs_error(missing_items: List[str], file_path: Optional[str], mode: str = "standard") -> None:
    if not missing_items:
        messagebox.showerror("Error", f"No design files found in {os.path.basename(file_path) if file_path else 'file'}!\nPlease check your {'designs folder' if mode == 'standard' else 'single and double design folders'}.")
        return
    missing_list = format_missing_items_list(missing_items, 20)
    folder_text = "designs folder" if mode == "standard" else "single and double design folders"
    messagebox.showerror("Error", f"No design files found!\n\nMissing designs for {len(missing_items)} {'SKU(s)' if mode == 'standard' else 'Order Number(s)'} in {os.path.basename(file_path) if file_path else 'file'}:\n{missing_list}\n\nPlease check your {folder_text}.")


def handle_missing_designs_warning(missing_items: List[str], file_path: Optional[str], mode: str = "standard") -> None:
    if not missing_items:
        return
    missing_list = format_missing_items_list(missing_items, 10)
    item_type = "SKUs" if mode == "standard" else "Order Numbers"
    messagebox.showwarning("Warning", f"Could not find designs for {len(missing_items)} {item_type} in {os.path.basename(file_path) if file_path else 'file'}:\n{missing_list}")


def handle_missing_sizes_warning(
    missing_sizes: List[str],
    missing_size_row_indices: List[int],
    df,
    file_path: Optional[str],
    gui,
    save_rows: bool = True,
) -> None:
    if not missing_sizes:
        return
    try:
        saved_file = None
        if save_rows and missing_size_row_indices and hasattr(gui, 'save_missing_size_reference_rows'):
            try:
                saved_file = gui.save_missing_size_reference_rows(df, missing_size_row_indices, file_path)
            except Exception as e:
                print(f"Error saving missing size reference rows: {e}")
        missing_list = format_missing_items_list(missing_sizes, 10)
        warning_msg = (f"Could not find size reference for {len(missing_sizes)} designs in {os.path.basename(file_path) if file_path else 'file'}:\n{missing_list}\n\nUsing image dimensions instead.")
        if saved_file:
            warning_msg += f"\n\nRows with missing size references have been saved to:\n{saved_file}"
        messagebox.showwarning("Warning", warning_msg)
    except Exception:
        try:
            messagebox.showwarning("Warning", f"Could not find size reference for {len(missing_sizes)} designs. Using image dimensions instead.")
        except Exception:
            pass
