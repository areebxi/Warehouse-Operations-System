"""Seed extras for mock / warehouse / Amazon / Gildan / -Yes shirt labels."""
from __future__ import annotations

import re

from fill_from_seeds import apparel_image_slug, clean, hyphen_tshirt_in_slug, map_sr_size

from add_labels_parse import (
    RE_AMZ_SIZE_CODE,
    RE_GILDAN_5000,
    RE_MOCK_P_UID,
    RE_WAREHOUSE_GARMENT,
    _WAREHOUSE_COLOUR,
    _WAREHOUSE_GA,
)
from add_labels_peer_keys import _alias_shirt_colour_label
from add_labels_peer_seed import _gildan_5000_peer, _peer_for_mock_uid, _warehouse_peer


def _extras_mock(
    lab: str, peers: dict[str, dict[str, str]]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    m = RE_MOCK_P_UID.match(lab)
    assert m is not None
    mock, uid = m.group(1).upper(), m.group(2)
    p_m = re.search(r"-(P\d+)-", lab, re.I)
    p_tok = p_m.group(1).upper() if p_m else None
    peer = _peer_for_mock_uid(peers, mock, uid, p_tok)
    extras: dict[str, str] = {}
    if not p_tok:
        extras["Print Positions"] = "Front Center"
    return peer, extras


def _extras_warehouse(
    lab: str,
    peers: dict[str, dict[str, str]],
    sku_uids: dict[str, str] | None,
) -> tuple[dict[str, str] | None, dict[str, str]]:
    wh = RE_WAREHOUSE_GARMENT.match(lab)
    assert wh is not None
    g, typ, col, sz = (wh.group(i).upper() for i in range(1, 5))
    peer = _warehouse_peer(peers, g, typ, col, sz)
    ga = _WAREHOUSE_GA.get((g, typ), "")
    colour = _WAREHOUSE_COLOUR.get(col.casefold(), "")
    if not colour and peer:
        colour = clean(peer.get("Colour"))
    size = map_sr_size(sz) or sz
    extras: dict[str, str] = {
        "Gender Apparel": ga,
        "Colour": colour,
        "Size": size,
        "Print Positions": "Front Center",
        "Position 1 Name": "Front Center",
    }
    slug = apparel_image_slug(ga, colour)
    if slug:
        extras["Apparel Image"] = slug
    uid = (sku_uids or {}).get(lab.casefold(), "")
    if uid:
        extras["Supplier SKU"] = uid
    return peer, extras


def _extras_amz(
    lab: str, peers: dict[str, dict[str, str]], fieldnames: list[str]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    amz = RE_AMZ_SIZE_CODE.match(lab)
    assert amz is not None
    fam = amz.group(1)
    d_tok, e_tok = amz.group(3), amz.group(4)
    prefix = f"{fam.casefold()}-"
    suffix = f"-{d_tok.casefold()}-{e_tok.casefold()}"
    colour_peer: dict[str, str] | None = None
    size_peer: dict[str, str] | None = None
    for key, row in peers.items():
        if key.startswith(prefix) and colour_peer is None:
            colour_peer = row
        if key.endswith(suffix):
            size_peer = row
    peer = colour_peer
    extras: dict[str, str] = {
        "Print Positions": (
            clean((colour_peer or {}).get("Print Positions")) or "Front Center"
        ),
        "Position 1 Name": "Front Center",
    }
    if size_peer and clean(size_peer.get("Size")):
        extras["Size"] = clean(size_peer.get("Size"))
    if peer:
        for copy_col in ("Width 1 (mm)", "Height 1 (mm)"):
            if copy_col in fieldnames and clean(peer.get(copy_col)):
                extras[copy_col] = clean(peer.get(copy_col))
        if size_peer:
            for copy_col in ("Width 1 (mm)", "Height 1 (mm)"):
                if copy_col in fieldnames and clean(size_peer.get(copy_col)):
                    extras[copy_col] = clean(size_peer.get(copy_col))
    return peer, extras


def _extras_gildan(
    lab: str, peers: dict[str, dict[str, str]], fieldnames: list[str]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    g5000 = RE_GILDAN_5000.match(lab)
    assert g5000 is not None
    col, sz = g5000.group(1), g5000.group(2)
    peer = _gildan_5000_peer(peers, col, sz)
    extras: dict[str, str] = {
        "Print Positions": (
            clean(peer.get("Print Positions")) if peer else ""
        ) or "Front Center",
        "Position 1 Name": "Front Center",
    }
    if peer:
        for copy_col in ("Width 1 (mm)", "Height 1 (mm)", "Position 1 Name"):
            if copy_col in fieldnames and clean(peer.get(copy_col)):
                extras[copy_col] = clean(peer.get(copy_col))
        img = hyphen_tshirt_in_slug(clean(peer.get("Apparel Image")))
        if img:
            extras["Apparel Image"] = img
        else:
            slug = apparel_image_slug(
                clean(peer.get("Gender Apparel")), clean(peer.get("Colour"))
            )
            if slug:
                extras["Apparel Image"] = slug
    return peer, extras


def _extras_yes_shirt(
    lab: str, peers: dict[str, dict[str, str]]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    stripped = lab.rsplit("-", 1)[0]
    peer = peers.get(stripped.casefold())
    if not peer:
        aliased = _alias_shirt_colour_label(stripped)
        peer = peers.get(aliased.casefold())
        if not peer:
            prefix = aliased.casefold()
            for key, row in peers.items():
                if key == prefix or key.startswith(prefix + "-"):
                    peer = row
                    if clean(row.get("Print Positions")) == "Front Center":
                        break
    return peer, {}
