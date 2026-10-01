from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pipeline_generate_packing_list_pdf.reporting_lookup_source import (
    _lookup_source_normal_logo,
)
from pipeline_generate_packing_list_pdf.reporting_match_logo_custom import (
    collect_custom_logo_detail,
)


def collect_logo_row_detail(
    *,
    i: int,
    row,
    row_id: str,
    order_num: str,
    item_sku: str,
    tokens: list[str],
    order_number_counts: dict,
    logo_customise_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    safe_str: Callable[[object], str],
    logo_design_tokens: Callable[[object], list[str]],
    find_image: Callable[..., Optional[Path]],
    find_image_normal_logo: Callable[..., Optional[Path]],
    resolve_custom_logo_context: Any = None,
    logo_image_for_slot: Any = None,
    find_image_custom_exact: Any = None,
    find_image_custom_logo: Any = None,
    find_image_custom_fbpi: Any = None,
) -> Dict[str, Any]:
    is_customised = safe_str(row.get("Customise", "")).lower() == "yes"
    if is_customised:
        return collect_custom_logo_detail(
            i=i,
            row=row,
            row_id=row_id,
            order_num=order_num,
            item_sku=item_sku,
            tokens=tokens,
            order_number_counts=order_number_counts,
            logo_customise_dir=logo_customise_dir,
            logo_normal_dir=logo_normal_dir,
            logo_custom_stem_map=logo_custom_stem_map,
            logo_normal_stem_map=logo_normal_stem_map,
            safe_str=safe_str,
            logo_design_tokens=logo_design_tokens,
            find_image=find_image,
            find_image_normal_logo=find_image_normal_logo,
            resolve_custom_logo_context=resolve_custom_logo_context,
            logo_image_for_slot=logo_image_for_slot,
            find_image_custom_exact=find_image_custom_exact,
            find_image_custom_logo=find_image_custom_logo,
            find_image_custom_fbpi=find_image_custom_fbpi,
        )
    attempts: List[Dict[str, Any]] = []
    primary_path: Optional[Path] = None
    for ti, tok in enumerate(tokens):
        p = find_image_normal_logo(logo_normal_dir, tok, logo_normal_stem_map, recursive=False)
        src = _lookup_source_normal_logo(tok, p, logo_normal_stem_map)
        attempts.append(
            {
                "field": f"Logo/Design normal (token {ti + 1}/{len(tokens)})",
                "token": tok,
                "path": p,
                "source": src,
            }
        )
        if ti == 0:
            primary_path = p
    return {
        "row_index": i,
        "process_and_item": row_id,
        "order_number": order_num,
        "item_sku": item_sku,
        "customise": "No",
        "logo_design_raw": safe_str(row.get("Logo/Design Image", "")),
        "tokens": list(tokens),
        "mode": "normal",
        "custom_logo_root": str(logo_customise_dir.resolve()) if logo_customise_dir else "(not set)",
        "normal_logo_root": str(logo_normal_dir.resolve()) if logo_normal_dir else "(not set)",
        "attempts": attempts,
        "resolved_path": primary_path,
    }
