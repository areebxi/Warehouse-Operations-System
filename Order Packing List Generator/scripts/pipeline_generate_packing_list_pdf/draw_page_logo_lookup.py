from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


def logo_image_for_slot_impl(
    slot_index: int,
    row_series,
    *,
    fbpi_slots: List[Tuple[Path, str]],
    base_custom_path: Optional[Path],
    is_scoped_custom_merge: bool,
    logo_customise_dir: Optional[Path],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    logo_normal_dir: Optional[Path],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    safe_str: Callable[..., str],
    logo_design_tokens: Callable[..., List[str]],
    find_image_custom_exact: Callable[..., Optional[Path]],
    find_image_custom_logo: Callable[..., Optional[Path]],
    find_image_normal_logo: Callable[..., Optional[Path]],
) -> Optional[Path]:
    is_customised_local = safe_str(row_series.get("Customise", "")).lower() == "yes"
    if is_customised_local:
        if fbpi_slots:
            if slot_index == 0:
                return base_custom_path
            fbpi_index = slot_index - 1
            if 0 <= fbpi_index < len(fbpi_slots):
                path, _label = fbpi_slots[fbpi_index]
                return path
            return None
        tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
        if slot_index >= len(tokens):
            return None
        if not logo_customise_dir and logo_custom_stem_map is None:
            return None
        token = tokens[slot_index]
        if is_scoped_custom_merge:
            item_sku_local_raw = safe_str(row_series.get("Item SKU", ""))
            item_sku_local = item_sku_local_raw.replace("/", "-") if item_sku_local_raw else ""
            custom_candidates: List[str] = []
            if item_sku_local:
                custom_candidates.append(f"{token}-{item_sku_local}")
            custom_candidates.append(token)
            for candidate in custom_candidates:
                matched = find_image_custom_exact(
                    logo_customise_dir, candidate, logo_custom_stem_map, recursive=True
                )
                if matched is not None:
                    return matched
            return None
        return find_image_custom_logo(
            logo_customise_dir, token, logo_custom_stem_map, recursive=True
        )
    if not logo_normal_dir and logo_normal_stem_map is None:
        return None
    tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    if slot_index >= len(tokens):
        return None
    token = tokens[slot_index]
    return find_image_normal_logo(logo_normal_dir, token, logo_normal_stem_map, recursive=False)
