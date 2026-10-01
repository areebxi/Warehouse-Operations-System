"""Load Print Sizes / PE / Size References tables for phase5."""
from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd

from phase5_helpers import clean, paper_from_printing_size, to_num
from phase5_maps import CONFIG, PE_PATH, PRINT_SIZES_PATH


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
    pc_blocks: dict[tuple[str, str, str], dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )

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
        if mock and size:
            key = (mock, gender, size)
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

    for b in mock_blocks.values():
        b["source"] = "mock_only"
    for b in mock_inside_blocks.values():
        b["source"] = "mock_inside"

    return mock_blocks, mock_inside_blocks, sku_index, pc_index
