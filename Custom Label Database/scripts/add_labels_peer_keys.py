"""Peer lookup keys for named Custom Labels."""
from __future__ import annotations

import re

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
    _SHIRT_COLOUR_ALIAS,
)


def _alias_shirt_colour_label(label: str) -> str:
    """Rewrite one colour token for peer lookup. Custom Label itself stays unchanged."""
    parts = label.split("-")
    out: list[str] = []
    changed = False
    for p in parts:
        alias = _SHIRT_COLOUR_ALIAS.get(p.casefold())
        if alias and not changed:
            out.append(alias.upper())
            changed = True
        else:
            out.append(p)
    return "-".join(out)


def _peer_keys_for_label(label: str) -> set[str]:
    keys: set[str] = set()
    m = RE_MOCK_P_UID.match(label)
    c800 = RE_C800T_AGE.match(label)
    bag = RE_BAG_COLOUR.match(label)
    if c800:
        keys.add(f"__prefix__:{c800.group(1).casefold()}")
        mock = re.match(r"^(M\d+)", label, re.I)
        if mock:
            m = mock.group(1).casefold()
            keys.add(f"__prefix__:{m}-p5-c800t-")
            keys.add(f"__prefix__:{m}-c800t-")
        return keys
    if "ACPPLQ" in label.upper() or RE_ACRYLIC_SIZE.search(label):
        keys.add("a515-photo")
        return keys
    if RE_IRONON.search(label) or "ironon" in label.casefold().replace("-", "").replace(" ", ""):
        iron_m = RE_IRONON.search(label)
        if iron_m:
            n = iron_m.group(1)
            keys.add(f"m280-p5-ironon-a{n}".casefold())
            keys.add(f"m280-p5-dtf-ironon-a{n}".casefold())
            keys.add(f"dtf-ironon-a{n}".casefold())
        keys.add("dtf-ironon-a4")
        keys.add("m262-p5-dtf-ironon-a4")
        keys.add("p5-dtf-ironon-a4")
        return keys
    bag_sz = RE_BAG_SIZE_YES.match(label)
    if bag_sz:
        prod, col, sz = bag_sz.group(1), bag_sz.group(2), bag_sz.group(3)
        keys.add(label.casefold())
        keys.add(f"{prod}-{col}-{sz}-yes".casefold())
        keys.add(f"__prefix__:{prod.casefold()}-{col.casefold()}-")
        if not prod.upper().startswith("BG-"):
            keys.add(f"__prefix__:bg-{prod.casefold()}-{col.casefold()}-")
        return keys
    if m:
        mock, uid = m.group(1).upper(), m.group(2)
        p_m = re.search(r"-(P\d+)-", label, re.I)
        p_tok = p_m.group(1).upper() if p_m else None
        if p_tok:
            keys.add(f"{mock}-{p_tok}-{uid}".casefold())
        for p in ("P5", "P3", "P6", "P7", "P1"):
            keys.add(f"{mock}-{p}-{uid}".casefold())
        keys.add(f"{mock}-{uid}".casefold())
        # Same-UID other mock (e.g. M260-P5-3263 → M76-3263 garment clone)
        keys.add(f"__suffix__:-{uid.casefold()}")
        # ponytail: alnum trailing codes (1D114) are not PE UIDs — acrylic default peer.
        if any(ch.isalpha() for ch in uid):
            keys.add("a515-photo")
        return keys
    if bag:
        prod = bag.group(1).upper()
        keys.add(f"__prefix__:{prod.casefold()}-")
        if not prod.startswith("BG-"):
            keys.add(f"__prefix__:bg-{prod.casefold()}-")
        keys.add("__prefix__:w101-")
        keys.add("__prefix__:bg-w101")
        return keys
    sticker = RE_STICKER.search(label)
    if sticker or "sticker" in label.casefold():
        keys.add("sticker-a4")
        keys.add("stckr-m(30cmx30cm)")
        keys.add("stckr-m(30cm x 30cm)")
        if sticker:
            letter = sticker.group(1)
            inner = sticker.group(2)
            compact = inner.replace(" ", "")
            keys.add(f"stckr-{letter}({compact})".casefold())
            keys.add(f"stckr-{letter}({inner})".casefold())
            keys.add(f"__prefix__:stckr-{letter.casefold()}(")
            keys.add(f"__prefix__:stickers-{letter.casefold()}(")
        return keys
    if RE_TRANSFER.match(label):
        keys.add("only-design")
        return keys
    garment = RE_WAREHOUSE_GARMENT.match(label)
    if garment:
        g, typ, col, sz = (garment.group(i).upper() for i in range(1, 5))
        keys.add(label.casefold())
        keys.add(f"__prefix__:{g.casefold()}-{typ.casefold()}-{col.casefold()}-")
        for og in ("M", "W", "K"):
            keys.add(f"{og}-{typ}-{col}-{sz}".casefold())
        return keys
    amz = RE_AMZ_SIZE_CODE.match(label)
    if amz:
        fam, _mid, d_tok, e_tok = amz.group(1), amz.group(2), amz.group(3), amz.group(4)
        keys.add(label.casefold())
        keys.add(f"__prefix__:{fam.casefold()}-")
        keys.add(f"__suffix__:-{d_tok.casefold()}-{e_tok.casefold()}")
        return keys
    gildan = RE_GILDAN_5000.match(label)
    if gildan:
        col, sz = gildan.group(1), gildan.group(2)
        keys.add(label.casefold())
        keys.add(f"a3-5000-{col}-{sz}".casefold())
        keys.add(f"__prefix__:a3-5000-{col.casefold()}-")
        return keys
    if label.rsplit("-", 1)[-1].casefold() == "yes":
        stripped = label.rsplit("-", 1)[0]
        keys.add(stripped.casefold())
        parts = stripped.split("-")
        if len(parts) >= 2:
            # F/B-M-T-NVY-S-YES → family peers F/B-M-T-NVY-L-YES (size missing).
            keys.add(f"__prefix__:{'-'.join(parts[:-1]).casefold()}-")
        aliased = _alias_shirt_colour_label(stripped)
        if aliased.casefold() != stripped.casefold():
            keys.add(aliased.casefold())
            keys.add(f"__prefix__:{aliased.casefold()}")
            keys.add(f"__prefix__:{aliased.casefold()}-")
            a_parts = aliased.split("-")
            if len(a_parts) >= 2:
                keys.add(f"__prefix__:{'-'.join(a_parts[:-1]).casefold()}-")
        return keys
    return keys
