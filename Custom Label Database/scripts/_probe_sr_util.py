"""Build Size Ref index and run containment probes."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import pandas as pd


def clean(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def build_sr_by_sku(sr: pd.DataFrame) -> dict[str, list[dict]]:
    by_sku: dict[str, list[dict]] = defaultdict(list)
    for _, r in sr.iterrows():
        sv = clean(r.get("SKU Value"))
        if not sv:
            continue
        w, h = r.get("Size Width"), r.get("Size Height")
        try:
            w_f, h_f = float(w), float(h)
        except (TypeError, ValueError):
            continue
        if pd.isna(w_f) or pd.isna(h_f):
            continue
        nd = r.get("Number of Designs")
        try:
            nd_i = int(float(nd)) if pd.notna(nd) else 1
        except (TypeError, ValueError):
            nd_i = 1
        by_sku[sv].append(
            {
                "w": int(w_f),
                "h": int(h_f),
                "nd": nd_i,
                "size": clean(r.get("Size")),
                "gender": clean(r.get("Gender")),
                "suffix": clean(r.get("Suffix")),
                "pos": clean(r.get("Printing Position")),
            }
        )
    return by_sku


APPAREL_RE = re.compile(
    r"t-?shirt|sweat|hoodie|polo|vest|jacket|romper|bodysuit|kids-|mens-|ladies-|womens-|fotl|gildan|fruit",
    re.I,
)


def probe_blank_rows(blank: pd.DataFrame, by_sku: dict[str, list[dict]]) -> dict:
    unique_skus = sorted(by_sku.keys(), key=len, reverse=True)
    matched_contain = matched_exact_cl = matched_bracket_style = 0
    hit_counter: Counter[str] = Counter()
    examples_contain = []
    examples_unmatched = []
    apparel_blank = apparel_contain = 0
    sku_upper = {k.upper(): k for k in by_sku}

    for _, row in blank.iterrows():
        cl = clean(row.get("Custom Label"))
        cl_u = cl.upper()
        ga = clean(row.get("Gender Apparel"))
        is_apparel = bool(APPAREL_RE.search(ga) or APPAREL_RE.search(cl))
        if is_apparel:
            apparel_blank += 1

        if cl_u and cl_u in sku_upper:
            matched_exact_cl += 1

        m = re.match(r"^(M\d+)-(?:P\d+-)?(\d+)$", cl_u, re.I)
        if m:
            mock, uid = m.group(1).upper(), m.group(2)
            for sv in by_sku:
                if re.match(rf"^{re.escape(mock)}\s*\({re.escape(uid)}\)$", sv, re.I):
                    matched_bracket_style += 1
                    break

        hit = None
        for sv in unique_skus:
            if sv.upper() in cl_u:
                hit = sv
                break

        if hit:
            matched_contain += 1
            hit_counter[hit] += 1
            if is_apparel:
                apparel_contain += 1
            if len(examples_contain) < 20:
                rows = by_sku[hit]
                examples_contain.append(
                    {
                        "cl": cl,
                        "ga": ga,
                        "hit": hit,
                        "nd": rows[0]["nd"],
                        "n_sr_rows": len(rows),
                        "wh": [(r["w"], r["h"], r["suffix"]) for r in rows[:4]],
                        "size_col": row.get("Size"),
                    }
                )
        elif len(examples_unmatched) < 20:
            examples_unmatched.append({"cl": cl, "ga": ga, "size": row.get("Size")})

    return {
        "matched_exact_cl": matched_exact_cl,
        "matched_bracket_style": matched_bracket_style,
        "matched_contain": matched_contain,
        "apparel_blank": apparel_blank,
        "apparel_contain": apparel_contain,
        "hit_counter": hit_counter,
        "examples_contain": examples_contain,
        "examples_unmatched": examples_unmatched,
    }


def probe_non_mock(db: pd.DataFrame, by_sku: dict[str, list[dict]]) -> tuple[list[str], int, int, list]:
    non_mock = [k for k in by_sku if not re.match(r"^M\d+", k, re.I)]
    non_mock_sorted = sorted(non_mock, key=len, reverse=True)
    contain_all = blank_among = 0
    samples = []
    for _, row in db.iterrows():
        cl_u = clean(row.get("Custom Label")).upper()
        if not cl_u:
            continue
        hit = None
        for sv in non_mock_sorted:
            if sv.upper() in cl_u:
                hit = sv
                break
        if hit:
            contain_all += 1
            is_blank = clean(row.get("Width 1 (mm)")) == ""
            if is_blank:
                blank_among += 1
                if len(samples) < 25:
                    samples.append(
                        (clean(row.get("Custom Label")), hit, clean(row.get("Width 1 (mm)")))
                    )
    return non_mock, contain_all, blank_among, samples
