"""
Fast Custom Label add: seed → same fill_from_seeds steps → append-only write.

Integrity: existing CL rows are never rewritten (append only). Fill rules are
the same blank-only / PE / print / Customise steps as fill_from_seeds.py.
Backup before write (unless --no-backup).

Default = **named labels only** (fast). Use --all-spc to also seed every PE
UID for that BTC SPC (slower; catalog completeness).

  python scripts/add_labels.py M260-P3-3265 W101-SkyBe-O/S-Yes
  python scripts/add_labels.py --skus 10428ALG-M260-P3-3265 128967LG-W101-SkyBe-O/S-Yes
  python scripts/add_labels.py --all-spc --skus 10428ALG-M260-P3-3265
  python scripts/add_labels.py --dry-run --skus ...
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(_WAREHOUSE))

from shared import paths as wh  # noqa: E402
from shared.cl_sku_match import key_after_first_dash  # noqa: E402

from fill_from_seeds import (  # noqa: E402
    DEFAULT_CONFIG,
    DEFAULT_PE,
    DEFAULT_PRINT_SIZES,
    apparel_image_slug,
    hyphen_tshirt_in_slug,
    clean,
    customise_for_label,
    load_pe_index,
    load_print_sizes,
    load_size_ref_index,
    load_overrides,
    map_sr_size,
    pe_sizes_from_index,
    step_apparel_image,
    step_areeb,
    step_customise,
    step_dedicated_suppliers,
    step_pe_enrich,
    step_print_sizes,
    step_printing_type,
    step_supplier_name,
    step_supplier_sku,
    step_supply,
    uid_from_custom_label,
)

SEED_COLS = (
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
    "Customise",
)

RE_MOCK_P_UID = re.compile(r"^(M\d+)(?:-P\d+)?-(\d+)$", re.I)
RE_MOCK_TOKEN = re.compile(r"^(M\d+)(?:-P\d+)?-", re.I)
RE_C800T_AGE = re.compile(
    # Optional -P# — listing SKUs sometimes omit it (M281-C800T-30-3>6).
    # ShipStation / HTML sometimes encodes > as &gt;.
    r"^(M\d+(?:-P\d+)?-C800T-\d+-)(\d+(?:>|&gt;)\d+|\d+-\d+)$",
    re.I,
)
# A515-PHOTO = A5 15mm. A410 in P5-ACPPLQ-A410-PB = A4 10mm. A625 = A6 25mm.
RE_ACRYLIC_SIZE = re.compile(r"(?:^|-)A([4-6])(\d{2})(?:-|$)", re.I)
_ACRYLIC_PAPER = {"4": ("A4", "210", "297"), "5": ("A5", "148", "210"), "6": ("A6", "105", "148")}
RE_BAG_COLOUR = re.compile(r"^(W\d+|BG-W\d+|BG-[A-Z0-9]+)-([A-Za-z0-9]+)-O/S", re.I)
# Optional DTF- prefix: M280-P5-IronOn-A6 and M280-P5-DTF-IronOn-A6.
RE_IRONON = re.compile(r"(?:DTF-)?IronOn-A(\d+)", re.I)
_IRONON_PAPER = {"4": ("210", "297"), "5": ("148", "210"), "6": ("105", "148")}
RE_STICKER = re.compile(r"(?:STICKERS?|STCKR)-([A-Z])\s*\(([^)]+)\)", re.I)
# Packing SKU DTF-Transfer-1M-1 → Custom Label Transfer-1M-1 (after first dash).
RE_TRANSFER = re.compile(r"^Transfer-(\d+M)(?:-\d+)?$", re.I)
# Warehouse garment: W-H-BLK-M / M-T-BLK-M / K-H-DHR-YXS (gender-type-colour-size).
RE_WAREHOUSE_GARMENT = re.compile(
    r"^(M|W|K)-(T|H|SS|SW|PS)-([A-Za-z0-9]+)-"
    r"(Y(?:2XL|XS|XL|S|M|L)|(?:[2-5]XL|XXL|XS|XL|S|M|L))$",
    re.I,
)
# Gildan Heavy Cotton style code in the packing SKU after first dash: 5000-NAT-S
_SIZE_TOKEN = r"(Y(?:2XL|XS|XL|S|M|L)|(?:[2-5]XL|XXL|XS|XL|S|M|L))"
RE_GILDAN_5000 = re.compile(rf"^5000-([A-Za-z0-9]+)-{_SIZE_TOKEN}$", re.I)
# W415-NAT-L-Yes / BG-W530-NAT-L-Yes (letter size, not O/S).
RE_BAG_SIZE_YES = re.compile(
    rf"^(W\d+|BG-W\d+)-([A-Za-z0-9]+)-{_SIZE_TOKEN}-Yes$",
    re.I,
)
_BAG_SIZE_NAME = {
    "xxs": "Extra Extra Small",
    "xs": "Extra Small",
    "s": "Small",
    "m": "Medium",
    "l": "Large",
    "xl": "Extra Large",
    "2xl": "2XL",
    "3xl": "3XL",
    "yxs": "YXS",
    "ys": "YS",
    "ym": "YM",
    "yl": "YL",
    "yxl": "YXL",
    "y2xl": "Y2XL",
}
_WAREHOUSE_GA = {
    ("M", "T"): "Mens-T-Shirt",
    ("W", "T"): "Womens-T-Shirt",
    ("K", "T"): "Kids-T-Shirt",
    ("M", "H"): "Mens-Hoodie",
    ("W", "H"): "Womens-Hoodie",
    ("K", "H"): "Kids-Hoodie",
    ("M", "SW"): "Mens-Sweatshirt",
    ("W", "SW"): "Womens-Sweatshirt",
    ("K", "SW"): "Kids-Sweatshirt",
}
_WAREHOUSE_COLOUR = {
    "blk": "Black",
    "whi": "White",
}

# Abbrev colour codes seen on bag Custom Labels → Colour name
_BAG_COLOUR = {
    "skybe": "Sky Blue",
    "clard": "Classic Red",
    "clardow": "Classic Red-Off White",
    "frenyow": "French Navy-Off White",
    "blabk": "Black-Black",
    "limgn": "Lime",
    "dusbe": "Dusty Blue",
    "nat": "Natural",
    "blk": "Black",
    "nvy": "Navy",
    "red": "Red",
    "bur": "Burgundy",
    "cpnk": "Classic Pink",
}

# Supervisor 15 Sep 2026: packing shirt colour tokens that are not the CL code.
# Peer lookup only — Custom Label keeps NAV / PUE.
_SHIRT_COLOUR_ALIAS = {
    "nav": "nvy",  # Navy
    "pue": "prp",  # Purple
}


def label_from_input(raw: str, *, from_sku: bool) -> str:
    s = clean(raw)
    if not s:
        return ""
    if from_sku:
        after = key_after_first_dash(s)
        return after or s
    # packing SKU pasted without flag: has design prefix then mock/bag tail
    if re.match(r"^\d+[A-Za-z]*-", s) and key_after_first_dash(s):
        return key_after_first_dash(s)
    return s


def _age_to_size(token: str) -> str:
    t = token.replace("&gt;", "-").replace(">", "-")
    if re.fullmatch(r"\d+-\d+", t):
        return f"{t} Months"
    return t


def _sticker_size(inner: str) -> str:
    compact = re.sub(r"\s+", "", clean(inner))
    return re.sub(r"[x×]", " x ", compact, count=1, flags=re.I)


def _sticker_mm(inner: str) -> tuple[str, str] | None:
    """50cmx50cm → ('500', '500'). Token drives mm; peer mm may be blank/wrong letter."""
    nums = re.findall(r"(\d+)\s*cm", clean(inner), flags=re.I)
    if len(nums) >= 2:
        return str(int(nums[0]) * 10), str(int(nums[1]) * 10)
    if len(nums) == 1:
        mm = str(int(nums[0]) * 10)
        return mm, mm
    return None


def _bag_ga(prod: str, peer: dict[str, str] | None) -> str:
    ga = clean(peer.get("Gender Apparel")) if peer else ""
    if ga.startswith("BG-"):
        return ga
    if prod.upper().startswith("BG-"):
        return prod.upper()
    if prod.upper().startswith("W"):
        return f"BG-{prod.upper()}"
    return ga or prod


_PEER_KEEP = (
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
    "Customise",
    "Supplier Product Code",
    "Supplier SKU",
    "Brand",
    "Category",
    "Department",
    "Sub-Category",
    "Sub-Department",
    "Width 1 (mm)",
    "Height 1 (mm)",
    "Position 1 Name",
)


def _slim_peer(r: dict[str, str], fieldnames: list[str]) -> dict[str, str]:
    keep = [c for c in _PEER_KEEP if c in fieldnames]
    return {c: clean(r.get(c)) for c in keep}


def _scan_existing(path: Path) -> tuple[list[str], set[str]]:
    """Fast pass: fieldnames + existing Custom Label set only."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        fieldnames = next(reader)
        try:
            lab_i = fieldnames.index("Custom Label")
        except ValueError as exc:
            raise ValueError("CL CSV missing Custom Label column") from exc
        existing: set[str] = set()
        for row in reader:
            if lab_i >= len(row):
                continue
            lab = row[lab_i].strip()
            if lab:
                existing.add(lab.casefold())
    return fieldnames, existing


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
        for p in ("P5", "P3", "P6"):
            keys.add(f"{mock}-{p}-{uid}".casefold())
        keys.add(f"{mock}-{uid}".casefold())
        # Same-UID other mock (e.g. M260-P5-3263 → M76-3263 garment clone)
        keys.add(f"__suffix__:-{uid}")
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
        aliased = _alias_shirt_colour_label(stripped)
        if aliased.casefold() != stripped.casefold():
            keys.add(aliased.casefold())
            keys.add(f"__prefix__:{aliased.casefold()}")
            keys.add(f"__prefix__:{aliased.casefold()}-")
        return keys
    return keys


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


