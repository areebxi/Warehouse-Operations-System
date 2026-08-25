"""
Phase 5 — Fill print Width/Height (mm) and Position 1-4 Name.

Supervisor choices (17 Aug 2026):
  Blank Print Positions -> Front Center
  Pocket -> always 80 x 100
  Front and Back -> same mm
  Print Sizes.xlsx first (shirts); Size References for bags/other
  Printing Size A3/A4 picks Print Sizes column; missing -> A4
  DB Size first; PE Size via Custom Label UID if unmapped
  Women -> Men size band
  Number of Designs drives extra slots
  Extra slots: Position names + W/H; Print Positions cell unchanged (except blanks)
  Sleeve / corners / kebab -> leave W/H blank
  No overwrite of existing mm
"""
from __future__ import annotations

import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
PE_PATH = BASE / "ProductExport.xlsx"
CONFIG = BASE / "Configuration Workbook.xlsx"
PRINT_SIZES_PATH = BASE / "Print Sizes.xlsx"
BACKUP = BASE / f"Custom Label Database_Updated_prePhase5Print_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
OUT = SRC
LOG = BASE / "docs" / "PHASE_5_CHANGELOG.md"

POCKET_WH = (80, 100)
MAX_SLOTS = 4

RE_MOCK = re.compile(r"\(M(\d+)\)", re.I)
RE_UID = re.compile(r"-(\d+)$")
RE_CRLF = re.compile(r"[\r\n]+")

AGE_TO_PRINT = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y/YXS",
    "3-4Y": "3-4Y/YXS",
    "3-4Y/YXS": "3-4Y/YXS",
    "YXS": "3-4Y/YXS",
    "5-6 Years": "5-6Y/YS",
    "5-6Y": "5-6Y/YS",
    "5-6Y/YS": "5-6Y/YS",
    "YS": "5-6Y/YS",
    "7-8 Years": "7-8Y/YM",
    "7-8Y": "7-8Y/YM",
    "7-8Y/YM": "7-8Y/YM",
    "YM": "7-8Y/YM",
    "9-11 Years": "9-11Y/YL",
    "9-11Y": "9-11Y/YL",
    "9-11Y/YL": "9-11Y/YL",
    "YL": "9-11Y/YL",
    "12-13 Years": "12-13Y/YXL",
    "12-13Y": "12-13Y/YXL",
    "12-13Y/YXL": "12-13Y/YXL",
    "YXL": "12-13Y/YXL",
}

AGE_TO_SR = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y",
    "3-4Y": "3-4Y",
    "5-6 Years": "5-6Y",
    "5-6Y": "5-6Y",
    "7-8 Years": "7-8Y",
    "7-8Y": "7-8Y",
    "9-11 Years": "9-11Y",
    "9-11Y": "9-11Y",
    "12-13 Years": "12-13Y",
    "12-13Y": "12-13Y",
    "12-14 Years": "14-15Y",
    "14-15 Years": "14-15Y",
    "14-15Y": "14-15Y",
}

