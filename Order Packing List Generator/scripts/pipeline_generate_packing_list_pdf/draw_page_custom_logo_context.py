from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.back_print_hint import FBPI_SIDE_SUFFIX_LOOKUP


def resolve_custom_logo_context_impl(
    row_series,
    order_number_counts: dict,
    *,
    is_plain_order: bool,
    logo_customise_dir: Optional[Path],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    safe_str: Callable[..., str],
    logo_design_tokens: Callable[..., List[str]],
    find_image_custom_exact: Callable[..., Optional[Path]],
    find_image_custom_logo: Callable[..., Optional[Path]],
    find_image_custom_fbpi: Callable[..., Optional[Path]],
) -> Tuple[bool, bool, Optional[Path], List[Tuple[Path, str]]]:
    is_customised = safe_str(row_series.get("Customise", "")).lower() == "yes"
    base_order_for_scope = safe_str(row_series.get("Order Number (Base)"))
    is_scoped_custom_merge = bool(
        is_customised
        and base_order_for_scope
        and order_number_counts.get(base_order_for_scope, 1) > 1
    )

    base_custom_path: Optional[Path] = None
    fbpi_slots: List[Tuple[Path, str]] = []
    if (not is_plain_order) and is_customised and (logo_customise_dir or logo_custom_stem_map is not None):
        item_sku_raw = safe_str(row_series.get("Item SKU", ""))
        item_sku = item_sku_raw.replace("/", "-") if item_sku_raw else ""
        logo_tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
        base_name = logo_tokens[0] if logo_tokens else ""
        if base_name:
            if is_scoped_custom_merge:
                base_candidates: List[str] = []
                if item_sku:
                    base_candidates.append(f"{base_name}-{item_sku}")
                base_candidates.append(base_name)
                for candidate in base_candidates:
                    base_custom_path = find_image_custom_exact(
                        logo_customise_dir, candidate, logo_custom_stem_map, recursive=True
                    )
                    if base_custom_path is not None:
                        break
                for suffix, label in FBPI_SIDE_SUFFIX_LOOKUP:
                    side_candidates: List[str] = []
                    if item_sku:
                        side_candidates.append(f"{base_name}-{suffix}-{item_sku}")
                    side_candidates.append(f"{base_name}-{suffix}")
                    p = None
                    for candidate_stem in side_candidates:
                        p = find_image_custom_exact(
                            logo_customise_dir, candidate_stem, logo_custom_stem_map, recursive=True
                        )
                        if p is not None:
                            break
                    if p is not None:
                        fbpi_slots.append((p, label))
            else:
                base_custom_path = find_image_custom_logo(
                    logo_customise_dir, base_name, logo_custom_stem_map, recursive=True
                )
                for suffix, label in FBPI_SIDE_SUFFIX_LOOKUP:
                    candidate_stem = f"{base_name}-{suffix}"
                    p = find_image_custom_fbpi(logo_custom_stem_map, candidate_stem)
                    if p is not None:
                        fbpi_slots.append((p, label))

    return is_customised, is_scoped_custom_merge, base_custom_path, fbpi_slots
