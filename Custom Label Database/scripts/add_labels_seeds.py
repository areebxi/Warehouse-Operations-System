"""Build blank-seed CL rows for named labels (peer clone + extras)."""
from __future__ import annotations

import pandas as pd

from add_labels_parse import (
    RE_ACRYLIC_SIZE,
    RE_AMZ_SIZE_CODE,
    RE_BAG_COLOUR,
    RE_BAG_SIZE_YES,
    RE_C800T_AGE,
    RE_GILDAN_5000,
    RE_IRONON,
    RE_MOCK_P_UID,
    RE_STICKER,
    RE_TRANSFER,
    RE_WAREHOUSE_GARMENT,
)
from add_labels_peer_seed import _expand_all_spc, _seed_from_peer
from add_labels_seed_bag import _extras_bag, _extras_bag_size
from add_labels_seed_garment import (
    _extras_amz,
    _extras_gildan,
    _extras_mock,
    _extras_warehouse,
    _extras_yes_shirt,
)
from add_labels_seed_special import (
    _extras_acrylic,
    _extras_c800,
    _extras_ironon,
    _extras_sticker,
    _extras_transfer,
)


def _peer_and_extras(
    lab: str,
    *,
    fieldnames: list[str],
    peers: dict[str, dict[str, str]],
    sku_uids: dict[str, str] | None,
) -> tuple[dict[str, str] | None, dict[str, str]]:
    if RE_C800T_AGE.match(lab):
        return _extras_c800(lab, peers, fieldnames)
    if "ACPPLQ" in lab.upper() or RE_ACRYLIC_SIZE.search(lab):
        return _extras_acrylic(lab, peers)
    if RE_IRONON.search(lab) or "ironon" in lab.casefold().replace("-", "").replace(" ", ""):
        return _extras_ironon(lab, peers)
    if RE_BAG_SIZE_YES.match(lab):
        return _extras_bag_size(lab, peers, fieldnames)
    if RE_MOCK_P_UID.match(lab):
        return _extras_mock(lab, peers)
    if RE_BAG_COLOUR.match(lab):
        return _extras_bag(lab, peers, fieldnames)
    if RE_STICKER.search(lab) or "sticker" in lab.casefold():
        return _extras_sticker(lab, peers)
    if RE_TRANSFER.match(lab):
        return _extras_transfer(lab)
    if RE_WAREHOUSE_GARMENT.match(lab):
        return _extras_warehouse(lab, peers, sku_uids)
    if RE_AMZ_SIZE_CODE.match(lab):
        return _extras_amz(lab, peers, fieldnames)
    if RE_GILDAN_5000.match(lab):
        return _extras_gildan(lab, peers, fieldnames)
    if lab.rsplit("-", 1)[-1].casefold() == "yes":
        return _extras_yes_shirt(lab, peers)
    return None, {}


def build_seed_rows(
    labels: list[str],
    *,
    fieldnames: list[str],
    existing: set[str],
    peers: dict[str, dict[str, str]],
    pe_index: pd.DataFrame | None,
    all_spc: bool,
    sku_uids: dict[str, str] | None = None,
) -> tuple[list[dict[str, str]], list[str]]:
    """Return (new rows, skipped reasons)."""
    skipped: list[str] = []
    wanted: list[str] = []
    seen: set[str] = set()

    for lab in labels:
        expand = (
            _expand_all_spc(lab, peers, pe_index)
            if all_spc and pe_index is not None
            else [lab]
        )
        for item in expand:
            k = item.casefold()
            if k in existing or k in seen:
                skipped.append(f"exists:{item}")
                continue
            seen.add(k)
            wanted.append(item)

    new_rows: list[dict[str, str]] = []
    for lab in wanted:
        peer, extras = _peer_and_extras(
            lab, fieldnames=fieldnames, peers=peers, sku_uids=sku_uids
        )
        new_rows.append(_seed_from_peer(fieldnames, lab, peer, extras=extras))
    return new_rows, skipped
