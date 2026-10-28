"""Helpers: sole Front/Back Center + live→Areeb print-field copy."""
from __future__ import annotations

LIVE_CL = "Custom_Label"
AREEB_CL = "Custom Label"

PRINT_PAIRS = [
    ("Print_Positions", "Print Positions"),
    ("Print_Position_Code", "Print Position Code"),
]
for n in range(1, 5):
    PRINT_PAIRS.extend(
        [
            (f"Position_{n}_Name", f"Position {n} Name"),
            (f"Print_Size_{n}", f"Print Size {n}"),
            (f"Width_{n}_mm", f"Width {n} (mm)"),
            (f"Height_{n}_mm", f"Height {n} (mm)"),
        ]
    )


def live_get(row: dict[str, str], live_key: str, areeb_key: str) -> str:
    if live_key in row:
        return (row.get(live_key) or "").strip()
    return (row.get(areeb_key) or "").strip()


def copy_print_from_live(dst: dict[str, str], src: dict[str, str]) -> None:
    for live_k, areeb_k in PRINT_PAIRS:
        if areeb_k not in dst:
            continue
        dst[areeb_k] = live_get(src, live_k, areeb_k)


def clear_slots_2_to_4(row: dict[str, str]) -> None:
    for n in range(2, 5):
        for c in (
            f"Position {n} Name",
            f"Print Size {n}",
            f"Width {n} (mm)",
            f"Height {n} (mm)",
            f"Design Image Suffix {n}",
        ):
            if c in row:
                row[c] = ""


def sole_center(
    row: dict[str, str],
    *,
    back: bool,
    width: str,
    height: str,
    print_size: str = "",
) -> None:
    name = "Back Center" if back else "Front Center"
    row["Print Positions"] = name
    row["Print Position Code"] = "B4" if back else "F4"
    row["Position 1 Name"] = name
    row["Print Size 1"] = print_size
    row["Width 1 (mm)"] = width
    row["Height 1 (mm)"] = height
    # ponytail: one filled position → blank Design Image Suffix (warehouse rule)
    row["Design Image Suffix 1"] = ""
    clear_slots_2_to_4(row)


def mm_ok(w: str, h: str) -> bool:
    try:
        wi, hi = float(w), float(h)
    except ValueError:
        return False
    return wi >= 100 and hi >= 100  # not pocket 80×100


def peer_front_mm(
    rows: list[dict[str, str]], size: str, ga_hint: str
) -> tuple[str, str] | None:
    size_cf = size.strip().casefold()
    hint = ga_hint.casefold()
    for r in rows:
        if (r.get("Size") or "").strip().casefold() != size_cf:
            continue
        ga = (r.get("Gender Apparel") or "").strip().casefold()
        if hint and hint[:4] not in ga and "t-shirt" not in ga and "tshirt" not in ga:
            continue
        pp = (r.get("Print Positions") or "").strip().casefold()
        p1 = (r.get("Position 1 Name") or "").strip().casefold()
        if pp != "front center" and p1 != "front center":
            continue
        w = (r.get("Width 1 (mm)") or "").strip()
        h = (r.get("Height 1 (mm)") or "").strip()
        if mm_ok(w, h):
            return w, h
    return None
