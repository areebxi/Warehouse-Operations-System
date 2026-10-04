from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd


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

