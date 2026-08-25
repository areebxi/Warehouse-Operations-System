from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# Share a summary only when a process has exactly this many orders/labels.
# Processes with more than this get their own summary page.
SHARE_SUMMARY_EXACT_LABELS = 1
SHARED_SUMMARIES_ENABLED = True


@dataclass(frozen=True)
class ProcessGroupResult:
    process_number: str
    order_count: int
    label_paths: list[Path]
    failures: list = field(default_factory=list)
    ship_from: str = ""
    source_file: str = ""
    source_index: int = 0

    @property
    def source_key(self) -> str:
        """Stable key for DTF/source boundary (empty = single/legacy input)."""
        if self.source_file:
            return f"{int(self.source_index)}::{self.source_file}"
        return f"{int(self.source_index)}::"


@dataclass(frozen=True)
class SummaryBucket:
    """One summary page covering one or more consecutive single-label processes."""

    summary_process_number: str
    members: tuple[ProcessGroupResult, ...]

    @property
    def process_numbers(self) -> list[str]:
        return [m.process_number for m in self.members]

    @property
    def label_paths(self) -> list[Path]:
        out: list[Path] = []
        for m in self.members:
            out.extend(m.label_paths)
        return out

    @property
    def label_count(self) -> int:
        return len(self.label_paths)

    @property
    def failures(self) -> list:
        out: list = []
        for m in self.members:
            out.extend(m.failures)
        return out

    @property
    def ship_from(self) -> str:
        counts: dict[str, int] = {}
        for m in self.members:
            s = str(m.ship_from or "").strip()
            if s:
                counts[s] = counts.get(s, 0) + 1
        if not counts:
            return ""
        return max(counts.items(), key=lambda kv: kv[1])[0]


def _sort_key(pn: str) -> tuple[int, str]:
    s = str(pn).strip()
    if s.isdigit():
        return (0, f"{int(s):020d}")
    return (1, s.lower())


def _is_consecutive_process(prev: str, curr: str) -> bool:
    """True only for numeric neighbors like 100 -> 101 (not 100 -> 200)."""
    a = str(prev).strip()
    b = str(curr).strip()
    if not (a.isdigit() and b.isdigit()):
        return False
    return int(b) == int(a) + 1


def _can_share(order_count: int, *, share_exact: int = SHARE_SUMMARY_EXACT_LABELS) -> bool:
    """Share only when the process has exactly one label (by default)."""
    return int(order_count) == int(share_exact)


def bucket_process_groups_for_shared_summaries(
    results: list[ProcessGroupResult],
    *,
    share_exact: int = SHARE_SUMMARY_EXACT_LABELS,
) -> list[SummaryBucket]:
    """
    Share summary pages only for processes with exactly one label.

    - order_count == 1: share with consecutive single-label neighbors
    - order_count >= 2: own summary page

    Hard rule: never share across DTF/source files. When the source file changes,
    always start a fresh summary page so the user can see the next file begin —
    even if process numbers are consecutive (104 then 105).
    """
    if share_exact < 0:
        raise ValueError("share_exact must be >= 0")

    ordered = sorted(
        results,
        key=lambda r: (int(r.source_index), _sort_key(r.process_number)),
    )
    buckets: list[SummaryBucket] = []
    pending: list[ProcessGroupResult] = []

    def _flush_pending() -> None:
        nonlocal pending
        if not pending:
            return
        buckets.append(
            SummaryBucket(
                summary_process_number=str(pending[0].process_number).strip(),
                members=tuple(pending),
            )
        )
        pending = []

    for r in ordered:
        if _can_share(r.order_count, share_exact=share_exact):
            if pending and (
                pending[-1].source_key != r.source_key
                or not _is_consecutive_process(pending[-1].process_number, r.process_number)
            ):
                _flush_pending()
            pending.append(r)
        else:
            _flush_pending()
            buckets.append(
                SummaryBucket(
                    summary_process_number=str(r.process_number).strip(),
                    members=(r,),
                )
            )

    _flush_pending()
    return buckets
