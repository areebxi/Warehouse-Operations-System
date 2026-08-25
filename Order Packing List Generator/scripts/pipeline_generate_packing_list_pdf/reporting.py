from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.core_helpers import is_plain_order_sku_impl


def _lookup_source_apparel(name: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    """Explain how find_image resolved (or failed) for apparel."""
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(name) == p:
            return "indexed_stem_map_exact"
        lower = name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower and path == p:
                return "indexed_stem_map_case_insensitive"
    return "filesystem_top_level_scan"


def _lookup_source_custom_logo(name: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(name) == p:
            return "indexed_stem_map_exact"
        lower = name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower and path == p:
                return "indexed_stem_map_case_insensitive"
    return "filesystem_recursive_scan"


def _lookup_source_normal_logo(token: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(token) == p:
            return "indexed_stem_map_exact_token"
        for stem, path in stem_map.items():
            if path == p and stem.startswith(token):
                return f"indexed_stem_map_prefix_match (matched stem={stem!r})"
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if path == p and stem.lower().startswith(token_lower):
                return f"indexed_stem_map_prefix_match_ci (matched stem={stem!r})"
    return "filesystem_prefix_scan"


def _custom_pdf_slot_token_label(
    slot: int,
    tokens: List[str],
    fbpi_slots: List[Tuple[Path, str]],
) -> str:
    """Human-readable token label for PDF customise slot trace (slot 0..4)."""
    if fbpi_slots:
        if slot == 0:
            return tokens[0] if tokens else "base"
        if 1 <= slot <= len(fbpi_slots):
            return f"{tokens[0]}-{fbpi_slots[slot - 1][1]} (fbpi)" if tokens else fbpi_slots[slot - 1][1]
        return f"slot {slot} (no fbpi pair)"
    if slot < len(tokens):
        return tokens[slot]
    return f"slot {slot}"


def build_order_counts_impl(
    df: pd.DataFrame,
    *,
    safe_str: Callable[[object], str],
) -> dict:
    counts: dict = {}
    first_idx: dict = {}
    base_series = df.get("Order Number (Base)")
    order_series = df.get("Order Number", pd.Series(dtype=object))
    for idx, on in order_series.items():
        base_val = ""
        if base_series is not None:
            try:
                base_val = safe_str(base_series.iloc[idx])
            except Exception:
                base_val = ""
        key = base_val or safe_str(on)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
        if key not in first_idx:
            first_idx[key] = idx
    for key, idx in first_idx.items():
        counts[("__first__", key)] = idx
    return counts


def build_process_totals_impl(
    df: pd.DataFrame,
    *,
    parse_process_and_item: Callable[[object], Tuple[Optional[str], Optional[str]]],
) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    col = df.get("Process and Item Number")
    if col is None:
        return totals
    for val in col:
        process_id, _item = parse_process_and_item(val)
        if not process_id:
            continue
        totals[process_id] = totals.get(process_id, 0) + 1
    return totals


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
            apparel_text = safe_str(row.get("Apparel Image", ""))
            picture_name = safe_str(row.get("Picture Name", ""))
            if apparel_text or picture_name:
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
                    attempts.append(
                        {
                            "field": field_label,
                            "token": name,
                            "path": p,
                            "source": src,
                        }
                    )
                    if p is not None:
                        path_found = p
                        chosen_field = field_label
                        chosen_token = name
                        break
                apparel_list.append(
                    {
                        "row_index": i,
                        "process_and_item": row_id,
                        "order_number": order_num,
                        "item_sku": item_sku,
                        "apparel_image_value": apparel_text,
                        "picture_name_value": picture_name,
                        "apparel_search_root": str(apparel_image_dir.resolve())
                        if apparel_image_dir
                        else "(not set)",
                        "attempts": attempts,
                        "chosen_field": chosen_field,
                        "chosen_token": chosen_token,
                        "resolved_path": path_found,
                    }
                )
        if has_logo_lookup:
            tokens = logo_design_tokens(row.get("Logo/Design Image"))
            if tokens:
                is_customised = safe_str(row.get("Customise", "")).lower() == "yes"
                if is_customised:
                    item_sku_raw = safe_str(row.get("Item SKU", ""))
                    token_list = list(tokens)
                    custom_logo_root = (
                        str(logo_customise_dir.resolve()) if logo_customise_dir else "(not set)"
                    )
                    normal_logo_root = (
                        str(logo_normal_dir.resolve()) if logo_normal_dir else "(not set)"
                    )
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
                        logo_list.append(
                            {
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
                        )
                    else:
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
                                        "token": _custom_pdf_slot_token_label(
                                            slot, token_list, fbpi_slots
                                        ),
                                        "path": p_slot,
                                        "source": "pdf_engine_same_as_draw",
                                    }
                                )
                            logo_list.append(
                                {
                                    **base_logo_dict,
                                    "pdf_aligned_custom": True,
                                    "custom_scoped_merge": is_scoped,
                                    "attempts": attempts_pdf,
                                    "resolved_path": primary_slot_path,
                                }
                            )
                        else:
                            order_val = safe_str(row.get("Order Number", ""))
                            if order_val:
                                first_idx = order_number_counts.get(("__first__", order_val))
                                rank = (i - first_idx + 1) if first_idx is not None else 1
                                base_name = order_val if rank == 1 else f"{order_val}-{rank - 1}"
                                p = find_image(
                                    logo_customise_dir, base_name, logo_custom_stem_map, recursive=True
                                )
                                src = _lookup_source_custom_logo(
                                    base_name, p, logo_custom_stem_map
                                )
                                logo_list.append(
                                    {
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
                                )
                else:
                    attempts: List[Dict[str, Any]] = []
                    primary_path: Optional[Path] = None
                    for ti, tok in enumerate(tokens):
                        p = find_image_normal_logo(
                            logo_normal_dir, tok, logo_normal_stem_map, recursive=False
                        )
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
                    logo_list.append(
                        {
                            "row_index": i,
                            "process_and_item": row_id,
                            "order_number": order_num,
                            "item_sku": item_sku,
                            "customise": "No",
                            "logo_design_raw": safe_str(row.get("Logo/Design Image", "")),
                            "tokens": list(tokens),
                            "mode": "normal",
                            "custom_logo_root": str(logo_customise_dir.resolve())
                            if logo_customise_dir
                            else "(not set)",
                            "normal_logo_root": str(logo_normal_dir.resolve())
                            if logo_normal_dir
                            else "(not set)",
                            "attempts": attempts,
                            "resolved_path": primary_path,
                        }
                    )
    return {"apparel": apparel_list, "logo": logo_list}


def format_image_match_log_impl(details: dict) -> str:
    """Human-readable per-row apparel and logo resolution for PDF (verbose for session logs)."""
    apparel = details.get("apparel") or []
    logo = details.get("logo") or []
    if not apparel and not logo:
        return "(no image lookups)"

    lines: List[str] = []
    lines.append(
        "PDF IMAGE LOOKUPS — each block is one CSV row. "
        "Attempts are in PDF engine order; 'Used in PDF' is the file drawn on the packing page."
    )
    lines.append("")

    for item in apparel:
        if isinstance(item, dict):
            lines.append("======== APPAREL (one CSV row) ========")
            lines.append(f"  CSV row index (0-based): {item['row_index']}")
            lines.append(f"  Process and Item Number: {item['process_and_item']}")
            lines.append(f"  Order Number: {item['order_number']}")
            lines.append(f"  Item SKU: {item['item_sku']}")
            lines.append(f"  CSV 'Apparel Image' cell: {item['apparel_image_value']!r}")
            lines.append(f"  CSV 'Picture Name' cell: {item['picture_name_value']!r}")
            lines.append(f"  Apparel image folder (top-level scan / stem map): {item.get('apparel_search_root', '')}")
            lines.append(
                "  Lookup order (same as PDF): try 'Apparel Image' token first, then 'Picture Name' if still no file."
            )
            for a in item.get("attempts", []):
                pth = a.get("path")
                abs_p = ""
                if isinstance(pth, Path) and pth is not None:
                    try:
                        abs_p = str(pth.resolve())
                    except OSError:
                        abs_p = str(pth)
                lines.append(
                    f"    Attempt | {a.get('field')}: token={a.get('token')!r} "
                    f"| result={abs_p or 'NOT FOUND'} | mechanism={a.get('source')}"
                )
            cf = item.get("chosen_field") or ""
            ct = item.get("chosen_token") or ""
            rp = item.get("resolved_path")
            lines.append("  --- Used in PDF (apparel photo on page) ---")
            if cf or ct:
                lines.append(f"    Chosen CSV field: {cf!r} | winning token: {ct!r}")
            if isinstance(rp, Path) and rp:
                try:
                    lines.append(f"    File name: {rp.name}")
                    lines.append(f"    Full path: {rp.resolve()}")
                except OSError:
                    lines.append(f"    File name: {rp.name}")
            else:
                lines.append("    No apparel image file resolved — PDF will not draw this apparel asset.")
            lines.append("")
        else:
            row_id, lookup_name, path = item  # type: ignore[misc]
            value = path.name if path is not None else "NOT FOUND"
            lines.append(f"Apparel: [{row_id}] {lookup_name} -> {value}")

    for item in logo:
        if isinstance(item, dict):
            lines.append("======== LOGO / DESIGN (one CSV row) ========")
            lines.append(f"  CSV row index (0-based): {item['row_index']}")
            lines.append(f"  Process and Item Number: {item['process_and_item']}")
            lines.append(f"  Order Number: {item['order_number']}")
            lines.append(f"  Item SKU: {item['item_sku']}")
            lines.append(f"  Customise: {item.get('customise', '')}")
            lines.append(f"  CSV 'Logo/Design Image' cell: {item.get('logo_design_raw', '')!r}")
            lines.append(f"  Parsed design tokens: {item.get('tokens', [])}")
            lines.append(f"  Mode: {item.get('mode', '')}")
            lines.append(f"  Custom logo folder (recursive when used): {item.get('custom_logo_root', '')}")
            lines.append(f"  Normal logo folder: {item.get('normal_logo_root', '')}")
            if item.get("mode") == "custom":
                if item.get("pdf_plain_order"):
                    lines.append(
                        "  Plain order (plain/plainlg in Item SKU): PDF does not draw logo image files on this row "
                        "(same as draw_page / draw_logo_square_rows)."
                    )
                elif item.get("pdf_aligned_custom"):
                    sm = item.get("custom_scoped_merge")
                    lines.append(
                        "  Customise logo resolution uses the same engine as PDF generation "
                        f"(scoped merge from Order Number (Base): {sm!r})."
                    )
                else:
                    lines.append(
                        f"  Customise lookup token (order-based): {item.get('custom_lookup_token')!r} "
                        f"(line rank among same order={item.get('custom_rank')})"
                    )
            for a in item.get("attempts", []):
                pth = a.get("path")
                abs_p = ""
                if isinstance(pth, Path) and pth is not None:
                    try:
                        abs_p = str(pth.resolve())
                    except OSError:
                        abs_p = str(pth)
                lines.append(
                    f"    Attempt | {a.get('field')}: token={a.get('token')!r} "
                    f"| result={abs_p or 'NOT FOUND'} | mechanism={a.get('source')}"
                )
            lines.append("  --- Used in PDF (logo on page) ---")
            if item.get("pdf_plain_order"):
                lines.append(
                    "    Plain order: PDF does not draw logo images from files on this row "
                    "(matches on-page behaviour)."
                )
            elif item.get("mode") == "normal" and len(item.get("tokens") or []) > 1:
                lines.append(
                    "    Primary reference: first token below matches logo slot 1; "
                    "additional tokens map to further slots when present."
                )
            rp = item.get("resolved_path")
            if not item.get("pdf_plain_order"):
                if isinstance(rp, Path) and rp:
                    try:
                        lines.append(f"    File name: {rp.name}")
                        lines.append(f"    Full path: {rp.resolve()}")
                    except OSError:
                        lines.append(f"    File name: {rp.name}")
                else:
                    lines.append("    No logo file resolved — PDF will not draw this logo asset.")
            lines.append("")
        else:
            row_id, lookup_key, path, kind = item  # type: ignore[misc]
            value = path.name if path is not None else "NOT FOUND"
            lines.append(f"Logo ({kind}): [{row_id}] {lookup_key} -> {value}")

    return "\n".join(lines).rstrip()


def _format_missing_items_section(
    missing_df: Optional[pd.DataFrame],
    header: str,
) -> Optional[str]:
    if missing_df is None or missing_df.empty:
        return None
    col = missing_df.get("Process and Item Number")
    if col is None:
        return None
    vals = col.dropna().astype(str).str.strip().drop_duplicates().sort_values().tolist()
    if not vals:
        return None
    return f"{header}:\n" + "\n".join(vals)


def format_missing_report_impl(
    missing_logo_actual_df: Optional[pd.DataFrame],
    missing_apparel_actual_df: Optional[pd.DataFrame],
) -> Optional[str]:
    sections: List[str] = []
    logo_section = _format_missing_items_section(missing_logo_actual_df, "Missing logos")
    if logo_section:
        sections.append(logo_section)
    apparel_section = _format_missing_items_section(missing_apparel_actual_df, "Missing apparel")
    if apparel_section:
        sections.append(apparel_section)
    if not sections:
        return None
    return "\n\n".join(sections)

