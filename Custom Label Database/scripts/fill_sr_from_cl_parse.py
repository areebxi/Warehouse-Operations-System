"""Parse CL mock+UID rows into Size References payloads."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from fill_from_seeds import (
    classify,
    clean,
    infer_printing_position,
    map_sr_size,
    mm_str,
    split_positions,
    sr_gender,
    to_num,
)
from fill_sr_from_cl_paths import RE_LETTER_SIZE, RE_MOCK_UID, RE_SR_KEY
from generate_from_mocks import load_mocks


def sr_key(mock: str, uid: str) -> str:
    return f"{mock.upper()} ({uid})"


def parse_cl_mock_uid(label: str) -> tuple[str, str] | None:
    m = RE_MOCK_UID.match(clean(label))
    if not m:
        return None
    return m.group(1).upper(), m.group(2)


def parse_sr_key(sku_value: str) -> str:
    m = RE_SR_KEY.match(clean(sku_value))
    if not m:
        return ""
    return sr_key(m.group(1), m.group(2))


def mm_cell(val) -> str:
    n = to_num(val)
    if n is None:
        return ""
    return mm_str(n)


def suffix_for_slots(pos_names: list[str], n_slots: int) -> list[str]:
    """Multi-design: F/B/P/S. Single-design: blank suffix (matches existing SR)."""
    if n_slots <= 1:
        return [""] * n_slots
    used: dict[str, int] = defaultdict(int)
    out: list[str] = []
    for i in range(n_slots):
        kind = classify(pos_names[i]) if i < len(pos_names) else "empty"
        if kind == "pocket":
            token = "P"
        elif kind == "back":
            token = "B"
        elif kind == "front":
            token = "F"
        elif kind == "other":
            token = "S"
        else:
            token = "F"
        n = used[token]
        used[token] = n + 1
        out.append(token if n == 0 else f"{token}-1")
    return out


def load_mock_meta(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    mocks = load_mocks(path)
    out: dict[str, dict[str, str]] = {}
    for _, rec in mocks.iterrows():
        mid = clean(rec.get("Pasting Mocks ID")).upper()
        if not mid or mid in out:
            continue
        out[mid] = {
            "product_code": clean(rec.get("Product Code")),
            "printing_size": clean(rec.get("Printing Size")),
            "printing_position": clean(rec.get("Printing Position")),
        }
    return out


def _map_sr_size(size: str) -> str:
    s = clean(size)
    if not s:
        return ""
    mapped = map_sr_size(s)
    if mapped != s:
        return mapped
    if RE_LETTER_SIZE.match(s):
        return map_sr_size(s.upper().replace("XXL", "2XL")) or s.upper()
    return s


def slot_payload(cl_row: dict) -> dict:
    label = clean(cl_row.get("Custom Label"))
    parsed = parse_cl_mock_uid(label)
    assert parsed is not None
    mock, uid = parsed
    pos_named = []
    widths: list[str] = []
    heights: list[str] = []
    print_sizes: list[str] = []
    for n in range(1, 5):
        pos_named.append(clean(cl_row.get(f"Position {n} Name")))
        widths.append(mm_cell(cl_row.get(f"Width {n} (mm)")))
        heights.append(mm_cell(cl_row.get(f"Height {n} (mm)")))
        print_sizes.append(clean(cl_row.get(f"Print Size {n}")))

    from_pp = split_positions(clean(cl_row.get("Print Positions")))
    names: list[str] = []
    for i in range(4):
        name = pos_named[i] or (from_pp[i] if i < len(from_pp) else "")
        names.append(name)

    n_wh = 0
    for i in range(4):
        if widths[i] and heights[i]:
            n_wh = i + 1
    n_pos = 0
    for i in range(4):
        if names[i]:
            n_pos = i + 1
    n_slots = max(n_wh, n_pos, 1)

    names = names[:n_slots]
    while len(names) < n_slots:
        names.append("")

    return {
        "key": sr_key(mock, uid),
        "mock": mock,
        "uid": uid,
        "n_slots": n_slots,
        "names": names,
        "widths": widths[:n_slots] + [""] * max(0, n_slots - 4),
        "heights": heights[:n_slots] + [""] * max(0, n_slots - 4),
        "print_sizes": print_sizes[:n_slots] + [""] * max(0, n_slots - 4),
        "gender": sr_gender(clean(cl_row.get("Gender Apparel")), clean(cl_row.get("Size"))),
        "size": _map_sr_size(clean(cl_row.get("Size"))),
        "product_code_cl": clean(cl_row.get("BTC Product Code"))
        or clean(cl_row.get("Supplier Product Code")),
        "wh_score": n_wh,
        "ga_len": len(clean(cl_row.get("Gender Apparel"))),
    }


def desired_sr_rows(payload: dict, mock_meta: dict[str, dict[str, str]]) -> list[dict]:
    meta = mock_meta.get(payload["mock"], {})
    names = payload["names"]
    n = payload["n_slots"]
    suffixes = suffix_for_slots(names, n)
    printing_pos = infer_printing_position([n_ for n_ in names if n_]) or meta.get(
        "printing_position", ""
    )
    product_code = meta.get("product_code") or payload["product_code_cl"]
    guide_psize = meta.get("printing_size", "")
    nd = str(n)
    rows: list[dict] = []
    for i in range(n):
        psize = payload["print_sizes"][i] if i < len(payload["print_sizes"]) else ""
        if not psize:
            psize = guide_psize
        w = payload["widths"][i] if i < len(payload["widths"]) else ""
        h = payload["heights"][i] if i < len(payload["heights"]) else ""
        rows.append(
            {
                "SKU Value": payload["key"],
                "Number of Designs": nd,
                "Size Width": w,
                "Size Height": h,
                "Suffix": suffixes[i],
                "Gender": payload["gender"],
                "Size": payload["size"],
                "Printing Position": printing_pos,
                "Product Code": product_code,
                "Printing Size": psize,
            }
        )
    return rows
