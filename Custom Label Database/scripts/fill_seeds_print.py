"""Print-size fill step for fill_from_seeds."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from size_code_logic import resolve_print_dims  # noqa: E402

from fill_seeds_apparel import classify, is_shirt_row, map_print_sizes_key
from fill_seeds_util import (
    MAX_SLOTS,
    clean,
    mm_str,
    split_positions,
    uid_from_custom_label,
)

def step_print_sizes(
    df: pd.DataFrame,
    size_index,
    overrides,
    ps_table: dict,
    counts: dict,
    only_missing_wh: bool,
    pe_sizes: dict | None = None,
    shirts_only: bool = False,
    w1_blank: bool = False,
) -> None:
    """
    Fill blank print sizes.
    Shirts (t-shirt / polo / M-T W-T K-T): Shirts Print Sizes A4 by size band
    (DB Size, else BTC Product Data Size), unless Size References has an exact
    mock+UID row. Everything else: Size References size-code pipeline.
    Positions from Print Positions (CSV). Number of Designs drives slot count.
    """
    pos_cols = [f"Position {i} Name" for i in range(1, 5)]
    w_cols = [f"Width {i} (mm)" for i in range(1, 5)]
    h_cols = [f"Height {i} (mm)" for i in range(1, 5)]
    for c in pos_cols + w_cols + h_cols:
        if c not in df.columns:
            df[c] = ""
    if "Print Positions" not in df.columns:
        df["Print Positions"] = ""

    rows_n = len(df)
    cl = df["Custom Label"].tolist()
    pp_col = df["Print Positions"].tolist()
    size_col = (
        df["Size"].tolist() if "Size" in df.columns else [""] * rows_n
    )
    ga_col = (
        df["Gender Apparel"].tolist()
        if "Gender Apparel" in df.columns
        else [""] * rows_n
    )
    sku_col = (
        df["Supplier SKU"].tolist() if "Supplier SKU" in df.columns else [""] * rows_n
    )
    pe_sizes = pe_sizes or {}
    w1_list = df["Width 1 (mm)"].tolist() if "Width 1 (mm)" in df.columns else [""] * rows_n

    new_pos = {c: [""] * rows_n for c in pos_cols}
    new_w = {c: [""] * rows_n for c in w_cols}
    new_h = {c: [""] * rows_n for c in h_cols}

    # Process rows that still have any blank width slot (multi-design needs this)
    process_mask = [True] * rows_n
    if only_missing_wh:
        w_lists = [df[c].tolist() for c in w_cols]
        for i in range(rows_n):
            process_mask[i] = any(clean(w_lists[s][i]) == "" for s in range(4))
    for i in range(rows_n):
        if not process_mask[i]:
            continue
        if w1_blank and clean(w1_list[i]) != "":
            process_mask[i] = False
            continue
        if shirts_only and not is_shirt_row(ga_col[i], cl[i], size_col[i]):
            process_mask[i] = False

    for i in range(rows_n):
        if not process_mask[i]:
            counts["print_skipped_already_has_wh"] += 1
            continue
        if i and i % 20000 == 0:
            print(f"  print: {i:,}/{rows_n:,}", flush=True)

        label = cl[i]
        pp = clean(pp_col[i])
        result = resolve_print_dims(label, pp, size_index, overrides, max_slots=MAX_SLOTS)

        code = result["size_code"]
        if code:
            counts["size_code_extracted"] += 1
        else:
            counts["size_code_missing"] += 1
        if result["override"]:
            counts["override_contain_hit"] += 1
        if result["matched_rows"]:
            counts["size_ref_rows_matched"] += 1
        else:
            counts["size_ref_rows_unmatched"] += 1

        names = result["position_names"]
        whs = list(result["whs"])
        n_slots = result["n_slots"]

        if is_shirt_row(ga_col[i], label, size_col[i]):
            size_used = size_col[i]
            ps_key = map_print_sizes_key(size_used)
            if not ps_key and pe_sizes:
                uid = re.sub(r"\.0$", "", clean(sku_col[i]))
                if not uid:
                    uid = uid_from_custom_label(label)
                pe_size = pe_sizes.get(uid, "")
                if pe_size:
                    ps_key = map_print_sizes_key(pe_size)
                    if ps_key:
                        counts["used_pe_size"] += 1
            shirt_wh = None
            if ps_key and ps_key in ps_table:
                shirt_wh = ps_table[ps_key].get("A4")
            if shirt_wh:
                pos_for_kind = names if names else split_positions(pp)
                if not pos_for_kind:
                    pos_for_kind = ["Front Center"]
                while len(whs) < max(n_slots, len(pos_for_kind)):
                    whs.append((None, None))
                n_slots = max(n_slots, len(pos_for_kind))
                overlaid = False
                for slot, name in enumerate(pos_for_kind[:MAX_SLOTS]):
                    kind = classify(name)
                    if kind in ("front", "back"):
                        if slot >= len(whs):
                            whs.append(shirt_wh)
                        else:
                            whs[slot] = shirt_wh
                        overlaid = True
                if overlaid:
                    names = pos_for_kind
                    counts["wh_from_shirt_print_sizes"] += 1

        # Position names from Print Positions (blank fill only later)
        for slot, name in enumerate(names[:MAX_SLOTS]):
            new_pos[pos_cols[slot]][i] = name

        filled_any = False
        for slot in range(min(n_slots, MAX_SLOTS)):
            if slot >= len(whs):
                break
            w, h = whs[slot]
            if w is None or h is None:
                continue
            new_w[w_cols[slot]][i] = mm_str(w)
            new_h[h_cols[slot]][i] = mm_str(h)
            counts[f"wh_slot_{slot + 1}"] += 1
            filled_any = True

        if filled_any:
            counts["rows_with_wh"] += 1
        else:
            counts["rows_no_wh"] += 1

        counts["n_designs_slots_total"] += n_slots

    proc = pd.Series(process_mask, index=df.index)

    # Position names: blank only
    for c in pos_cols:
        incoming = pd.Series(new_pos[c], index=df.index)
        mask = proc & df[c].eq("") & incoming.ne("")
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())

    # Width/Height: blank only
    for c in w_cols + h_cols:
        incoming = pd.Series(
            new_w[c] if c in w_cols else new_h[c], index=df.index
        )
        mask = proc & df[c].eq("") & incoming.ne("")
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())
        counts[f"blank_filled_{c}"] = int(mask.sum())

    counts["width1_now_filled"] = int((df["Width 1 (mm)"].map(clean) != "").sum())
    counts["pos1_now_filled"] = int((df["Position 1 Name"].map(clean) != "").sum())
    counts["width1_still_blank"] = int((df["Width 1 (mm)"].map(clean) == "").sum())

