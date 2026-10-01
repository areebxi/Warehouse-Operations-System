"""Seed extras for C800T / acrylic / iron-on / sticker / transfer labels."""
from __future__ import annotations

import re

from fill_from_seeds import clean

from add_labels_parse import (
    RE_ACRYLIC_SIZE,
    RE_C800T_AGE,
    RE_IRONON,
    RE_STICKER,
    RE_TRANSFER,
    _ACRYLIC_PAPER,
    _IRONON_PAPER,
    _age_to_size,
    _sticker_mm,
    _sticker_size,
)


def _extras_c800(
    lab: str, peers: dict[str, dict[str, str]], fieldnames: list[str]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    c800 = RE_C800T_AGE.match(lab)
    assert c800 is not None
    extras: dict[str, str] = {}
    peer: dict[str, str] | None = None
    series = c800.group(1)
    age = c800.group(2)
    extras["Size"] = _age_to_size(age)
    mock_m = re.match(r"^(M\d+)", lab, re.I)
    prefixes = [series.casefold()]
    if mock_m:
        mock_fold = mock_m.group(1).casefold()
        prefixes.extend((f"{mock_fold}-p5-c800t-", f"{mock_fold}-c800t-"))
    for prefix in prefixes:
        for key, row in peers.items():
            if key.startswith(prefix):
                peer = row
                break
        if peer:
            break
    if peer and not clean(peer.get("Print Positions")):
        extras["Print Positions"] = "Front Center"
    extras.setdefault("Print Positions", "Front Center")
    if peer:
        for col in ("Width 1 (mm)", "Height 1 (mm)", "Position 1 Name"):
            if col in fieldnames and clean(peer.get(col)):
                extras[col] = clean(peer.get(col))
        if not extras.get("Position 1 Name"):
            extras["Position 1 Name"] = "Front Center"
    return peer, extras


def _extras_acrylic(
    lab: str, peers: dict[str, dict[str, str]]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    peer = peers.get("a515-photo")
    extras: dict[str, str] = {
        "Gender Apparel": "Photo Acrylic",
        "Apparel Image": "Photo-Acrylic",
        "Print Positions": "Front Center",
        "Position 1 Name": "Front Center",
    }
    size_m = RE_ACRYLIC_SIZE.search(lab)
    if size_m and size_m.group(1) in _ACRYLIC_PAPER:
        paper, w, h = _ACRYLIC_PAPER[size_m.group(1)]
        extras["Size"] = f"{paper} {int(size_m.group(2))}mm"
        extras["Width 1 (mm)"] = w
        extras["Height 1 (mm)"] = h
    return peer, extras


def _extras_ironon(
    lab: str, peers: dict[str, dict[str, str]]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    iron_m = RE_IRONON.search(lab)
    n = iron_m.group(1) if iron_m else ""
    peer = None
    extras: dict[str, str] = {}
    if n:
        for key in (
            f"m280-p5-ironon-a{n}".casefold(),
            f"m280-p5-dtf-ironon-a{n}".casefold(),
            f"dtf-ironon-a{n}".casefold(),
        ):
            peer = peers.get(key)
            if peer:
                break
    if not peer:
        peer = (
            peers.get("dtf-ironon-a4")
            or peers.get("m262-p5-dtf-ironon-a4")
            or peers.get("p5-dtf-ironon-a4")
        )
    if n:
        extras["Size"] = f"A{n}"
        extras["Gender Apparel"] = f"DTF-IronOn-A{n}"
        extras["Colour"] = "Iron On Sticker"
        extras["Print Positions"] = "Front Center"
        extras["Position 1 Name"] = "Front Center"
        wh_mm = _IRONON_PAPER.get(n)
        if wh_mm:
            extras["Width 1 (mm)"], extras["Height 1 (mm)"] = wh_mm
    return peer, extras


def _extras_sticker(
    lab: str, peers: dict[str, dict[str, str]]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    sticker = RE_STICKER.search(lab)
    peer: dict[str, str] | None = None
    extras: dict[str, str] = {}
    if sticker:
        letter = sticker.group(1)
        inner = sticker.group(2)
        compact = inner.replace(" ", "")
        extras["Size"] = _sticker_size(inner)
        mm = _sticker_mm(inner)
        if mm:
            extras["Width 1 (mm)"], extras["Height 1 (mm)"] = mm
        extras.setdefault("Print Positions", "Front Center")
        extras.setdefault("Position 1 Name", "Front Center")
        letter_fold = letter.casefold()
        exact = [
            f"stckr-{letter}({compact})".casefold(),
            f"stckr-{letter}({inner})".casefold(),
            f"stickers-{letter}({compact})-yes".casefold(),
            f"stickers-{letter}({compact})".casefold(),
        ]
        for key in exact:
            peer = peers.get(key)
            if peer:
                break
        if not peer:
            # Same letter, other cm (L 50cm clones L 40cm — not A4 iron-on).
            for key, row in peers.items():
                if key.startswith(f"stickers-{letter_fold}(") or key.startswith(
                    f"stckr-{letter_fold}("
                ):
                    peer = row
                    if "yes" in key:
                        break
    if not peer:
        for key in ("sticker-a4", "stckr-m(30cmx30cm)", "stckr-m(30cm x 30cm)"):
            peer = peers.get(key)
            if peer:
                break
    return peer, extras


def _extras_transfer(lab: str) -> tuple[None, dict[str, str]]:
    tm = RE_TRANSFER.match(lab)
    return None, {
        "Gender Apparel": "Only-Design",
        "Size": tm.group(1).upper() if tm else "",
        "Print Positions": "Front Center",
        "Position 1 Name": "Front Center",
    }
