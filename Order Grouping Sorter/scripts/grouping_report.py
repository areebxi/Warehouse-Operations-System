"""Dry-run / run text report."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from grouping_models import (
    PERSONALISED_READY_TAG,
    RESEND_FILE,
    SHIFT1_SPLIT_ORDERS,
    UNMATCHED_FILE,
    Order,
    ProcessPart,
    SortResult,
)
from grouping_parts import assign_inside_file
from grouping_shift import shift_file_token

def _counts(orders: list[Order]) -> tuple[int, int, int]:
    return len(orders), sum(o.line_count for o in orders), sum(o.units for o in orders)

def format_report(result: SortResult, written: list[Path] | None = None) -> str:
    lines: list[str] = []
    o, li, u = _counts(
        [
            *result.resend,
            *result.unmatched,
            *result.held,
            *(o for b in result.bins for o in b.orders),
        ]
    )
    wrote = written is not None
    mode = "run" if wrote else "dry-run"
    lines.append(f"Order Grouping Sorter {mode}  run-date={result.run_date.isoformat()}")
    if wrote:
        lines.append(f"Input WAS written ({len(written)} CSV).")
        for path in written or []:
            lines.append(f"  {path}")
    else:
        lines.append("Input was NOT written.")
    lines.append(
        f"awaiting_shipment fetched={result.pool_orders}  "
        f"skipped post-order-designs={result.skipped_post}  "
        f"skipped DTFOcean.co.uk WP={result.skipped_excluded_store}  "
        f"empty/discount-only={result.empty_skipped}"
    )
    ro, rl, ru = _counts(result.resend)
    lines.append(f"{RESEND_FILE}  orders={ro}  lines={rl}  units={ru}")
    for p in assign_inside_file(result.resend):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    uo, ul, uu = _counts(result.unmatched)
    lines.append(f"{UNMATCHED_FILE}  orders={uo}  lines={ul}  units={uu}")
    reasons = Counter(o.unmatched_reason or "(no reason)" for o in result.unmatched)
    for reason, n in reasons.most_common():
        lines.append(f"  {reason}: {n}")
    for p in assign_inside_file(result.unmatched):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    ho, hl, hu = _counts(result.held)
    lines.append(
        f"HELD personalised (no {PERSONALISED_READY_TAG!r})  "
        f"orders={ho}  lines={hl}  units={hu}"
    )
    for p in assign_inside_file(result.held):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    lines.append(
        f"shift={result.shift_slot}  folder={result.shift_folder}  "
        f"{shift_file_token(result.shift_slot)}"
    )
    mix_word = "yes" if result.mix_today_future else "no"
    lines.append(
        f"today+future mix={mix_word}  today_orders={result.today_orders}  "
        f"eligible_orders={result.eligible_orders}  "
        f"(mix when eligible orders<={SHIFT1_SPLIT_ORDERS}; else split today vs later dates)"
    )
    if result.skipped_already_written:
        lines.append(
            f"skipped already in today's earlier shift CSVs: "
            f"{result.skipped_already_written} orders"
        )
    if result.overlaps:
        lines.append("fixed-batch overlaps (first wins; orders):")
        for pair, n in result.overlaps.most_common():
            lines.append(f"  {pair}: {n}")
    used = sum(o.line_count for b in result.bins for o in b.orders)
    lines.append(f"{result.shift_folder}  lines={used}")
    if not result.bins:
        lines.append("  (empty)")
    else:
        for b in result.bins:
            _append_process_block(lines, b.process_name, b.orders, b.parts, indent="  ")
    lines.append(
        f"grouped orders={o}  lines={li}  units={u}  (resend+unmatched+held+bins)"
    )
    return "\n".join(lines) + "\n"

def _append_process_block(
    lines: list[str],
    name: str,
    orders: list[Order],
    parts: list[ProcessPart] | None = None,
    *,
    indent: str,
) -> None:
    bo, bl, bu = _counts(orders)
    lines.append(f"{indent}{name}  orders={bo}  lines={bl}  units={bu}")
    inside = parts if parts is not None else assign_inside_file(orders)
    for p in inside:
        po, pl, pu = _counts(p.orders)
        lines.append(f"{indent}  -{p.n}  orders={po}  lines={pl}  units={pu}")
