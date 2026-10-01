from __future__ import annotations

import re
import sys
from pathlib import Path

from pipeline_generate_packing_list_pdf.core_helpers import (
    PROCESS_ITEM_RE as _PROCESS_ITEM_RE,
    parse_process_and_item_impl,
    safe_str_impl,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

UNMATCHED_ROOT_DIR = wh.packing_runtime_dir() / "Unmatched SKU Files"
MISSING_LOGO_ROOT_DIR = wh.packing_missing_logo_dir()
DATA_DIR = wh.packing_data_dir()
ALL_ORDERS_PATH = wh.packing_all_orders_path()

_FILENAME_UNSAFE = re.compile(r'[<>:"/\\|?*]')


def _sanitize_process_for_filename(name: str) -> str:
    """Return a safe filename segment (no path/Windows-unsafe chars)."""
    if not name:
        return "process"
    return _FILENAME_UNSAFE.sub("_", name.strip()).strip("_") or "process"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_process_and_item(val):
    return parse_process_and_item_impl(val, safe_str=safe_str_impl, process_item_re=_PROCESS_ITEM_RE)


def _shift_subdir_name(shift_label: str) -> str:
    return (
        f"{shift_label} Shift"
        if shift_label and " Shift" not in shift_label
        else (shift_label or "Shift")
    )


def _path_display(p: Path | str | None) -> str:
    if p is None or (isinstance(p, str) and not p.strip()):
        return "(not set)"
    try:
        q = Path(p)
        return str(q.resolve())
    except OSError:
        return str(p)
