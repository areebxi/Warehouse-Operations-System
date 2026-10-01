from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from pipeline_generate_packing_list_pdf.reporting_counts import build_order_counts_impl
from pipeline_generate_packing_list_pdf.reporting_match_apparel import (
    collect_apparel_row_detail,
)
from pipeline_generate_packing_list_pdf.reporting_match_logo import collect_logo_row_detail


def collect_image_match_details_impl(
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
    apparel_list: List[Dict[str, Any]] = []
    logo_list: List[Dict[str, Any]] = []
    has_apparel_lookup = apparel_stem_map is not None or (apparel_image_dir and apparel_image_dir.is_dir())
    has_logo_lookup = (
        logo_normal_stem_map is not None
        or logo_custom_stem_map is not None
        or (logo_normal_dir and logo_normal_dir.is_dir())
        or (logo_customise_dir and logo_customise_dir.is_dir())
    )
    for i in range(len(df)):
        row = df.iloc[i]
        row_id = safe_str(row.get("Process and Item Number", "")) or f"row {i}"
        order_num = safe_str(row.get("Order Number", ""))
        item_sku = safe_str(row.get("Item SKU", ""))
        if has_apparel_lookup:
            detail = collect_apparel_row_detail(
                i=i,
                row=row,
                row_id=row_id,
                order_num=order_num,
                item_sku=item_sku,
                apparel_image_dir=apparel_image_dir,
                apparel_stem_map=apparel_stem_map,
                safe_str=safe_str,
                find_image=find_image,
            )
            if detail is not None:
                apparel_list.append(detail)
        if has_logo_lookup:
            tokens = logo_design_tokens(row.get("Logo/Design Image"))
            if tokens:
                logo_list.append(
                    collect_logo_row_detail(
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
                )
    return {"apparel": apparel_list, "logo": logo_list}
