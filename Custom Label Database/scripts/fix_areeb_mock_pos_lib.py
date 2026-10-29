"""Compare/normalize mock Print Positions; apply from live or Mocks map."""
from __future__ import annotations

import re

from fix_areeb_pos_lib import clear_slots_2_to_4, copy_print_from_live, mm_ok, sole_center
from generate_mocks_util import clean, map_print_positions

RE_LEADING_MOCK = re.compile(r"^(M\d+)\b", re.I)
RE_MOCK_SUFFIX = re.compile(r"\s*\(M\d+\)\s*$", re.I)

CODE_BY_NAME = {
    "front center": "F4",
    "back center": "B4",
    "front left pocket": "F8",
}


def leading_mock_id(label: str) -> str | None:
    m = RE_LEADING_MOCK.match(clean(label))
    return m.group(1).upper() if m else None


def strip_mock_suffix(pp: str) -> str:
    return RE_MOCK_SUFFIX.sub("", clean(pp)).strip()


def norm_pp(pp: str) -> str:
    """Compare key: lower, collapse spaces, strip (M##), stable slot order."""
    s = strip_mock_suffix(pp).casefold()
    s = re.sub(r"\s+", " ", s)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return ", ".join(parts)


def expected_pp(mocks_raw: dict[str, str], mock_id: str) -> str:
    raw = mocks_raw.get(mock_id, "")
    return map_print_positions(raw, mock_id) if raw else ""


def slot_names(mapped: str) -> list[str]:
    body = strip_mock_suffix(mapped)
    return [p.strip() for p in body.split(",") if p.strip()]


def sole_pocket(row: dict[str, str]) -> None:
    row["Print Positions"] = "Front Left Pocket"
    if "Print Position Code" in row:
        row["Print Position Code"] = "F8"
    row["Position 1 Name"] = "Front Left Pocket"
    if "Print Size 1" in row:
        row["Print Size 1"] = ""
    row["Width 1 (mm)"] = "80"
    row["Height 1 (mm)"] = "100"
    if "Design Image Suffix 1" in row:
        row["Design Image Suffix 1"] = ""
    clear_slots_2_to_4(row)


def keep_shirt_mm(row: dict[str, str]) -> tuple[str, str]:
    w = (row.get("Width 1 (mm)") or "").strip()
    h = (row.get("Height 1 (mm)") or "").strip()
    if mm_ok(w, h):
        return w, h
    for n in range(2, 5):
        w = (row.get(f"Width {n} (mm)") or "").strip()
        h = (row.get(f"Height {n} (mm)") or "").strip()
        if mm_ok(w, h):
            return w, h
    return (row.get("Width 1 (mm)") or "").strip(), (row.get("Height 1 (mm)") or "").strip()


def apply_from_mocks(row: dict[str, str], mapped: str) -> None:
    names = slot_names(mapped)
    if not names:
        return
    if len(names) == 1 and names[0].casefold() == "front left pocket":
        sole_pocket(row)
        return
    if len(names) == 1 and names[0].casefold() in ("front center", "back center"):
        w, h = keep_shirt_mm(row)
        sole_center(row, back=names[0].casefold() == "back center", width=w, height=h)
        return
    row["Print Positions"] = mapped
    if "Print Position Code" in row:
        codes = [CODE_BY_NAME.get(n.casefold(), "") for n in names]
        row["Print Position Code"] = "/".join(c for c in codes if c)
    for i, name in enumerate(names, start=1):
        row[f"Position {i} Name"] = name
        if "pocket" in name.casefold():
            row[f"Width {i} (mm)"] = "80"
            row[f"Height {i} (mm)"] = "100"
        elif i == 1:
            w, h = keep_shirt_mm(row)
            row["Width 1 (mm)"], row["Height 1 (mm)"] = w, h
    for i in range(len(names) + 1, 5):
        for c in (
            f"Position {i} Name",
            f"Print Size {i}",
            f"Width {i} (mm)",
            f"Height {i} (mm)",
            f"Design Image Suffix {i}",
        ):
            if c in row:
                row[c] = ""


def prefer_live_or_mocks(
    dst: dict[str, str],
    live: dict[str, str] | None,
    mapped: str,
    live_pp_key: str,
) -> str:
    """Return 'live' | 'mocks'. Mutates dst."""
    if live is not None:
        live_pp = (live.get(live_pp_key) or live.get("Print Positions") or "").strip()
        if norm_pp(live_pp) == norm_pp(mapped):
            copy_print_from_live(dst, live)
            return "live"
    apply_from_mocks(dst, mapped)
    return "mocks"
