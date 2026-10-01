"""Size References lookup for phase5_print_sizes."""
from __future__ import annotations

import re

from phase5_helpers import clean, infer_printing_position, is_age_size
from phase5_loaders import _block_from_rows


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

    if s.endswith("-BS") and len(s) > 3:
        base = s[: -len("-BS")]
        if base and base != s:
            cands.append(base)

    if s.startswith("BG-") and len(s) > len("BG-"):
        cands.append(s.replace("BG-", "", 1))
        remainder = s.replace("BG-", "", 1)
        if "CHINA" in remainder and "BAG" in remainder:
            cands.append("BG-" + remainder.replace("-", ""))

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
    if "" not in genders_try:
        genders_try.append("")

    ga_keys = normalize_gender_apparel_for_sr_sku(gender_apparel)

    inside = ""
    m_inside = re.search(r"-(?:P\d+-)?(\d+)$", clean(custom_label).upper())
    if m_inside:
        inside = m_inside.group(1)

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
