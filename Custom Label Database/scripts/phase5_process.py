"""Per-row print-size fill loop for phase5_print_sizes."""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

from phase5_helpers import (
    classify,
    extract_mock,
    kinds_in,
    map_print_sizes_key,
    map_sr_size,
    paper_from_printing_size,
    split_positions,
    sr_gender,
    suffix_name,
)
from phase5_lookup import lookup_sr
from phase5_maps import MAX_SLOTS, RE_UID
from phase5_wh import assign_columns, fill_slots, sr_by_kind


def process_rows(
    df: pd.DataFrame,
    ps_table: dict,
    mock_blocks: dict,
    mock_inside_blocks: dict,
    sku_index: dict,
    pc_index: dict,
    pe_sizes: dict[str, str],
) -> tuple[dict, list, dict]:
    """Fill position/W/H columns in-place on df. Returns (counts, samples, meta)."""
    rows_n = len(df)
    pos_cols = [f"Position {i} Name" for i in range(1, 5)]
    w_cols = [f"Width {i} (mm)" for i in range(1, 5)]
    h_cols = [f"Height {i} (mm)" for i in range(1, 5)]

    counts: dict = defaultdict(int)
    samples: list = []

    cl = df["Custom Label"].tolist()
    ga = df["Gender Apparel"].tolist()
    sizes = df["Size"].tolist()
    sku_col = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).tolist()
    spc_col = df["Supplier Product Code"].tolist()
    pp_col = df["Print Positions"].tolist()

    new_pp = list(pp_col)
    new_pos = {c: [""] * rows_n for c in pos_cols}
    new_w = {c: [""] * rows_n for c in w_cols}
    new_h = {c: [""] * rows_n for c in h_cols}
    bracket_sr_rows = [False] * rows_n

    for i in range(rows_n):
        if i and i % 20000 == 0:
            print(f"  processed {i:,}/{rows_n:,}", flush=True)
        _process_one(
            i, cl, ga, sizes, sku_col, spc_col, pp_col, new_pp, new_pos, new_w, new_h,
            bracket_sr_rows, pos_cols, w_cols, h_cols, ps_table, mock_blocks,
            mock_inside_blocks, sku_index, pc_index, pe_sizes, counts, samples,
        )

    assign_columns(
        df, new_pp, new_pos, new_w, new_h, bracket_sr_rows, pos_cols, w_cols, h_cols, counts
    )
    return counts, samples, {"rows_n": rows_n}


def _process_one(
    i, cl, ga, sizes, sku_col, spc_col, pp_col, new_pp, new_pos, new_w, new_h,
    bracket_sr_rows, pos_cols, w_cols, h_cols, ps_table, mock_blocks,
    mock_inside_blocks, sku_index, pc_index, pe_sizes, counts, samples,
) -> None:
    pp = pp_col[i]
    if not pp:
        pp = "Front Center"
        new_pp[i] = "Front Center"
        counts["blank_pp_set_front_center"] += 1
    else:
        counts["had_print_positions"] += 1

    mock = extract_mock(pp)
    pos_list = split_positions(pp) or ["Front Center"]
    size_db, gender_ap, spc, label, sku = sizes[i], ga[i], spc_col[i], cl[i], sku_col[i]

    ps_key = map_print_sizes_key(size_db)
    size_used = size_db
    if not ps_key:
        uid = sku if sku and sku in pe_sizes else ""
        if not uid:
            m = RE_UID.search(label)
            cand = m.group(1) if m else ""
            if cand and cand in pe_sizes:
                uid = cand
        pe_size = pe_sizes.get(uid, "")
        if pe_size:
            ps_key = map_print_sizes_key(pe_size)
            if ps_key:
                size_used = pe_size
                counts["used_pe_size"] += 1

    gender = sr_gender(gender_ap, size_used)
    sr_size = map_sr_size(size_used)
    block = lookup_sr(
        mock, spc, label, gender, sr_size, pos_list,
        mock_blocks, mock_inside_blocks, sku_index, pc_index, gender_ap,
    )
    if block:
        if block.get("source") == "mock_inside":
            bracket_sr_rows[i] = True
        counts["size_ref_matched"] += 1
    else:
        counts["size_ref_unmatched"] += 1

    n_designs = block["n_designs"] if block else len(pos_list)
    n_designs = min(max(int(n_designs), len(pos_list), 1), MAX_SLOTS)

    names = list(pos_list)
    if block:
        for r in block["rows"]:
            if len(names) >= n_designs:
                break
            cand = suffix_name(
                r.get("suffix", ""),
                r.get("printing_position", "") or block.get("printing_position", ""),
            )
            if not cand or classify(cand) in kinds_in(names):
                continue
            names.append(cand)
            counts["extra_position_from_sr"] += 1
    names = names[:MAX_SLOTS]

    paper = paper_from_printing_size(block["printing_size"] if block else "")
    shirt_wh = None
    if ps_key and ps_key in ps_table:
        shirt_wh = ps_table[ps_key].get(paper) or ps_table[ps_key].get("A4")
        if shirt_wh:
            counts["used_print_sizes"] += 1

    filled_any_wh = fill_slots(
        i, names, sr_by_kind(block), shirt_wh, bracket_sr_rows[i],
        new_pos, new_w, new_h, pos_cols, w_cols, h_cols, counts,
    )
    counts["rows_with_wh" if filled_any_wh else "rows_no_wh"] += 1
    if len(samples) < 8 and filled_any_wh:
        samples.append(
            {
                "Custom Label": label,
                "Size": size_db,
                "PP": new_pp[i][:60],
                "P1": names[0] if names else "",
                "W1": new_w[w_cols[0]][i],
                "H1": new_h[h_cols[0]][i],
                "P2": names[1] if len(names) > 1 else "",
                "W2": new_w[w_cols[1]][i] if len(names) > 1 else "",
                "H2": new_h[h_cols[1]][i] if len(names) > 1 else "",
                "src": "print_sizes" if shirt_wh else ("size_ref" if block else "none"),
            }
        )
