from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pipeline_generate_packing_list_pdf.reporting_lookup_source import (
    _lookup_source_apparel,
)


def collect_apparel_row_detail(
    *,
    i: int,
    row,
    row_id: str,
    order_num: str,
    item_sku: str,
    apparel_image_dir: Optional[Path],
    apparel_stem_map: Optional[Dict[str, Path]],
    safe_str: Callable[[object], str],
    find_image: Callable[..., Optional[Path]],
) -> Optional[Dict[str, Any]]:
    apparel_text = safe_str(row.get("Apparel Image", ""))
    picture_name = safe_str(row.get("Picture Name", ""))
    if not (apparel_text or picture_name):
        return None
    attempts: List[Dict[str, Any]] = []
    path_found: Optional[Path] = None
    chosen_field = ""
    chosen_token = ""
    for field_label, name in (
        ("Apparel Image column", apparel_text),
        ("Picture Name column", picture_name),
    ):
        if not name:
            continue
        p = find_image(apparel_image_dir, name, apparel_stem_map, recursive=False)
        src = _lookup_source_apparel(name, p, apparel_stem_map)
        attempts.append({"field": field_label, "token": name, "path": p, "source": src})
        if p is not None:
            path_found = p
            chosen_field = field_label
            chosen_token = name
            break
    return {
        "row_index": i,
        "process_and_item": row_id,
        "order_number": order_num,
        "item_sku": item_sku,
        "apparel_image_value": apparel_text,
        "picture_name_value": picture_name,
        "apparel_search_root": str(apparel_image_dir.resolve()) if apparel_image_dir else "(not set)",
        "attempts": attempts,
        "chosen_field": chosen_field,
        "chosen_token": chosen_token,
        "resolved_path": path_found,
    }
