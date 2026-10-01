"""Resolve peer rows into seed row dicts / SPC expansion."""
from __future__ import annotations

import re

import pandas as pd

from fill_from_seeds import clean, customise_for_label, hyphen_tshirt_in_slug

from add_labels_parse import RE_MOCK_P_UID, RE_MOCK_TOKEN


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