def _collect_peers_for_labels(
    path: Path, fieldnames: list[str], labels: list[str]
) -> dict[str, dict[str, str]]:
    exact: set[str] = set()
    prefixes: list[str] = []
    suffixes: list[str] = []
    for lab in labels:
        for item in _peer_keys_for_label(lab):
            if item.startswith("__prefix__:"):
                prefixes.append(item.split(":", 1)[1])
            elif item.startswith("__suffix__:"):
                suffixes.append(item.split(":", 1)[1].casefold())
            else:
                exact.add(item)
    if not exact and not prefixes and not suffixes:
        return {}
    peers: dict[str, dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lab = clean(r.get("Custom Label"))
            if not lab:
                continue
            key = lab.casefold()
            if (
                key not in exact
                and not any(key.startswith(p) for p in prefixes)
                and not any(key.endswith(s) for s in suffixes)
            ):
                continue
            prev = peers.get(key)
            slim = _slim_peer(r, fieldnames)
            if prev is None:
                peers[key] = slim
            elif slim.get("Gender Apparel", "").startswith("FOTL") and not prev.get(
                "Gender Apparel", ""
            ).startswith("FOTL"):
                peers[key] = slim
    return peers


def _peer_for_mock_uid(
    peers: dict[str, dict[str, str]], mock: str, uid: str, prefer_p: str | None
) -> dict[str, str] | None:
    mock = mock.upper()
    candidates: list[str] = []
    if prefer_p:
        candidates.append(f"{mock}-{prefer_p}-{uid}")
    candidates.extend(
        [
            f"{mock}-P5-{uid}",
            f"{mock}-P3-{uid}",
            f"{mock}-P6-{uid}",
            f"{mock}-{uid}",
        ]
    )
    for lab in candidates:
        hit = peers.get(lab.casefold())
        if hit:
            return hit
    # any same-UID row on this mock, else best other mock with this UID (garment)
    suffix = f"-{uid}".casefold()
    same_mock: dict[str, str] | None = None
    other: list[dict[str, str]] = []
    for key, row in peers.items():
        if not key.endswith(suffix):
            continue
        if key.startswith(mock.casefold()):
            if same_mock is None:
                same_mock = row
            continue
        other.append(row)
    if same_mock:
        return same_mock

    def _score(row: dict[str, str]) -> tuple[int, int, int]:
        ga = clean(row.get("Gender Apparel", ""))
        pp = clean(row.get("Print Positions", "")).casefold()
        img = clean(row.get("Apparel Image", ""))
        front = 1 if pp == "front center" else 0
        fotl = 1 if ga.startswith("FOTL") else 0
        img_ok = 1 if img.startswith("Fruit-Of-The-Loom") or img.startswith("FOTL-") else 0
        return (front, fotl, img_ok)

    if other:
        other.sort(key=_score, reverse=True)
        return other[0]
    return None


def _seed_from_peer(
    fieldnames: list[str], label: str, peer: dict[str, str] | None, *, extras: dict[str, str] | None = None
) -> dict[str, str]:
    row = {c: "" for c in fieldnames}
    row["Custom Label"] = label
    row["Customise"] = customise_for_label(label)
    if peer:
        for col in ("Gender Apparel", "Colour", "Size", "Apparel Image", "Print Positions"):
            if col in row:
                val = clean(peer.get(col))
                if col == "Apparel Image":
                    val = hyphen_tshirt_in_slug(val)
                row[col] = val
        # Prefer Front Center from mocks when peer Print Positions blank
        if not row.get("Print Positions"):
            row["Print Positions"] = "Front Center"
    if extras:
        for k, v in extras.items():
            if k in row and v:
                row[k] = v
    if not row.get("Print Positions") and (
        RE_MOCK_TOKEN.match(label) or re.search(r"(?:^|-)P\d+-", label, re.I)
    ):
        row["Print Positions"] = "Front Center"
    return row


def _expand_all_spc(
    label: str,
    peers: dict[str, dict[str, str]],
    pe_index: pd.DataFrame,
) -> list[str]:
    """If label is mock(+P)-UID and peer has SPC, return all PE UIDs as same mock pattern."""
    m = RE_MOCK_P_UID.match(label)
    if not m:
        return [label]
    mock, uid = m.group(1).upper(), m.group(2)
    p_m = re.search(r"-(P\d+)-", label, re.I)
    p_tok = p_m.group(1).upper() if p_m else None
    peer = _peer_for_mock_uid(peers, mock, uid, p_tok)
    spc = clean(peer.get("Supplier Product Code")) if peer else ""
    if not spc and uid in pe_index.index:
        spc = clean(pe_index.at[uid, "SPC"]) if "SPC" in pe_index.columns else ""
    if not spc:
        return [label]
    prefix = f"{mock}-{p_tok}-" if p_tok else f"{mock}-"
    out: list[str] = []
    for pe_uid in pe_index.index.astype(str):
        u = clean(pe_uid)
        if not u or clean(pe_index.at[pe_uid, "SPC"]) != spc:
            continue
        out.append(f"{prefix}{u}")
    return out or [label]


def _warehouse_peer(
    peers: dict[str, dict[str, str]], g: str, typ: str, col: str, sz: str
) -> dict[str, str] | None:
    for og in (g, "M", "W", "K"):
        hit = peers.get(f"{og}-{typ}-{col}-{sz}".casefold())
        if hit:
            return hit
    prefix = f"{g.casefold()}-{typ.casefold()}-{col.casefold()}-"
    for key, row in peers.items():
        if key.startswith(prefix):
            return row
    return None


def _gildan_5000_peer(
    peers: dict[str, dict[str, str]], col: str, sz: str
) -> dict[str, str] | None:
    for lab in (f"A3-5000-{col}-{sz}", f"5000-{col}-{sz}", f"A3-5000-{col}-{sz}-YES"):
        hit = peers.get(lab.casefold())
        if hit:
            return hit
    prefix = f"a3-5000-{col.casefold()}-"
    for key, row in peers.items():
        if key.startswith(prefix):
            return row
    return None


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
        extras: dict[str, str] = {}
        peer: dict[str, str] | None = None

        m = RE_MOCK_P_UID.match(lab)
        c800 = RE_C800T_AGE.match(lab)
        bag = RE_BAG_COLOUR.match(lab)
        bag_sz = RE_BAG_SIZE_YES.match(lab)

        if c800:
            # clone nearest same-series C800T row (P5 cousin if this label omitted -P#-)
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
        elif "ACPPLQ" in lab.upper() or RE_ACRYLIC_SIZE.search(lab):
            peer = peers.get("a515-photo")
            extras["Gender Apparel"] = "Photo Acrylic"
            extras["Apparel Image"] = "Photo-Acrylic"
            extras["Print Positions"] = "Front Center"
            extras["Position 1 Name"] = "Front Center"
            size_m = RE_ACRYLIC_SIZE.search(lab)
            if size_m and size_m.group(1) in _ACRYLIC_PAPER:
                paper, w, h = _ACRYLIC_PAPER[size_m.group(1)]
                extras["Size"] = f"{paper} {int(size_m.group(2))}mm"
                extras["Width 1 (mm)"] = w
                extras["Height 1 (mm)"] = h
        elif RE_IRONON.search(lab) or "ironon" in lab.casefold().replace("-", "").replace(" ", ""):
            iron_m = RE_IRONON.search(lab)
            n = iron_m.group(1) if iron_m else ""
            peer = None
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
        elif bag_sz:
            prod, col_tok, sz_tok = (
                bag_sz.group(1),
                bag_sz.group(2),
                bag_sz.group(3),
            )
            colour = _BAG_COLOUR.get(col_tok.casefold(), "")
            size_name = _BAG_SIZE_NAME.get(sz_tok.casefold(), map_sr_size(sz_tok) or sz_tok)
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
        elif m:
            mock, uid = m.group(1).upper(), m.group(2)
            p_m = re.search(r"-(P\d+)-", lab, re.I)
            p_tok = p_m.group(1).upper() if p_m else None
            peer = _peer_for_mock_uid(peers, mock, uid, p_tok)
            if not p_tok:
                extras["Print Positions"] = "Front Center"
        elif bag:
            code = bag.group(2)
            colour = _BAG_COLOUR.get(code.casefold(), "")
            # peer: same product family W101-ClaRd or BG-W101-*
            prod = bag.group(1).upper()
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
        elif RE_STICKER.search(lab) or "sticker" in lab.casefold():
            sticker = RE_STICKER.search(lab)
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
        elif RE_TRANSFER.match(lab):
            tm = RE_TRANSFER.match(lab)
            extras["Gender Apparel"] = "Only-Design"
            extras["Size"] = tm.group(1).upper() if tm else ""
            extras["Print Positions"] = "Front Center"
            extras["Position 1 Name"] = "Front Center"
        elif RE_WAREHOUSE_GARMENT.match(lab):
            wh = RE_WAREHOUSE_GARMENT.match(lab)
            assert wh is not None
            g, typ, col, sz = (wh.group(i).upper() for i in range(1, 5))
            peer = _warehouse_peer(peers, g, typ, col, sz)
            ga = _WAREHOUSE_GA.get((g, typ), "")
            colour = _WAREHOUSE_COLOUR.get(col.casefold(), "")
            if not colour and peer:
                colour = clean(peer.get("Colour"))
            size = map_sr_size(sz) or sz
            extras["Gender Apparel"] = ga
            extras["Colour"] = colour
            extras["Size"] = size
            extras["Print Positions"] = "Front Center"
            extras["Position 1 Name"] = "Front Center"
            slug = apparel_image_slug(ga, colour)
            if slug:
                extras["Apparel Image"] = slug
            uid = (sku_uids or {}).get(lab.casefold(), "")
            if uid:
                extras["Supplier SKU"] = uid
        elif RE_GILDAN_5000.match(lab):
            g5000 = RE_GILDAN_5000.match(lab)
            assert g5000 is not None
            col, sz = g5000.group(1), g5000.group(2)
            peer = _gildan_5000_peer(peers, col, sz)
            extras["Print Positions"] = (
                clean(peer.get("Print Positions")) if peer else ""
            ) or "Front Center"
            extras["Position 1 Name"] = "Front Center"
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
        elif lab.rsplit("-", 1)[-1].casefold() == "yes":
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

        new_rows.append(_seed_from_peer(fieldnames, lab, peer, extras=extras))
    return new_rows, skipped


def fill_rows(df: pd.DataFrame, pe_index: pd.DataFrame, counts: dict) -> None:
    step_supplier_sku(df, counts)
    step_pe_enrich(df, pe_index, counts)
    step_dedicated_suppliers(df, counts)
    step_apparel_image(df, counts)
    print("  loading Size References + Shirts Print Sizes...", flush=True)
    size_index = load_size_ref_index(DEFAULT_CONFIG)
    overrides = load_overrides(DEFAULT_CONFIG)
    ps_table = load_print_sizes(DEFAULT_PRINT_SIZES)
    pe_sizes = pe_sizes_from_index(pe_index)
    step_print_sizes(
        df,
        size_index,
        overrides,
        ps_table,
        counts,
        only_missing_wh=False,
        pe_sizes=pe_sizes,
    )
    step_customise(df, counts)
    step_areeb(df, counts)
    step_supply(df, counts)
    step_printing_type(df, counts)
    step_supplier_name(df, counts)


def append_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            w.writerow({c: row.get(c, "") for c in fieldnames})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("labels", nargs="*", help="Custom Labels and/or packing SKUs")
    ap.add_argument(
        "--skus",
        nargs="+",
        default=[],
        help="Packing Item SKUs (Custom Label = after first dash)",
    )
    ap.add_argument(
        "--all-spc",
        action="store_true",
        help="Also seed every PE UID for the named mock's BTC SPC (slower)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    raw_items: list[tuple[str, bool]] = [(x, False) for x in args.labels]
    raw_items.extend((x, True) for x in args.skus)
    if not raw_items:
        print("No labels/SKUs given.", file=sys.stderr)
        return 2

    labels = []
    for raw, from_sku in raw_items:
        lab = label_from_input(raw, from_sku=from_sku)
        if lab:
            labels.append(lab)
    # dedupe preserve order
    seen_in: set[str] = set()
    uniq: list[str] = []
    for lab in labels:
        k = lab.casefold()
        if k in seen_in:
            continue
        seen_in.add(k)
        uniq.append(lab)
    labels = uniq

    cl_path = wh.cl_csv_path()
    print(f"Scanning labels in {cl_path} ...", flush=True)
    fieldnames, existing = _scan_existing(cl_path)
    print(f"  existing labels={len(existing):,}", flush=True)

    print(f"Loading BTC Product Data: {DEFAULT_PE}", flush=True)
    pe_index = load_pe_index(DEFAULT_PE)
    print(f"  PE UIDs={len(pe_index):,}", flush=True)

    sku_uids: dict[str, str] = {}
    for raw, from_sku in raw_items:
        if not from_sku:
            continue
        lab = label_from_input(raw, from_sku=True)
        prefix = raw.split("-", 1)[0].strip()
        if lab and prefix.isdigit() and prefix in pe_index.index:
            sku_uids[lab.casefold()] = prefix

    print("Loading peer rows for named labels...", flush=True)
    peers = _collect_peers_for_labels(cl_path, fieldnames, labels)

    if args.all_spc:
        expanded: list[str] = []
        for lab in labels:
            expanded.extend(_expand_all_spc(lab, peers, pe_index))
        labels = list(dict.fromkeys(expanded))
        print(f"  --all-spc expanded to {len(labels)} labels", flush=True)
        peers = _collect_peers_for_labels(cl_path, fieldnames, labels)

    new_rows, skipped = build_seed_rows(
        labels,
        fieldnames=fieldnames,
        existing=existing,
        peers=peers,
        pe_index=pe_index,
        all_spc=False,  # expansion already done when --all-spc
        sku_uids=sku_uids,
    )
    print(
        f"Named inputs={len(labels)}  new rows={len(new_rows)}  "
        f"skipped={len(skipped)}  all_spc={args.all_spc}",
        flush=True,
    )
    for r in new_rows[:12]:
        print(
            "  seed",
            {k: r.get(k) for k in SEED_COLS},
            flush=True,
        )
    if len(new_rows) > 12:
        print(f"  ... +{len(new_rows) - 12} more", flush=True)

    if not new_rows:
        print("Nothing to add.", flush=True)
        return 0

    assert uid_from_custom_label("M260-P3-3265") == "3265"
    assert uid_from_custom_label("M281-P5-C800T-30-18-24") == ""
    assert uid_from_custom_label("Transfer-1M-1") == ""
    assert uid_from_custom_label("Transfer-3M") == ""
    assert uid_from_custom_label("208544") == "208544"
    assert label_from_input("10428ALG-M260-P3-3265", from_sku=True) == "M260-P3-3265"
    assert customise_for_label("W101-SkyBe-O/S-Yes") == "Yes"
    assert customise_for_label("M260-P3-3265") == "Yes"
    assert customise_for_label("M55-120852") == ""
    assert _age_to_size("3&gt;6") == "3-6 Months"
    assert _age_to_size("6>12") == "6-12 Months"
    assert RE_C800T_AGE.match("M281-P5-C800T-30-3&gt;6")
    assert RE_C800T_AGE.match("M281-C800T-30-3>6")
    assert RE_C800T_AGE.match("M281-P5-C800T-30-6>12")
    assert customise_for_label("P5-ACPPLQ-A410-PB") == "Yes"
    assert customise_for_label("A515") == "Yes"
    assert customise_for_label("A515-PHOTO") == ""
    assert _alias_shirt_colour_label("M-T-NAV-XL") == "M-T-NVY-XL"
    assert _alias_shirt_colour_label("M-T-PUE-L") == "M-T-PRP-L"
    assert RE_BAG_COLOUR.match("BG-BG140S-ClaRdOW-O/S-YES")
    assert _BAG_COLOUR["clardow"] == "Classic Red-Off White"
    assert _sticker_size("50cmx50cm") == "50cm x 50cm"
    assert _sticker_mm("50cmx50cm") == ("500", "500")
    assert _sticker_mm("20cm x 20cm") == ("200", "200")
    assert RE_IRONON.search("M280-P5-IronOn-A6")
    assert RE_IRONON.search("M280-P5-DTF-IronOn-A6")
    assert RE_BAG_SIZE_YES.match("W415-NAT-L-Yes")
    assert RE_TRANSFER.match("Transfer-1M-1") and RE_TRANSFER.match("Transfer-3M")
    assert label_from_input("DTF-Transfer-1M-1", from_sku=True) == "Transfer-1M-1"
    assert label_from_input("ACPPLQ-A625-PHOTO", from_sku=True) == "A625-PHOTO"
    assert label_from_input("75931-W-H-BLK-M", from_sku=True) == "W-H-BLK-M"
    assert RE_WAREHOUSE_GARMENT.match("W-H-BLK-M")
    assert _WAREHOUSE_GA[("W", "H")] == "Womens-Hoodie"
    assert "m-h-blk-m" in _peer_keys_for_label("W-H-BLK-M")
    assert label_from_input("128357LG-5000-NAT-S", from_sku=True) == "5000-NAT-S"
    assert RE_GILDAN_5000.match("5000-NAT-S") and RE_GILDAN_5000.match("5000-LPNK-XL")
    assert "a3-5000-nat-s" in _peer_keys_for_label("5000-NAT-S")
    assert hyphen_tshirt_in_slug("Gildan-Heavy-Cotton-Adult-TShirt-Natural") == (
        "Gildan-Heavy-Cotton-Adult-T-Shirt-Natural"
    )
    df = pd.DataFrame(new_rows)
    for c in fieldnames:
        if c not in df.columns:
            df[c] = ""
    df = df[fieldnames]
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    counts: dict = defaultdict(int)
    print("Filling (same steps as fill_from_seeds)...", flush=True)
    assert pe_index is not None
    fill_rows(df, pe_index, counts)

    print("=== Counts ===", flush=True)
    for k in sorted(counts):
        if counts[k]:
            print(f"  {k}: {counts[k]:,}", flush=True)

    if args.dry_run:
        print("Dry-run: no write.", flush=True)
        return 0

    if not args.no_backup:
        backups = wh.cl_backups_dir()
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backups / f"{cl_path.stem}_preAdd_{stamp}{cl_path.suffix}"
        shutil.copy2(cl_path, backup)
        print(f"Backup: {backup}", flush=True)

    out_rows = df.to_dict(orient="records")
    try:
        append_rows(cl_path, fieldnames, out_rows)
    except PermissionError:
        fallback = cl_path.with_name(cl_path.stem + "_write_fallback" + cl_path.suffix)
        shutil.copy2(cl_path, fallback)
        append_rows(fallback, fieldnames, out_rows)
        print(f"Live CSV locked. Wrote fallback: {fallback}", flush=True)
        return 0

    print(f"Appended {len(out_rows)} rows -> {cl_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
