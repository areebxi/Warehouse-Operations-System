"""Per-chunk missing logo/apparel checks for preflight dry-run."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from pipeline_generate_packing_list_pdf.core_helpers import (
    is_plain_order_sku_impl,
    logo_design_tokens_impl,
    safe_str_impl,
)
from pipeline_generate_packing_list_pdf.draw_page_custom_logo_context import (
    resolve_custom_logo_context_impl,
)
from pipeline_generate_packing_list_pdf.draw_page_logo_lookup import (
    logo_image_for_slot_impl,
)

_safe_str = safe_str_impl
_logo_design_tokens = partial(logo_design_tokens_impl, safe_str=_safe_str)

def _flag_chunk(
    df_chunk: pd.DataFrame,
    *,
    has_apparel_lookup: bool,
    has_logo_lookup: bool,
    order_number_counts: dict,
    apparel_image_dir: Optional[Path],
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_normal_dir: Optional[Path],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    find_apparel,
    find_normal,
    find_custom_exact,
    find_custom_logo,
    find_custom_fbpi,
) -> Tuple[List[object], List[object]]:
    missing_logo_idxs: List[object] = []
    missing_apparel_idxs: List[object] = []
    logo_customise_dir = None

    for i in range(len(df_chunk)):
        row = df_chunk.iloc[i]
        idx = df_chunk.index[i]
        if has_apparel_lookup:
            apparel_text = _safe_str(row.get("Apparel Image", ""))
            picture_name = _safe_str(row.get("Picture Name", ""))
            if apparel_text or picture_name:
                found = False
                for name in (apparel_text, picture_name):
                    if not name:
                        continue
                    if find_apparel(apparel_image_dir, name, apparel_stem_map, recursive=False):
                        found = True
                        break
                if not found:
                    missing_apparel_idxs.append(idx)

        if not has_logo_lookup:
            continue
        tokens = _logo_design_tokens(row.get("Logo/Design Image"))
        if not tokens:
            continue
        is_customised = _safe_str(row.get("Customise", "")).lower() == "yes"
        item_sku_raw = _safe_str(row.get("Item SKU", ""))
        if is_plain_order_sku_impl(item_sku_raw):
            continue
        if is_customised:
            _ic, is_scoped, base_custom_path, fbpi_slots = resolve_custom_logo_context_impl(
                row,
                order_number_counts,
                is_plain_order=False,
                logo_customise_dir=logo_customise_dir,
                logo_custom_stem_map=logo_custom_stem_map,
                safe_str=_safe_str,
                logo_design_tokens=_logo_design_tokens,
                find_image_custom_exact=find_custom_exact,
                find_image_custom_logo=find_custom_logo,
                find_image_custom_fbpi=find_custom_fbpi,
            )
            p0 = logo_image_for_slot_impl(
                0,
                row,
                fbpi_slots=fbpi_slots,
                base_custom_path=base_custom_path,
                is_scoped_custom_merge=is_scoped,
                logo_customise_dir=logo_customise_dir,
                logo_custom_stem_map=logo_custom_stem_map,
                logo_normal_dir=logo_normal_dir,
                logo_normal_stem_map=logo_normal_stem_map,
                safe_str=_safe_str,
                logo_design_tokens=_logo_design_tokens,
                find_image_custom_exact=find_custom_exact,
                find_image_custom_logo=find_custom_logo,
                find_image_normal_logo=find_normal,
            )
            if p0 is None:
                missing_logo_idxs.append(idx)
        else:
            all_ok = True
            for tok in tokens:
                if not find_normal(logo_normal_dir, tok, logo_normal_stem_map, recursive=False):
                    all_ok = False
                    break
            if not all_ok:
                missing_logo_idxs.append(idx)

    return missing_logo_idxs, missing_apparel_idxs
