"""Missing Run GUI: config load/save."""

from __future__ import annotations

import json
import sys
from tkinter import BooleanVar, StringVar

from .core import (
    CONFIG_DIR,
    DEFAULT_MISSING_TYPE,
    MISSING_PDF_SUBDIRS,
    MISSING_RUN_CONFIG,
    PROJECT_ROOT,
)


def load_missing_run_config(
    *,
    shift_var: StringVar,
    process_name_var: StringVar,
    missing_type_var: StringVar,
    missing_input_var: StringVar,
    all_orders_var: StringVar,
    apparel_dir_var: StringVar,
    logo_custom_single_dir_var: StringVar,
    logo_custom_double_dir_var: StringVar,
    logo_normal_dir_var: StringVar,
    pdf_copy_dir_var: StringVar,
    excel_copy_dir_var: StringVar,
    use_demo_images_var: BooleanVar,
) -> None:
    data = None
    for path in (MISSING_RUN_CONFIG, PROJECT_ROOT / "missing_run_config.json"):
        if not path.is_file():
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
                break
        except Exception:
            continue
    if data is None:
        return
    # ponytail: never restore date — always open as today (field stays editable)
    shift_var.set(str(data.get("shift", "")).strip())
    process_name_var.set(str(data.get("process_name", "")).strip())
    missing_type = str(data.get("missing_type", "")).strip()
    if missing_type in MISSING_PDF_SUBDIRS:
        missing_type_var.set(missing_type)
    for key, var in [
        ("missing_input", missing_input_var),
        ("all_orders", all_orders_var),
        ("apparel_dir", apparel_dir_var),
        ("logo_custom_single_dir", logo_custom_single_dir_var),
        ("logo_custom_double_dir", logo_custom_double_dir_var),
        ("logo_normal_dir", logo_normal_dir_var),
        ("pdf_copy_dir", pdf_copy_dir_var),
        ("excel_copy_dir", excel_copy_dir_var),
    ]:
        val = str(data.get(key, "")).strip()
        if val:
            var.set(val)
    if isinstance(data.get("use_demo_images"), bool):
        use_demo_images_var.set(data["use_demo_images"])
    legacy_logo_custom = str(data.get("logo_custom_dir", "")).strip()
    if not logo_custom_single_dir_var.get() and legacy_logo_custom:
        logo_custom_single_dir_var.set(legacy_logo_custom)


def save_missing_run_config(
    *,
    date_var: StringVar,
    shift_var: StringVar,
    process_name_var: StringVar,
    missing_type_var: StringVar,
    missing_input_var: StringVar,
    all_orders_var: StringVar,
    apparel_dir_var: StringVar,
    logo_custom_single_dir_var: StringVar,
    logo_custom_double_dir_var: StringVar,
    logo_normal_dir_var: StringVar,
    pdf_copy_dir_var: StringVar,
    excel_copy_dir_var: StringVar,
    use_demo_images_var: BooleanVar,
) -> None:
    data = {
        "date": date_var.get().strip(),
        "shift": shift_var.get().strip(),
        "process_name": process_name_var.get().strip(),
        "missing_type": missing_type_var.get().strip() or DEFAULT_MISSING_TYPE,
        "missing_input": missing_input_var.get().strip(),
        "all_orders": all_orders_var.get().strip(),
        "apparel_dir": (apparel_dir_var.get() or "").strip(),
        "logo_custom_single_dir": (logo_custom_single_dir_var.get() or "").strip(),
        "logo_custom_double_dir": (logo_custom_double_dir_var.get() or "").strip(),
        "logo_normal_dir": (logo_normal_dir_var.get() or "").strip(),
        "pdf_copy_dir": (pdf_copy_dir_var.get() or "").strip(),
        "excel_copy_dir": (excel_copy_dir_var.get() or "").strip(),
        "use_demo_images": use_demo_images_var.get(),
    }
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        MISSING_RUN_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        print(
            f"[missing run] config save failed ({MISSING_RUN_CONFIG}): {exc}",
            file=sys.stderr,
            flush=True,
        )
