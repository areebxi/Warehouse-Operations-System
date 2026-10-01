"""Size References lookup for fill_from_seeds."""
from __future__ import annotations

import re

from fill_seeds_apparel import is_age_size, normalize_gender_apparel_for_sr_sku
from fill_seeds_size_ref import _block_from_rows, pick_pc_block
from fill_seeds_util import clean

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

