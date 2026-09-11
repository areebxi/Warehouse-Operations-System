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
    clean,
    customise_for_label,
    load_pe_index,
    load_print_sizes,
    load_size_ref_index,
    load_overrides,
    pe_sizes_from_index,
    step_apparel_image,
    step_customise,
    step_dedicated_suppliers,
    step_pe_enrich,
    step_print_sizes,
    step_supplier_sku,
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
    # ShipStation / HTML sometimes encodes > as &gt; (literal unmatched SKU)
    r"^(M\d+-P\d+-C800T-\d+-)(\d+(?:>|&gt;)\d+|\d+-\d+)$",
    re.I,
)
RE_BAG_COLOUR = re.compile(r"^(W\d+|BG-W\d+)-([A-Za-z0-9]+)-O/S", re.I)

# Abbrev colour codes seen on bag Custom Labels → Colour name
_BAG_COLOUR = {
    "skybe": "Sky Blue",
    "clard": "Classic Red",
    "limgn": "Lime",
    "dusbe": "Dusty Blue",
    "nat": "Natural",
    "blk": "Black",
    "nvy": "Navy",
    "red": "Red",
    "bur": "Burgundy",
    "cpnk": "Classic Pink",
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
        return keys
    if bag:
        prod = bag.group(1).upper()
        keys.add(f"__prefix__:{prod.casefold()}-")
        if not prod.startswith("BG-"):
            keys.add(f"__prefix__:bg-{prod.casefold()}-")
        keys.add("__prefix__:w101-")
        keys.add("__prefix__:bg-w101")
        return keys
    return keys


def _collect_peers_for_labels(
    path: Path, fieldnames: list[str], labels: list[str]
) -> dict[str, dict[str, str]]:
    exact: set[str] = set()
    prefixes: list[str] = []
    for lab in labels:
        for item in _peer_keys_for_label(lab):
            if item.startswith("__prefix__:"):
                prefixes.append(item.split(":", 1)[1])
            else:
                exact.add(item)
    if not exact and not prefixes:
        return {}
    peers: dict[str, dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lab = clean(r.get("Custom Label"))
            if not lab:
                continue
            key = lab.casefold()
            if key not in exact and not any(key.startswith(p) for p in prefixes):
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
    # any same-UID mock row
    suffix = f"-{uid}".casefold()
    for key, row in peers.items():
        if key.endswith(suffix) and key.startswith(mock.casefold()):
            return row
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
                row[col] = clean(peer.get(col))
        # Prefer Front Center from mocks when peer Print Positions blank
        if not row.get("Print Positions"):
            row["Print Positions"] = "Front Center"
    if extras:
        for k, v in extras.items():
            if k in row and v:
                row[k] = v
    if not row.get("Print Positions") and RE_MOCK_TOKEN.match(label):
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


def build_seed_rows(
    labels: list[str],
    *,
    fieldnames: list[str],
    existing: set[str],
    peers: dict[str, dict[str, str]],
    pe_index: pd.DataFrame | None,
    all_spc: bool,
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

        if c800:
            # clone nearest same-series C800T row
            series = c800.group(1)
            age = c800.group(2)
            extras["Size"] = _age_to_size(age)
            # prefer existing sibling in series
            for key, row in peers.items():
                if key.startswith(series.casefold()):
                    peer = row
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
        elif m:
            mock, uid = m.group(1).upper(), m.group(2)
            p_m = re.search(r"-(P\d+)-", lab, re.I)
            p_tok = p_m.group(1).upper() if p_m else None
            peer = _peer_for_mock_uid(peers, mock, uid, p_tok)
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
                ga = clean(peer.get("Gender Apparel")) if peer else f"BG-{prod}"
                if not ga.startswith("BG-") and prod.startswith("W"):
                    ga = f"BG-{prod}"
                extras["Gender Apparel"] = ga or f"BG-{prod}"
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
    assert label_from_input("10428ALG-M260-P3-3265", from_sku=True) == "M260-P3-3265"
    assert customise_for_label("W101-SkyBe-O/S-Yes") == "Yes"
    assert customise_for_label("M260-P3-3265") == "Yes"
    assert customise_for_label("M55-120852") == ""
    assert _age_to_size("3&gt;6") == "3-6 Months"
    assert RE_C800T_AGE.match("M281-P5-C800T-30-3&gt;6")
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
