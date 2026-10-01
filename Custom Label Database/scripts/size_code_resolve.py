"""Resolve Size References rows and print Width/Height slots."""
from __future__ import annotations

import re

from size_code_index import OverrideRule, SizeRefIndex, SrRow
from size_code_extract import extract_size_code, split_size_code
from size_code_util import POCKET_ADULT, POCKET_KIDS, clean, normalize_sku


def _rows_for_exact(index: SizeRefIndex, sku_value: str) -> list[SrRow]:
    return list(index.by_exact_sku.get(sku_value.upper(), []))


def resolve_sr_rows(code: str, index: SizeRefIndex) -> list[SrRow]:
    """
    Prefer exact (base, bracket) pair → bare base → contains / bracket-only fallbacks.
    """
    base, br = split_size_code(code)
    mb = index.by_base.get(base)

    if br is not None:
        candidates = [
            f"{base} ({br})",
            f"{base}({br})",
        ]
        if not br.startswith("-"):
            candidates.append(f"{base} (-{br})")
        for cand in candidates:
            rows = _rows_for_exact(index, cand)
            if rows:
                return rows
        if mb:
            for key in (br, br.lstrip("-"), f"-{br.lstrip('-')}"):
                if key in mb.brackets:
                    return list(mb.brackets[key])

    if mb and mb.bare_rows:
        return list(mb.bare_rows)

    rows = _rows_for_exact(index, base)
    if rows:
        return rows

    if mb and mb.brackets:
        key = sorted(mb.brackets.keys(), key=len, reverse=True)[0]
        return list(mb.brackets[key])

    return []


def pocket_dims_for_sku(sku_u: str) -> tuple[int, int]:
    if re.search(r"(^|-)K(-|$)", sku_u):
        return POCKET_KIDS
    return POCKET_ADULT


def apply_dim_overrides(
    rows_wh: list[tuple[int | None, int | None]],
    sku_u: str,
    override: OverrideRule | None,
    size_code: str | None,
) -> list[tuple[int | None, int | None]]:
    """
    After SR lookup: Override Print Size may replace dims.
    Width & Height present → use them.
    Blank → hardcoded pocket: -K- → 65×80, else 80×100.
    F8 size codes also force pocket dims.
    """
    force_pocket = False
    forced: tuple[int, int] | None = None

    if override is not None:
        if override.w is not None and override.h is not None:
            forced = (override.w, override.h)
        else:
            force_pocket = True

    if size_code and size_code.upper().startswith("F8"):
        force_pocket = True

    if "F8-" in sku_u or sku_u.startswith("F8"):
        if forced is None:
            force_pocket = True

    if force_pocket and forced is None:
        forced = pocket_dims_for_sku(sku_u)

    if forced is None:
        return rows_wh

    return [forced for _ in rows_wh] if rows_wh else [forced]


def n_designs_from_rows(rows: list[SrRow], pos_count: int) -> int:
    nd = 1
    for r in rows:
        if r.n_designs:
            nd = max(nd, r.n_designs)
            break
    return max(nd, pos_count, 1)


def slot_dimensions(
    rows: list[SrRow], n_slots: int
) -> list[tuple[int | None, int | None]]:
    """Map SR rows (by Number of Designs / suffix order) onto slots 1..n."""
    ordered = list(rows)
    out: list[tuple[int | None, int | None]] = []
    for i in range(n_slots):
        if i < len(ordered):
            out.append((ordered[i].w, ordered[i].h))
        elif ordered:
            out.append((ordered[-1].w, ordered[-1].h))
        else:
            out.append((None, None))
    return out


def resolve_print_dims(
    custom_label: str,
    print_positions: str,
    index: SizeRefIndex,
    overrides: list[OverrideRule],
    max_slots: int = 4,
) -> dict:
    """
    Full resolve for one Custom Label row.
    Returns dict with size_code, override, n_slots, position_names, widths, heights, source.
    """
    sku_u, _ = normalize_sku(custom_label)
    code, ov = extract_size_code(custom_label, index, overrides)
    pos_names = [p.strip() for p in clean(print_positions).split(",") if p.strip()]
    if not pos_names:
        pos_names = []

    rows: list[SrRow] = []
    if code:
        rows = resolve_sr_rows(code, index)

    n = n_designs_from_rows(rows, len(pos_names)) if rows else max(len(pos_names), 1)
    n = min(n, max_slots)

    whs = slot_dimensions(rows, n) if rows else [(None, None)] * n
    whs = apply_dim_overrides(whs, sku_u, ov, code)

    if (not rows) and ov is not None:
        forced = apply_dim_overrides([(None, None)], sku_u, ov, code)[0]
        n = min(max(len(pos_names), 1), max_slots)
        whs = [forced] * n

    return {
        "size_code": code,
        "override": ov.contain if ov else None,
        "n_slots": n,
        "position_names": pos_names[:max_slots],
        "whs": whs[:max_slots],
        "matched_rows": len(rows),
    }
