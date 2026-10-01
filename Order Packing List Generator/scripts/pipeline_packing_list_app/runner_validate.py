from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from pipeline_runtime.runner_utils import _FILENAME_UNSAFE
from pipeline_shipstation.tags_process_lookup import resolve_tag_list_processes

from .config import DEFAULT_CL_CSV


def get_input_paths(app) -> list[Path]:
    paths = getattr(app, "input_paths", None)
    if isinstance(paths, list):
        return list(paths)
    raw = (app.input_csv_var.get() or "").strip()
    return [Path(p.strip()) for p in raw.split(";") if p.strip()] if raw else []


def resolve_cl_csv_path(app) -> Path:
    var = getattr(app, "cl_csv_var", None)
    text = str(var.get() if var is not None else "").strip()
    return Path(text) if text else Path(DEFAULT_CL_CSV)


def validate_image_folders(app) -> bool:
    """Require any non-empty image folder path to be an existing directory."""
    folders = (
        ("Apparel Image folder", app.apparel_dir_var.get()),
        ("Normal Design folder", app.logo_normal_dir_var.get()),
        ("Customise Single Position Design folder", app.logo_custom_single_dir_var.get()),
        ("Customise Double Position Design folder", app.logo_custom_double_dir_var.get()),
    )
    for label, raw in folders:
        path_str = (raw or "").strip()
        if not path_str:
            continue
        if not Path(path_str).is_dir():
            messagebox.showerror("Error", f"{label} is not a valid directory:\n{path_str}")
            return False
    return True


def resolve_selected_tag_processes(app) -> list[tuple[int, str, str]] | None:
    """
    Resolve process numbers for all selected tags.

    Returns None (and shows a messagebox) on failure.
    On success for a single tag with blank GUI, fills the process field from the sheet.
    """
    tags = (
        app.selected_shipstation_tags()
        if hasattr(app, "selected_shipstation_tags")
        else ([app.selected_shipstation_tag()] if app.selected_shipstation_tag() else [])
    )
    tags = [t for t in tags if t]
    multi = len(tags) > 1
    gui_value = "" if multi else (app.fixed_process_number_var.get() or "").strip()
    resolved, err = resolve_tag_list_processes(
        tags,
        shift_label=(app.shift_var.get() or "").strip(),
        gui_value=gui_value,
    )
    if err:
        messagebox.showerror("Error", err)
        return None
    for _tag_id, _tag_name, process_name in resolved:
        if _FILENAME_UNSAFE.search(process_name):
            messagebox.showerror(
                "Error", 'Fixed process number cannot contain / \\ : * ? " < > |'
            )
            return None
    if len(resolved) == 1 and not gui_value:
        app.fixed_process_number_var.set(resolved[0][2])
    return resolved


def validate_tag_mode(app) -> bool:
    """Validate date/shift/tag/process for ShipStation tag fetch."""
    tags = (
        app.selected_shipstation_tags()
        if hasattr(app, "selected_shipstation_tags")
        else ([app.selected_shipstation_tag()] if app.selected_shipstation_tag() else [])
    )
    tags = [t for t in tags if t]
    if not tags:
        messagebox.showerror("Error", "Please select at least one ShipStation tag.")
        return False
    try:
        datetime.strptime(app.date_var.get().strip(), "%d-%m-%Y")
    except Exception:
        messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
        return False
    shift = (app.shift_var.get() or "").strip()
    if not shift:
        messagebox.showerror("Error", "Please select a shift.")
        return False
    if resolve_selected_tag_processes(app) is None:
        return False
    workbook = Path(app.workbook_var.get())
    if not workbook.is_file():
        messagebox.showerror("Error", f"Workbook not found: {workbook}")
        return False
    cl_csv = resolve_cl_csv_path(app)
    if not cl_csv.is_file():
        messagebox.showerror("Error", f"Custom Label Database CSV not found: {cl_csv}")
        return False
    if not validate_image_folders(app):
        return False
    return True


def validate_inputs(app) -> bool:
    if hasattr(app, "is_tag_mode") and app.is_tag_mode():
        return validate_tag_mode(app)
    paths = get_input_paths(app)
    if not paths or any(not p.is_file() for p in paths):
        messagebox.showerror(
            "Error",
            "Please select an Input CSV file (or switch Input source to ShipStation tag).",
        )
        return False
    try:
        datetime.strptime(app.date_var.get().strip(), "%d-%m-%Y")
    except Exception:
        messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
        return False
    if not app.shift_var.get():
        messagebox.showerror("Error", "Please select a shift.")
        return False
    workbook = Path(app.workbook_var.get())
    if not workbook.is_file():
        messagebox.showerror("Error", f"Workbook not found: {workbook}")
        return False
    cl_csv = resolve_cl_csv_path(app)
    if not cl_csv.is_file():
        messagebox.showerror("Error", f"Custom Label Database CSV not found: {cl_csv}")
        return False
    if not validate_image_folders(app):
        return False
    return True
