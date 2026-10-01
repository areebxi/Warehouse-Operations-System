from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pipeline_generate_packing_list_pdf.core_helpers import is_plain_order_sku_impl
from pipeline_generate_packing_list_pdf.reporting_lookup_source import (
    _custom_pdf_slot_token_label,
    _lookup_source_custom_logo,
)


def collect_custom_logo_detail(
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
    resolve_custom_logo_context: Any,
    logo_image_for_slot: Any,
    find_image_custom_exact: Any,
    find_image_custom_logo: Any,
    find_image_custom_fbpi: Any,
) -> Dict[str, Any]:
    item_sku_raw = safe_str(row.get("Item SKU", ""))
    token_list = list(tokens)
    custom_logo_root = str(logo_customise_dir.resolve()) if logo_customise_dir else "(not set)"
    normal_logo_root = str(logo_normal_dir.resolve()) if logo_normal_dir else "(not set)"
    base_logo_dict: Dict[str, Any] = {
        "row_index": i,
        "process_and_item": row_id,
        "order_number": order_num,
        "item_sku": item_sku,
        "customise": "Yes",
        "logo_design_raw": safe_str(row.get("Logo/Design Image", "")),
        "tokens": token_list,
        "mode": "custom",
        "custom_logo_root": custom_logo_root,
        "normal_logo_root": normal_logo_root,
    }
    if is_plain_order_sku_impl(item_sku_raw):
        return {
            **base_logo_dict,
            "pdf_plain_order": True,
            "attempts": [
                {
                    "field": "PDF logo drawing",
                    "token": "plain/plainlg in Item SKU",
                    "path": None,
                    "source": "pdf_skips_logo_images_same_as_draw_page",
                }
            ],
            "resolved_path": None,
        }

    pdf_custom_deps_ok = (
        resolve_custom_logo_context is not None
        and logo_image_for_slot is not None
        and find_image_custom_exact is not None
        and find_image_custom_logo is not None
        and find_image_custom_fbpi is not None
    )
    if pdf_custom_deps_ok:
        is_plain_order = is_plain_order_sku_impl(item_sku_raw)
        _ic, is_scoped, base_custom_path, fbpi_slots = resolve_custom_logo_context(
            row,
            order_number_counts,
            is_plain_order=is_plain_order,
            logo_customise_dir=logo_customise_dir,
            logo_custom_stem_map=logo_custom_stem_map,
            safe_str=safe_str,
            logo_design_tokens=logo_design_tokens,
            find_image_custom_exact=find_image_custom_exact,
            find_image_custom_logo=find_image_custom_logo,
            find_image_custom_fbpi=find_image_custom_fbpi,
        )
        attempts_pdf: List[Dict[str, Any]] = [
            {
                "field": "PDF resolve_custom_logo_context",
                "token": (
                    f"scoped_merge={is_scoped} "
                    f"fbpi_slots={len(fbpi_slots)} "
                    f"base_path_set={base_custom_path is not None}"
                ),
                "path": base_custom_path,
                "source": "pdf_engine_same_as_draw",
            }
        ]
        primary_slot_path: Optional[Path] = None
        for slot in range(5):
            p_slot = logo_image_for_slot(
                slot,
                row,
                fbpi_slots=fbpi_slots,
                base_custom_path=base_custom_path,
                is_scoped_custom_merge=is_scoped,
                logo_customise_dir=logo_customise_dir,
                logo_custom_stem_map=logo_custom_stem_map,
                logo_normal_dir=logo_normal_dir,
                logo_normal_stem_map=logo_normal_stem_map,
                safe_str=safe_str,
                logo_design_tokens=logo_design_tokens,
                find_image_custom_exact=find_image_custom_exact,
                find_image_custom_logo=find_image_custom_logo,
                find_image_normal_logo=find_image_normal_logo,
            )
            if slot == 0:
                primary_slot_path = p_slot
            attempts_pdf.append(
                {
                    "field": f"PDF logo slot {slot}",
                    "token": _custom_pdf_slot_token_label(slot, token_list, fbpi_slots),
                    "path": p_slot,
                    "source": "pdf_engine_same_as_draw",
                }
            )
        return {
            **base_logo_dict,
            "pdf_aligned_custom": True,
            "custom_scoped_merge": is_scoped,
            "attempts": attempts_pdf,
            "resolved_path": primary_slot_path,
        }

    order_val = safe_str(row.get("Order Number", ""))
    if not order_val:
        return {**base_logo_dict, "attempts": [], "resolved_path": None}
    first_idx = order_number_counts.get(("__first__", order_val))
    rank = (i - first_idx + 1) if first_idx is not None else 1
    base_name = order_val if rank == 1 else f"{order_val}-{rank - 1}"
    p = find_image(logo_customise_dir, base_name, logo_custom_stem_map, recursive=True)
    src = _lookup_source_custom_logo(base_name, p, logo_custom_stem_map)
    return {
        **base_logo_dict,
        "order_number": order_val,
        "custom_rank": rank,
        "custom_lookup_token": base_name,
        "attempts": [
            {
                "field": "Logo/Design customise (Order Number token)",
                "token": base_name,
                "path": p,
                "source": src,
            }
        ],
        "resolved_path": p,
    }
