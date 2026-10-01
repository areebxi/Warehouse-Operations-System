"""Width/Height slot fill + column assign for phase5_print_sizes."""
from __future__ import annotations

import pandas as pd

from phase5_helpers import classify, mm_str, suffix_name
from phase5_maps import POCKET_WH


def sr_by_kind(block: dict | None) -> dict:
    out = {}
    if not block:
        return out
    for r in block["rows"]:
        kind = classify(suffix_name(r.get("suffix", ""), r.get("printing_position", "")))
        if kind in ("empty", "other"):
            if r.get("suffix") == "P":
                kind = "pocket"
            elif r.get("suffix") == "F":
                kind = "front"
            elif r.get("suffix") == "B":
                kind = "back"
        if kind not in out and r.get("w") is not None:
            out[kind] = (r["w"], r["h"])
    if not out and len(block["rows"]) == 1:
        r = block["rows"][0]
        if r.get("w") is not None:
            out["front"] = (r["w"], r["h"])
    return out


def fill_slots(
    i,
    names,
    sr_kinds,
    shirt_wh,
    use_sr_bracket,
    new_pos,
    new_w,
    new_h,
    pos_cols,
    w_cols,
    h_cols,
    counts,
) -> bool:
    filled_any_wh = False
    for slot, name in enumerate(names):
        new_pos[pos_cols[slot]][i] = name
        counts["position_names_set"] += 1
        kind = classify(name)
        wh = None
        src = ""
        if kind == "pocket":
            wh = POCKET_WH
            src = "pocket_fixed"
        elif kind in ("front", "back"):
            if use_sr_bracket:
                if kind in sr_kinds:
                    wh, src = sr_kinds[kind], "size_ref_bracket"
                elif "front" in sr_kinds and kind == "back":
                    wh, src = sr_kinds["front"], "size_ref_bracket_front_for_back"
                elif sr_kinds:
                    wh, src = next(iter(sr_kinds.values())), "size_ref_bracket_any"
                elif shirt_wh:
                    wh, src = shirt_wh, "print_sizes"
            else:
                if shirt_wh:
                    wh, src = shirt_wh, "print_sizes"
                elif kind in sr_kinds:
                    wh, src = sr_kinds[kind], "size_ref"
                elif "front" in sr_kinds and kind == "back":
                    wh, src = sr_kinds["front"], "size_ref_front_for_back"
                elif sr_kinds and kind == "front":
                    wh, src = next(iter(sr_kinds.values())), "size_ref_any"
        else:
            counts["skipped_other_position"] += 1

        if wh and wh[0] is not None and wh[1] is not None:
            new_w[w_cols[slot]][i] = mm_str(wh[0])
            new_h[h_cols[slot]][i] = mm_str(wh[1])
            counts[f"wh_from_{src}"] += 1
            filled_any_wh = True
    return filled_any_wh


def assign_columns(
    df, new_pp, new_pos, new_w, new_h, bracket_sr_rows, pos_cols, w_cols, h_cols, counts
) -> None:
    df["Print Positions"] = new_pp
    for c in pos_cols:
        incoming = pd.Series(new_pos[c], index=df.index)
        mask = df[c].eq("") & incoming.ne("")
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())

    bracket_series = pd.Series(bracket_sr_rows, index=df.index)
    for c in w_cols:
        incoming = pd.Series(new_w[c], index=df.index)
        inc_num = pd.to_numeric(incoming, errors="coerce")
        cur_num = pd.to_numeric(df[c], errors="coerce")
        mask = bracket_series & inc_num.notna() & (cur_num.isna() | (cur_num != inc_num))
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())
    for c in h_cols:
        incoming = pd.Series(new_h[c], index=df.index)
        inc_num = pd.to_numeric(incoming, errors="coerce")
        cur_num = pd.to_numeric(df[c], errors="coerce")
        mask = bracket_series & inc_num.notna() & (cur_num.isna() | (cur_num != inc_num))
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())

    counts["width1_filled"] = int((df["Width 1 (mm)"] != "").sum())
    counts["height1_filled"] = int((df["Height 1 (mm)"] != "").sum())
    counts["pos1_filled"] = int((df["Position 1 Name"] != "").sum())
    counts["pp_filled"] = int((df["Print Positions"] != "").sum())
