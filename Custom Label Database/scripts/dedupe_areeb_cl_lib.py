"""Keep-score + mistake fixes for Areeb CL Custom Label dedupe."""
from __future__ import annotations

import re
from collections import defaultdict

Y_SIZE = {
    "YXS": "3-4 Years", "YS": "5-6 Years", "YM": "7-8 Years",
    "YL": "9-11 Years", "YXL": "12-14 Years", "Y2XL": "14-15 Years",
    "YXXL": "14-15 Years", "Y3XL": "14-15 Years",
}
SHORT_GA = re.compile(
    r"^(Kids|Mens|Womens|Men|Women)-[A-Za-z][A-Za-z0-9-]*$", re.I
)
KEY_COLS = (
    "Gender Apparel", "Colour", "Size", "Apparel Image", "Print Positions",
    "Position 1 Name", "Width 1 (mm)", "Height 1 (mm)", "Supply Method",
    "Supplier Name", "BTC SKU", "Printing Type", "Category (Areeb)",
    "Product Type (Areeb)", "Brand",
)


def toks(cl: str) -> list[str]:
    return [t for t in cl.upper().split("-") if t]


def youth_size(cl: str) -> str | None:
    for t in toks(cl):
        if t in Y_SIZE:
            return Y_SIZE[t]
    return None


def kids_label(cl: str) -> bool:
    t = toks(cl)
    return bool(t) and (t[0] == "K" or (len(t) >= 2 and t[0] == "B" and t[1] == "K"))


def apparel_kind_colour(cl: str) -> tuple[str, str]:
    """('T','RED') for K-T-RED-…; ('T','WHI') for B-K-T-WHI-…."""
    t = toks(cl)
    if t and t[0] == "K" and len(t) >= 3:
        return t[1], t[2]
    if len(t) >= 4 and t[0] == "B" and t[1] == "K":
        return t[2], t[3]
    return "", ""


def is_short_ga(ga: str) -> bool:
    return bool(SHORT_GA.match(ga.strip()))


def is_long_supplier_ga(ga: str) -> bool:
    g = ga.strip()
    if not g or is_short_ga(g):
        return False
    return (" " in g) or g.upper().startswith(("FOTL", "GILDAN", "FRUIT", "SF500", "AWDIS"))


def token_score(cl: str, row: dict[str, str]) -> int:
    ga = (row.get("Gender Apparel") or "").strip()
    size = (row.get("Size") or "").strip()
    score = 0
    exp = youth_size(cl)
    if exp and size == exp:
        score += 2
    elif exp and size:
        score -= 1
    if kids_label(cl):
        gal = ga.lower()
        if "kids" in gal or "youth" in gal:
            score += 2
        elif "mens" in gal or gal.startswith("men"):
            score -= 2
    return score


def ga_score(ga: str) -> int:
    if is_long_supplier_ga(ga):
        return 2
    if is_short_ga(ga):
        return 0
    return 1


def filled(row: dict[str, str]) -> int:
    return sum(1 for c in KEY_COLS if (row.get(c) or "").strip())


def strength(cl: str, row: dict[str, str], index: int) -> tuple:
    ga = (row.get("Gender Apparel") or "").strip()
    return (token_score(cl, row), ga_score(ga), filled(row), -index)


def pick_winner(
    cl: str, indexed: list[tuple[int, dict[str, str]]]
) -> tuple[int, dict[str, str]]:
    return max(indexed, key=lambda ir: strength(cl, ir[1], ir[0]))


def sole_pos(row: dict[str, str]) -> str:
    pp = (row.get("Print Positions") or "").strip().lower()
    p1 = (row.get("Position 1 Name") or "").strip().lower()
    if pp == p1 == "front center":
        return "front"
    if pp == p1 == "back center":
        return "back"
    return ""


def mock_prefix(cl: str) -> str | None:
    m = re.match(r"^(M\d+-P\d+)-", cl, re.I)
    return m.group(1).upper() if m else None


def clone_kids_fields(dst: dict[str, str], src: dict[str, str], size: str) -> None:
    for col in (
        "Gender Apparel", "Apparel Image", "Brand", "Category (Areeb)",
        "Product Type (Areeb)", "Product Style (Areeb)", "Department (Areeb)",
        "Supply Method", "Supplier Name", "BTC Product Code",
    ):
        if (src.get(col) or "").strip():
            dst[col] = src[col]
    dst["Size"] = size
    for col in ("BTC SKU", "Supplier SKU", "Print Positions", "Print Position Code"):
        if (src.get(col) or "").strip():
            dst[col] = src[col]
    for n in range(1, 5):
        for c in (
            f"Position {n} Name", f"Print Size {n}", f"Width {n} (mm)",
            f"Height {n} (mm)", f"Design Image Suffix {n}",
        ):
            if (src.get(c) or "").strip():
                dst[c] = src[c]


def fix_kt_mens_youth(rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    kids_peer: dict[tuple[str, str], dict[str, str]] = {}
    for r in rows:
        cl = (r.get("Custom Label") or "").strip()
        ga = (r.get("Gender Apparel") or "").strip()
        if not kids_label(cl) or "kids" not in ga.lower():
            continue
        kind, colour = apparel_kind_colour(cl)
        if kind and colour and youth_size(cl):
            kids_peer.setdefault((kind, colour), r)
    log: list[tuple[str, str, str]] = []
    for r in rows:
        cl = (r.get("Custom Label") or "").strip()
        ga = (r.get("Gender Apparel") or "").strip()
        if not kids_label(cl) or youth_size(cl) is None:
            continue
        gal = ga.lower()
        if "mens" not in gal and not gal.startswith("men"):
            continue
        exp = youth_size(cl) or "14-15 Years"
        kind, colour = apparel_kind_colour(cl)
        peer = kids_peer.get((kind, colour))
        before = f"{ga}|{(r.get('Size') or '').strip()}"
        if peer:
            clone_kids_fields(r, peer, exp)
        else:
            # ponytail: no same-kind/colour peer — short Kids GA by dash kind
            r["Gender Apparel"] = {
                "T": "Kids-T-Shirt", "H": "Kids-Hoodie", "SS": "Kids-Sweatshirt",
            }.get(kind, "Kids-T-Shirt")
            r["Size"] = exp
            if "Department (Areeb)" in r:
                r["Department (Areeb)"] = "Kids"
        after = f"{(r.get('Gender Apparel') or '').strip()}|{(r.get('Size') or '').strip()}"
        log.append((cl, before, after))
    return log


def fix_lone_back(rows: list[dict[str, str]]) -> list[str]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        cl = (r.get("Custom Label") or "").strip()
        pref = mock_prefix(cl)
        if not pref:
            continue
        col = (r.get("Colour") or "").strip().casefold()
        groups[(pref, col)].append(r)
    fixed: list[str] = []
    for _, members in groups.items():
        kinds = [sole_pos(r) for r in members]
        n_f, n_b = kinds.count("front"), kinds.count("back")
        if n_f < 2 or n_b < 1 or n_f <= n_b:
            continue
        for r, k in zip(members, kinds):
            if k != "back":
                continue
            r["Print Positions"] = "Front Center"
            r["Position 1 Name"] = "Front Center"
            if (r.get("Print Position Code") or "").strip().upper() == "B4":
                r["Print Position Code"] = "F4"
            fixed.append((r.get("Custom Label") or "").strip())
    return fixed
