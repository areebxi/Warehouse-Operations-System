from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd

from pipeline_generate_packing_list_pdf.core_helpers import is_plain_order_sku_impl
from pipeline_generate_packing_list_pdf.reporting_counts import build_order_counts_impl


def count_image_lookup_stats_impl(
    df: pd.DataFrame,
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    *,
    apparel_image_dir: Optional[Path],
    logo_customise_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    safe_str: Callable[[object], str],
    logo_design_tokens: Callable[[object], list[str]],
    find_image: Callable[..., Optional[Path]],
    find_image_normal_logo: Callable[..., Optional[Path]],
    resolve_custom_logo_context: Any = None,
    logo_image_for_slot: Any = None,
    find_image_custom_exact: Any = None,
    find_image_custom_logo: Any = None,
    find_image_custom_fbpi: Any = None,
) -> dict:
    order_number_counts = build_order_counts_impl(df, safe_str=safe_str)
    apparel_found = apparel_total = logo_found = logo_total = 0
    has_apparel_lookup = apparel_stem_map is not None or (apparel_image_dir and apparel_image_dir.is_dir())
    has_logo_lookup = (
        logo_normal_stem_map is not None
        or logo_custom_stem_map is not None
        or (logo_normal_dir and logo_normal_dir.is_dir())
        or (logo_customise_dir and logo_customise_dir.is_dir())
    )
    for i in range(len(df)):
        row = df.iloc[i]
        if has_apparel_lookup:
            apparel_text = safe_str(row.get("Apparel Image", ""))
            picture_name = safe_str(row.get("Picture Name", ""))
            if apparel_text or picture_name:
                apparel_total += 1
                for name in (apparel_text, picture_name):
                    if not name:
                        continue
                    if find_image(apparel_image_dir, name, apparel_stem_map, recursive=False):
                        apparel_found += 1
                        break
        if has_logo_lookup:
            tokens = logo_design_tokens(row.get("Logo/Design Image"))
            if tokens:
                logo_total += 1
                is_customised = safe_str(row.get("Customise", "")).lower() == "yes"
                if is_customised:
                    item_sku_raw = safe_str(row.get("Item SKU", ""))
                    if is_plain_order_sku_impl(item_sku_raw):
                        continue
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
                        p0 = logo_image_for_slot(
                            0,
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
                        if p0 is not None:
                            logo_found += 1
                    else:
                        order_val = safe_str(row.get("Order Number", ""))
                        if order_val:
                            first_idx = order_number_counts.get(("__first__", order_val))
                            rank = (i - first_idx + 1) if first_idx is not None else 1
                            base_name = order_val if rank == 1 else f"{order_val}-{rank - 1}"
                            if find_image(logo_customise_dir, base_name, logo_custom_stem_map, recursive=True):
                                logo_found += 1
                else:
                    all_tokens_ok = True
                    for tok in tokens:
                        if not find_image_normal_logo(
                            logo_normal_dir, tok, logo_normal_stem_map, recursive=False
                        ):
                            all_tokens_ok = False
                            break
                    if all_tokens_ok:
                        logo_found += 1
    return {
        "apparel_found": apparel_found,
        "apparel_total": apparel_total,
        "logo_found": logo_found,
        "logo_total": logo_total,
    }

