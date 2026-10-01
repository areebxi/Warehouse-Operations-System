"""Seed extras for bag colour / bag size-Yes labels."""
from __future__ import annotations

from fill_from_seeds import apparel_image_slug, clean, hyphen_tshirt_in_slug, map_sr_size

from add_labels_parse import (
    RE_BAG_COLOUR,
    RE_BAG_SIZE_YES,
    _BAG_COLOUR,
    _BAG_SIZE_NAME,
    _bag_ga,
)


def _extras_bag_size(
    lab: str, peers: dict[str, dict[str, str]], fieldnames: list[str]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    bag_sz = RE_BAG_SIZE_YES.match(lab)
    assert bag_sz is not None
    prod, col_tok, sz_tok = (
        bag_sz.group(1),
        bag_sz.group(2),
        bag_sz.group(3),
    )
    colour = _BAG_COLOUR.get(col_tok.casefold(), "")
    size_name = _BAG_SIZE_NAME.get(sz_tok.casefold(), map_sr_size(sz_tok) or sz_tok)
    peer: dict[str, str] | None = None
    extras: dict[str, str] = {}
    # Prefer exact size peer, else same family (L often shares XL bag mm).
    prefer = [
        f"{prod}-{col_tok}-{sz_tok}-yes".casefold(),
        f"bg-{prod}-{col_tok}-{sz_tok}-yes".casefold()
        if not prod.upper().startswith("BG-")
        else "",
    ]
    for key in prefer:
        if key and key in peers:
            peer = peers[key]
            break
    if not peer:
        prefix = f"{prod.casefold()}-{col_tok.casefold()}-"
        bg_prefix = (
            f"bg-{prod.casefold()}-{col_tok.casefold()}-"
            if not prod.upper().startswith("BG-")
            else ""
        )
        same_sz: dict[str, str] | None = None
        family: dict[str, str] | None = None
        for key, row in peers.items():
            if not (key.startswith(prefix) or (bg_prefix and key.startswith(bg_prefix))):
                continue
            if f"-{sz_tok.casefold()}-" in f"-{key}-" or key.endswith(
                f"-{sz_tok.casefold()}-yes"
            ):
                same_sz = row
                break
            if family is None:
                family = row
            # Prefer Large/XL mm for L when exact missing (W415 peers).
            if sz_tok.casefold() == "l" and (
                "-xl-" in key or key.endswith("-xl-yes") or "-l-" in key
            ):
                family = row
        peer = same_sz or family
    extras["Gender Apparel"] = _bag_ga(prod, peer)
    if colour:
        extras["Colour"] = colour
    extras["Size"] = size_name
    extras["Print Positions"] = (
        clean(peer.get("Print Positions")) if peer else ""
    ) or "Front Center"
    extras["Position 1 Name"] = "Front Center"
    if peer:
        for col in ("Brand", "Category", "Department", "Width 1 (mm)", "Height 1 (mm)"):
            if col in fieldnames and clean(peer.get(col)):
                extras[col] = clean(peer.get(col))
        # L missing on W415: other L bags / XL are 267×378.
        if sz_tok.casefold() == "l" and not extras.get("Width 1 (mm)"):
            for key, row in peers.items():
                if clean(row.get("Size")).casefold() == "large" and clean(
                    row.get("Width 1 (mm)")
                ):
                    extras["Width 1 (mm)"] = clean(row.get("Width 1 (mm)"))
                    extras["Height 1 (mm)"] = clean(row.get("Height 1 (mm)"))
                    break
    img = hyphen_tshirt_in_slug(clean(peer.get("Apparel Image")) if peer else "")
    if img:
        extras["Apparel Image"] = img
    elif extras.get("Gender Apparel") and extras.get("Colour"):
        slug = apparel_image_slug(extras["Gender Apparel"], extras["Colour"])
        if slug:
            extras["Apparel Image"] = slug
    return peer, extras


def _extras_bag(
    lab: str, peers: dict[str, dict[str, str]], fieldnames: list[str]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    bag = RE_BAG_COLOUR.match(lab)
    assert bag is not None
    code = bag.group(2)
    colour = _BAG_COLOUR.get(code.casefold(), "")
    prod = bag.group(1).upper()
    peer: dict[str, str] | None = None
    extras: dict[str, str] = {}
    for key, row in peers.items():
        if key.startswith(prod.casefold() + "-") or key.startswith(
            ("bg-" + prod.casefold() + "-") if not prod.startswith("BG") else prod.casefold()
        ):
            peer = row
            break
    if not peer:
        for key, row in peers.items():
            if "w101" in key and prod.upper().endswith("W101"):
                peer = row
                break
    if colour:
        extras["Colour"] = colour
        extras["Gender Apparel"] = _bag_ga(prod, peer)
        extras["Apparel Image"] = f"{extras['Gender Apparel']}-{colour}".replace(
            " ", "-"
        )
        extras["Size"] = (clean(peer.get("Size")) if peer else "") or "Standard Size"
        extras["Print Positions"] = (
            clean(peer.get("Print Positions")) if peer else ""
        ) or "Front Center"
        if peer:
            for col in ("Brand", "Category", "Department", "Width 1 (mm)", "Height 1 (mm)", "Position 1 Name"):
                if col in fieldnames and clean(peer.get(col)):
                    extras[col] = clean(peer.get(col))
    return peer, extras