LETTER_TO_SR = {
    "Extra Small": "XS",
    "XS": "XS",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

LETTER_TO_MEN_PRINT = {
    "Extra Small": "Men Small",
    "XS": "Men Small",
    "Small": "Men Small",
    "S": "Men Small",
    "Medium": "Men Medium",
    "M": "Men Medium",
    "Large": "Men Large",
    "L": "Men Large",
    "Extra Large": "Men XL",
    "XL": "Men XL",
    "2XL": "Men 2XL",
    "XXL": "Men 2XL",
    "3XL": "Men 3XL",
    "4XL": "Men 4XL",
    "5XL": "Men 5XL",
}

PE_AGE = {
    "1-2": "1-2Y",
    "2-3": "2-3Y",
    "3-4": "3-4Y",
    "5-6": "5-6Y",
    "7-8": "7-8Y",
    "9-11": "9-11Y",
    "12-13": "12-13Y",
    "14-15": "14-15Y",
}

SUFFIX_TO_NAME = {
    "P": "Front Left Pocket",
    "F": "Front Center",
    "B": "Back Center",
    "S": "Sleeve",
    "S-1": "Sleeve",
}

KNOWN_HUMAN = {
    "front center",
    "back center",
    "front left pocket",
    "front right pocket",
    "front bottom left corner",
    "front bottom right corner",
    "right sleeve",
    "sleeve",
    "inside",
}


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    s = RE_CRLF.sub(" ", s)
    return s.strip()


def to_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        n = float(s)
        if n != n:  # NaN
            return None
        return int(n) if n == int(n) else n
    except (TypeError, ValueError):
        return None


def extract_mock(pp: str) -> str:
    m = RE_MOCK.search(pp)
    return f"M{m.group(1)}" if m else ""


def split_positions(pp: str) -> list[str]:
    pp = RE_MOCK.sub("", pp)
    parts = re.split(r"\s*,\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]


def is_age_size(size: str) -> bool:
    s = size.lower()
    return (
        "year" in s
        or size in PE_AGE
        or size in AGE_TO_PRINT
        or size in AGE_TO_SR
        or bool(re.match(r"^\d+-\d+y", s, re.I))
    )


def sr_gender(gender_apparel: str, size: str) -> str:
    if is_age_size(size):
        return "Kids"
    g = gender_apparel.lower()
    if any(x in g for x in ("kid", "child", "youth", "junior", "infant", "baby", "toddler")):
        return "Kids"
    if any(x in g for x in ("women", "woman", "ladies", "lady", "girl", "female")):
        return "Women"
    return "Men"


def map_sr_size(size: str) -> str:
    if size in AGE_TO_SR:
        return AGE_TO_SR[size]
    if size in LETTER_TO_SR:
        return LETTER_TO_SR[size]
    if size in PE_AGE:
        return PE_AGE[size]
    return size


def map_print_sizes_key(size: str) -> str:
    if size in AGE_TO_PRINT:
        return AGE_TO_PRINT[size]
    if size in LETTER_TO_MEN_PRINT:
        return LETTER_TO_MEN_PRINT[size]
    if size in PE_AGE:
        age_sr = PE_AGE[size]
        return AGE_TO_PRINT.get(age_sr, AGE_TO_PRINT.get(age_sr + " Years", ""))
    return ""


def classify(name: str) -> str:
    n = name.lower().strip()
    if not n:
        return "empty"
    if n not in KNOWN_HUMAN and "-" in n:
        return "other"
    if "sleeve" in n or "corner" in n or n == "inside":
        return "other"
    if "pocket" in n or "chest" in n:
        return "pocket"
    if "back" in n:
        return "back"
    if "front" in n:
        return "front"
    return "other"


def infer_printing_position(pos_list: list[str]) -> str:
    kinds = [classify(p) for p in pos_list]
    has_p = "pocket" in kinds
    has_f = "front" in kinds
    has_b = "back" in kinds
    if has_p and has_b:
        return "Left Chest & Back Print"
    if has_f and has_b:
        return "Front & Back Print"
    if has_p:
        return "Left Chest"
    if has_b and not has_f:
        return "Back Print"
    if has_f:
        return "Front Print"
    return ""


def paper_from_printing_size(val: str) -> str:
    s = (val or "").upper()
    if "A3" in s:
        return "A3"
    if "A4" in s:
        return "A4"
    return "A4"


def suffix_name(suffix: str, printing_position: str) -> str:
    suf = (suffix or "").upper()
    if suf in SUFFIX_TO_NAME:
        return SUFFIX_TO_NAME[suf]
    pp = (printing_position or "").strip()
    if pp == "Left Chest":
        return "Front Left Pocket"
    if pp == "Front Print":
        return "Front Center"
    if pp == "Back Print":
        return "Back Center"
    return ""


def kinds_in(names: list[str]) -> set[str]:
    return {classify(n) for n in names if n}


def load_print_sizes() -> dict[str, dict[str, tuple[int, int]]]:
    raw = pd.read_excel(PRINT_SIZES_PATH, sheet_name=0, header=None)
    table: dict[str, dict[str, tuple[int, int]]] = {}
    for _, row in raw.iloc[2:].iterrows():
        key = clean(row.iloc[0])
        if not key:
            continue
        a4w, a4h = to_num(row.iloc[1]), to_num(row.iloc[2])
        a3w, a3h = to_num(row.iloc[3]), to_num(row.iloc[4])
        entry = {}
        if a4w is not None and a4h is not None:
            entry["A4"] = (int(a4w), int(a4h))
        if a3w is not None and a3h is not None:
            entry["A3"] = (int(a3w), int(a3h))
        if entry:
            table[key] = entry
    return table


def load_pe_sizes() -> dict[str, str]:
    pe = pd.read_excel(PE_PATH, sheet_name="staff", dtype=str, usecols=["UID", "Size"])
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    out = {}
    for uid, size in zip(pe["UID"].map(clean), pe["Size"].map(clean)):
        if uid and uid not in out:
            out[uid] = size
    return out


def _block_from_rows(rows: list[dict]) -> dict:
    n_designs = 1
    for r in rows:
        nd = r.get("n_designs")
        if nd:
            n_designs = int(nd)
            break
    return {
        "n_designs": n_designs,
        "printing_position": rows[0].get("printing_position", "") if rows else "",
        "printing_size": next((r["printing_size"] for r in rows if r.get("printing_size")), ""),
        "mock": rows[0].get("mock", "") if rows else "",
        "sku_value": rows[0].get("sku_value", "") if rows else "",
        "rows": rows,
    }


def load_size_ref() -> tuple[dict, dict, dict, dict]:
    sr = pd.read_excel(CONFIG, sheet_name="Size References")
    mock_index: dict[tuple[str, str, str], list[dict]] = {}
    mock_inside_index: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    sku_index: dict[str, list[dict]] = defaultdict(list)
    pc_blocks: dict[tuple[str, str, str], dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for _, rec in sr.iterrows():
        sku_val = clean(rec.get("SKU Value"))
        suffix = clean(rec.get("Suffix"))
        gender = clean(rec.get("Gender"))
        size = clean(rec.get("Size"))
        ppos = clean(rec.get("Printing Position"))
        psize = clean(rec.get("Printing Size"))
        pcode = clean(rec.get("Product Code"))
        w = to_num(rec.get("Size Width"))
        h = to_num(rec.get("Size Height"))
        nd = to_num(rec.get("Number of Designs")) or 1
        mock_m = re.match(r"^(M\d+)", sku_val, re.I)
        mock = mock_m.group(1).upper() if mock_m else ""

        # Bracket/SKU "mock (inside)" parsing, e.g. "M260 (102722)"
        mock_paren_m = re.match(r"^(M\d+)\s*\(([^)]+)\)", sku_val, re.I)
        mock_paren = mock_paren_m.group(1).upper() if mock_paren_m else ""
        inside_paren = clean(mock_paren_m.group(2)) if mock_paren_m else ""

        row = {
            "sku_value": sku_val,
            "suffix": suffix.upper(),
            "gender": gender,
            "size": size,
            "printing_position": ppos,
            "printing_size": psize,
            "w": int(w) if w is not None else None,
            "h": int(h) if h is not None else None,
            "n_designs": int(nd),
            "mock": mock,
        }
        if sku_val:
            sku_index[sku_val.upper()].append(row)
        # Index mock bands even when Gender in Size References is blank.
        # (Some rows in SR leave Gender empty but still provide dimensions.)
        if mock and size:
            key = (mock, gender, size)
            # keep first row per suffix for this mock+gender+size
            existing = mock_index.get(key)
            if existing is None:
                mock_index[key] = [row]
            else:
                sufs = {r["suffix"] for r in existing}
                if row["suffix"] not in sufs:
                    existing.append(row)

        if mock_paren and inside_paren and size:
            key_mi = (mock_paren, inside_paren, gender, size)
            mock_inside_index[key_mi].append(row)
        if pcode and gender and size:
            for code in pcode.split("-"):
                code = code.strip()
                if not code:
                    continue
                pc_blocks[(code, gender, size)][sku_val].append(row)

    pc_index: dict[tuple[str, str, str], list[dict]] = {}
    for key, by_sku in pc_blocks.items():
        blocks = [_block_from_rows(rows) for rows in by_sku.values() if rows]
        # collapse identical (mock, printing_position, printing_size, suffix mm)
        seen = set()
        uniq = []
        for b in blocks:
            sig = (
                b["mock"],
                b["printing_position"],
                paper_from_printing_size(b["printing_size"]),
                tuple((r["suffix"], r["w"], r["h"]) for r in b["rows"]),
            )
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append(b)
        pc_index[key] = uniq

    mock_blocks = {k: _block_from_rows(v) for k, v in mock_index.items()}
    mock_inside_blocks = {k: _block_from_rows(v) for k, v in mock_inside_index.items()}

    # Mark which lookup path we came from.
    for b in mock_blocks.values():
        b["source"] = "mock_only"
    for b in mock_inside_blocks.values():
        b["source"] = "mock_inside"

    return mock_blocks, mock_inside_blocks, sku_index, pc_index


def normalize_gender_apparel_for_sr_sku(gender_apparel: str) -> list[str]:
    """
    Size References 'SKU Value' for some babywear/apparel entries omits certain
    prefixes/suffixes that appear in our main DB's 'Gender Apparel'.

    Examples:
      - 'C800T-BS' -> 'C800T'
      - 'BG-BG125J' -> 'BG125J'
    """
    s = clean(gender_apparel).upper()
    if not s:
        return []

    cands: list[str] = []

    # Babywear codes often end with '-BS' in the DB but are stored without it in SR.
    if s.endswith("-BS") and len(s) > 3:
        base = s[: -len("-BS")]
        if base and base != s:
            cands.append(base)

    # Bags/other products sometimes have a 'BG-' prefix in the DB while SR stores without it.
    if s.startswith("BG-") and len(s) > len("BG-"):
        cands.append(s.replace("BG-", "", 1))

        # Example specific discrepancy:
        #   DB: "BG-China-Bag"
        #   SR: "BG-Chinabag"
        # Normalize by removing internal dashes after the "BG-" prefix.
        #   "BG-" + "CHINA-BAG" -> "BG-" + "CHINABAG"
        remainder = s.replace("BG-", "", 1)
        if "CHINA" in remainder and "BAG" in remainder:
            cands.append("BG-" + remainder.replace("-", ""))

    # De-dupe while preserving order
    out: list[str] = []
    seen: set[str] = set()
    for x in cands:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def score_block(block: dict, wanted_pos: str) -> int:
    got = block.get("printing_position") or ""
    if not wanted_pos:
        return 1
    if got == wanted_pos:
        return 100
    if wanted_pos in got or got in wanted_pos:
        return 50
    # loose
    if "Chest" in wanted_pos and "Chest" in got:
        return 40
    if "Front" in wanted_pos and "Front" in got:
        return 30
    if "Back" in wanted_pos and "Back" in got:
        return 20
    return 0


def pick_pc_block(blocks: list[dict], pos_list: list[str], mock: str) -> dict | None:
    if not blocks:
        return None
    if mock:
        mocked = [b for b in blocks if b.get("mock") == mock]
        if mocked:
            blocks = mocked
    wanted = infer_printing_position(pos_list)
    ranked = sorted(blocks, key=lambda b: score_block(b, wanted), reverse=True)
    best = ranked[0]
    best_score = score_block(best, wanted)
    if best_score == 0 and wanted:
        # still return best for A3/A4 / n_designs rather than nothing
        return best
    return best


def lookup_sr(
    mock: str,
    spc: str,
    custom_label: str,
    gender: str,
    sr_size: str,
    pos_list: list[str],
    mock_blocks: dict,
    mock_inside_blocks: dict,
    sku_index: dict,
    pc_index: dict,
    gender_apparel: str,
) -> dict | None:
    genders_try = [gender]
    if gender == "Women":
        genders_try.append("Men")
    if gender != "Kids" and is_age_size(sr_size):
        genders_try.append("Kids")
    # Also try blank SR gender rows (some Size References entries have empty Gender).
    if "" not in genders_try:
        genders_try.append("")

    ga_keys = normalize_gender_apparel_for_sr_sku(gender_apparel)

    # Prefer bracket-based matching (mock + inside code) when possible.
    # Example:
    #   SR: "M260 (102722)"
    #   DB: "M260-102722" or "M260-P6-102722"
    inside = ""
    m_inside = re.search(r"-(?:P\d+-)?(\d+)$", clean(custom_label).upper())
    if m_inside:
        inside = m_inside.group(1)

    # Some rows have Print Positions like "Front Center" without "(M###)" mock codes.
    # In that case, derive the mock from the Custom Label itself (e.g. "M260-102722").
    mock_eff = mock
    if not mock_eff:
        m_mock = re.match(r"^(M\d+)", clean(custom_label).upper(), flags=re.I)
        mock_eff = m_mock.group(1).upper() if m_mock else ""

    if mock_eff and sr_size and inside:
        for g in genders_try:
            b = mock_inside_blocks.get((mock_eff, inside, g, sr_size))
            if b:
                return b

    if mock and sr_size:
        for g in genders_try:
            b = mock_blocks.get((mock, g, sr_size))
            if b:
                return b

    # Fast path: match Size References 'SKU Value' using whatever keys we have.
    # For some categories, 'Supplier Product Code' is blank, so we also derive
    # candidates from 'Gender Apparel'.
    for key in (spc.upper(), custom_label.upper(), *ga_keys):
        if key and key in sku_index:
            return _block_from_rows(sku_index[key])

    if spc and sr_size:
        for g in genders_try:
            blocks = pc_index.get((spc, g, sr_size))
            picked = pick_pc_block(blocks or [], pos_list, mock)
            if picked:
                return picked
    return None


def mm_str(val) -> str:
    if val is None or val == "":
        return ""
    return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)


def main() -> None:
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading Print Sizes...", flush=True)
    ps_table = load_print_sizes()
    print(f"  {len(ps_table)} apparel size bands", flush=True)

    print("Loading Size References...", flush=True)
    mock_blocks, mock_inside_blocks, sku_index, pc_index = load_size_ref()
    print(f"  mock blocks={len(mock_blocks)} sku keys={len(sku_index)} pc keys={len(pc_index)}", flush=True)

    print("Loading PE sizes...", flush=True)
    pe_sizes = load_pe_sizes()
    print(f"  {len(pe_sizes)} UIDs", flush=True)

    print("Loading CLD...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows_n = len(df)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

    pos_cols = [f"Position {i} Name" for i in range(1, 5)]
    w_cols = [f"Width {i} (mm)" for i in range(1, 5)]
    h_cols = [f"Height {i} (mm)" for i in range(1, 5)]

    counts = defaultdict(int)
    samples = []

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
    # True when we used Size References bracket matching (mock + inside code),
    # so we can safely overwrite Width/Height if they disagree.
    bracket_sr_rows = [False] * rows_n

    for i in range(rows_n):
        if i and i % 20000 == 0:
            print(f"  processed {i:,}/{rows_n:,}", flush=True)

        pp = pp_col[i]
        if not pp:
            pp = "Front Center"
            new_pp[i] = "Front Center"
            counts["blank_pp_set_front_center"] += 1
        else:
            counts["had_print_positions"] += 1

        mock = extract_mock(pp)
        pos_list = split_positions(pp)
        if not pos_list:
            pos_list = ["Front Center"]

        size_db = sizes[i]
        gender_ap = ga[i]
        spc = spc_col[i]
        label = cl[i]
        sku = sku_col[i]

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
            mock,
            spc,
            label,
            gender,
            sr_size,
            pos_list,
            mock_blocks,
            mock_inside_blocks,
            sku_index,
            pc_index,
            gender_ap,
        )
        if block:
            if block.get("source") == "mock_inside":
                bracket_sr_rows[i] = True
            counts["size_ref_matched"] += 1
        else:
            counts["size_ref_unmatched"] += 1

        n_designs = block["n_designs"] if block else len(pos_list)
        n_designs = max(int(n_designs), len(pos_list), 1)
        n_designs = min(n_designs, MAX_SLOTS)

        names = list(pos_list)
        if block:
            for r in block["rows"]:
                if len(names) >= n_designs:
                    break
                cand = suffix_name(r.get("suffix", ""), r.get("printing_position", "") or block.get("printing_position", ""))
                if not cand:
                    continue
                if classify(cand) in kinds_in(names):
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

        sr_by_kind = {}
        if block:
            for r in block["rows"]:
                kind = classify(suffix_name(r.get("suffix", ""), r.get("printing_position", "")))
                if kind in ("empty", "other"):
                    if r.get("suffix") == "P":
                        kind = "pocket"
                    elif r.get("suffix") == "F":
                        kind = "front"
                    elif r.get("suffix") == "B":
                        kind = "back"
                if kind not in sr_by_kind and r.get("w") is not None:
                    sr_by_kind[kind] = (r["w"], r["h"])
            if not sr_by_kind and len(block["rows"]) == 1:
                r = block["rows"][0]
                if r.get("w") is not None:
                    sr_by_kind["front"] = (r["w"], r["h"])

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
                use_sr_bracket = bracket_sr_rows[i]
                if use_sr_bracket:
                    # For bracket-matched mock+inside cases, enforce Size References dimensions
                    # even for shirts (Print Sizes.xlsx may disagree).
                    if kind in sr_by_kind:
                        wh = sr_by_kind[kind]
                        src = "size_ref_bracket"
                    elif "front" in sr_by_kind and kind == "back":
                        wh = sr_by_kind["front"]
                        src = "size_ref_bracket_front_for_back"
                    elif sr_by_kind:
                        wh = next(iter(sr_by_kind.values()))
                        src = "size_ref_bracket_any"
                    elif shirt_wh:
                        wh = shirt_wh
                        src = "print_sizes"
                else:
                    if shirt_wh:
                        wh = shirt_wh
                        src = "print_sizes"
                    elif kind in sr_by_kind:
                        wh = sr_by_kind[kind]
                        src = "size_ref"
                    elif "front" in sr_by_kind and kind == "back":
                        wh = sr_by_kind["front"]
                        src = "size_ref_front_for_back"
                    elif sr_by_kind and kind == "front":
                        # bags / single row
                        wh = next(iter(sr_by_kind.values()))
                        src = "size_ref_any"
            else:
                counts["skipped_other_position"] += 1

            if wh and wh[0] is not None and wh[1] is not None:
                new_w[w_cols[slot]][i] = mm_str(wh[0])
                new_h[h_cols[slot]][i] = mm_str(wh[1])
                counts[f"wh_from_{src}"] += 1
                filled_any_wh = True

        if filled_any_wh:
            counts["rows_with_wh"] += 1
        else:
            counts["rows_no_wh"] += 1

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

    # assign (blank-only for mm; position names currently empty)
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

    print("Counts:", dict(counts), flush=True)
    if samples:
        print(pd.DataFrame(samples).to_string(index=False), flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

    sample_txt = pd.DataFrame(samples).to_string(index=False) if samples else "(none)"
    log = f"""# Phase 5 Changelog — Print sizes

**Executed:** {datetime.now().strftime('%d %B %Y')}  
**Supervisor approval:** implement print Width/Height + Position names (choice A)

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `{BACKUP.name}`  
**Rows:** {rows_n:,} (unchanged — no deletes)

---

## Rules applied

- Blank Print Positions -> `Front Center`
- Pocket -> 80 x 100 mm
- Front and Back -> same millimetres
- Print Sizes.xlsx first (shirts); Size References for bags / unmapped sizes
- Printing Size A3/A4 selects the Print Sizes column; missing -> A4
- Database Size first; ProductExport Size via Custom Label UID if unmapped
- Women uses Men Print Sizes band
- Number of Designs adds extra Position name + W/H slots; Print Positions text not expanded
- Sleeve / corners / kebab-case: Position name may be set; Width/Height left blank
- Overwrite Width/Height for bracket-matched mock+inside cases when Size References disagree

---

## Summary

| Metric | Count |
|--------|------:|
| Blank Print Positions set to Front Center | {counts.get('blank_pp_set_front_center', 0):,} |
| Print Positions now filled | {counts.get('pp_filled', 0):,} |
| Size References matched | {counts.get('size_ref_matched', 0):,} |
| Size References unmatched | {counts.get('size_ref_unmatched', 0):,} |
| Rows using Print Sizes.xlsx | {counts.get('used_print_sizes', 0):,} |
| Rows using PE Size fallback | {counts.get('used_pe_size', 0):,} |
| Extra position names from Size References | {counts.get('extra_position_from_sr', 0):,} |
| Rows with at least one W/H filled | {counts.get('rows_with_wh', 0):,} |
| Rows with no W/H | {counts.get('rows_no_wh', 0):,} |
| Position 1 Name filled | {counts.get('pos1_filled', 0):,} |
| Width 1 (mm) filled | {counts.get('width1_filled', 0):,} |
| Height 1 (mm) filled | {counts.get('height1_filled', 0):,} |
| Width 1 cells written | {counts.get('filled_Width 1 (mm)', 0):,} |
| Width 2 cells written | {counts.get('filled_Width 2 (mm)', 0):,} |
| Width 3 cells written | {counts.get('filled_Width 3 (mm)', 0):,} |
| Width 4 cells written | {counts.get('filled_Width 4 (mm)', 0):,} |
| W/H from pocket fixed 80x100 | {counts.get('wh_from_pocket_fixed', 0):,} |
| W/H from Print Sizes.xlsx | {counts.get('wh_from_print_sizes', 0):,} |
| W/H from Size References | {counts.get('wh_from_size_ref', 0) + counts.get('wh_from_size_ref_front_for_back', 0) + counts.get('wh_from_size_ref_any', 0):,} |
| Other positions skipped (no mm) | {counts.get('skipped_other_position', 0):,} |

---

## Sample filled rows

```
{sample_txt}
```

---

*See: [PHASE_5_PRINT_SIZES_PLAN.md](PHASE_5_PRINT_SIZES_PLAN.md)*
"""
    LOG.write_text(log, encoding="utf-8")
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 5 print sizes complete.", flush=True)


if __name__ == "__main__":
    main()
