"""Size References index builders for fill_from_seeds."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

from fill_seeds_apparel import infer_printing_position, paper_from_printing_size
from fill_seeds_util import clean, to_num

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
        "source": "",
    }


def load_size_ref(config_path: Path) -> tuple[dict, dict, dict, dict]:
    if config_path.suffix.lower() == ".csv":
        sr = pd.read_csv(config_path, dtype=str)
    else:
        sr = pd.read_excel(config_path, sheet_name="Size References")
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
            mock_inside_index[(mock_paren, inside_paren, gender, size)].append(row)
        if pcode and gender and size:
            for code in pcode.split("-"):
                code = code.strip()
                if code:
                    pc_blocks[(code, gender, size)][sku_val].append(row)

    pc_index: dict[tuple[str, str, str], list[dict]] = {}
    for key, by_sku in pc_blocks.items():
        blocks = [_block_from_rows(rows) for rows in by_sku.values() if rows]
        seen: set = set()
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


def score_block(block: dict, wanted_pos: str) -> int:
    got = block.get("printing_position") or ""
    if not wanted_pos:
        return 1
    if got == wanted_pos:
        return 100
    if wanted_pos in got or got in wanted_pos:
        return 50
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
    return ranked[0] if ranked else None

