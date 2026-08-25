"""Probe: why blank print sizes remain vs simple SKU Value containment."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import pandas as pd

DB = r"D:\Custom Label Database\Custom Label Database.xlsx"
SR = r"D:\Custom Label Database\support\Configuration Workbook.xlsx"


def clean(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def main() -> None:
    print("Loading DB + Size References...")
    db = pd.read_excel(DB, dtype=str)
    sr = pd.read_excel(SR, sheet_name="Size References")

    for c in ("Width 1 (mm)", "Width 2 (mm)", "Height 1 (mm)", "Height 2 (mm)"):
        if c not in db.columns:
            db[c] = ""

    w1 = db["Width 1 (mm)"].map(clean)
    blank_mask = w1.eq("")
    blank = db[blank_mask]
    print(f"blank Width 1: {len(blank):,} / {len(db):,}")
    print(f"blank Width 2 (among filled W1): {(db.loc[~blank_mask, 'Width 2 (mm)'].map(clean).eq('').sum()):,}")

    # Index SR by SKU Value (keep all design rows for Number of Designs)
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

    # Prefer longest SKU Value (more specific) for containment
    unique_skus = sorted(by_sku.keys(), key=len, reverse=True)
    print(f"SKU Values with dims: {len(unique_skus):,}")

    # Exact-key logic used today: SPC / full Custom Label / Gender Apparel
    # (not containment)
    matched_contain = 0
    matched_exact_cl = 0
    matched_bracket_style = 0  # M260 (uid) -> M260-uid / M260-P#-uid
    hit_counter: Counter[str] = Counter()
    examples_contain = []
    examples_unmatched = []
    apparel_blank = 0
    apparel_contain = 0

    apparel_re = re.compile(
        r"t-?shirt|sweat|hoodie|polo|vest|jacket|romper|bodysuit|kids-|mens-|ladies-|womens-|fotl|gildan|fruit",
        re.I,
    )

    for _, row in blank.iterrows():
        cl = clean(row.get("Custom Label"))
        cl_u = cl.upper()
        ga = clean(row.get("Gender Apparel"))
        is_apparel = bool(apparel_re.search(ga) or apparel_re.search(cl))
        if is_apparel:
            apparel_blank += 1

        if cl_u and cl_u in {k.upper(): k for k in by_sku}:
            matched_exact_cl += 1

        # bracket-style: SR has M260 (123432), CL has M260-123432
        m = re.match(r"^(M\d+)-(?:P\d+-)?(\d+)$", cl_u, re.I)
        bracket_hit = False
        if m:
            mock, uid = m.group(1).upper(), m.group(2)
            key_paren = f"{mock} ({uid})"
            # any case variant in by_sku
            for sv in by_sku:
                if sv.upper() == key_paren.upper() or (
                    sv.upper().startswith(mock + " (") and uid in sv
                ):
                    # loose: mock (something containing uid)
                    if re.match(rf"^{re.escape(mock)}\s*\({re.escape(uid)}\)$", sv, re.I):
                        bracket_hit = True
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
        else:
            if len(examples_unmatched) < 20:
                examples_unmatched.append({"cl": cl, "ga": ga, "size": row.get("Size")})

    print()
    print("=== Among blank Width 1 rows ===")
    print(f"exact Custom Label == SKU Value: {matched_exact_cl}")
    print(f"bracket M### (uid) style possible: {matched_bracket_style}")
    print(f"simple containment (SKU Value in Custom Label): {matched_contain}")
    print(f"apparel-ish blanks: {apparel_blank}, of which containment hits: {apparel_contain}")
    print()
    print("Top containment hits:")
    for k, v in hit_counter.most_common(30):
        print(f"  {v:4d}  {k!r}  sr_rows={len(by_sku[k])} nd={by_sku[k][0]['nd']}")

    print("\nContainment examples:")
    for e in examples_contain:
        print(
            f"  CL={e['cl']!r}\n"
            f"    GA={e['ga']!r} Size={e['size_col']!r}\n"
            f"    hit={e['hit']!r} nd={e['nd']} sr_rows={e['n_sr_rows']} wh={e['wh']}"
        )

    print("\nStill unmatched examples:")
    for e in examples_unmatched:
        print(f"  CL={e['cl']!r} GA={e['ga']!r} Size={e['size']!r}")

    # Non-mock SKU catalog (user's t-shirt examples)
    print("\n=== Non-mock SKU Values in Size References ===")
    non_mock = [k for k in by_sku if not re.match(r"^M\d+", k, re.I)]
    print(f"count={len(non_mock)}")
    for k in sorted(non_mock, key=str.upper)[:80]:
        rows = by_sku[k]
        print(
            f"  {k!r:42s} nd={rows[0]['nd']} n={len(rows)} "
            f"size={rows[0]['size']!r} wh={rows[0]['w']}x{rows[0]['h']}"
        )

    # How many DB rows (all, not just blank) contain a non-mock SKU Value
    print("\n=== All DB rows containing a non-mock SKU Value ===")
    non_mock_sorted = sorted(non_mock, key=len, reverse=True)
    contain_all = 0
    blank_among = 0
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
                    samples.append((clean(row.get("Custom Label")), hit, clean(row.get("Width 1 (mm)"))))
    print(f"rows with non-mock SKU containment: {contain_all}")
    print(f"  of which Width1 blank: {blank_among}")
    print("samples (blank):")
    for s in samples:
        print(" ", s)


if __name__ == "__main__":
    main()
