from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from scripts.app.util.process_numbers import process_number_sort_key


# Fallback when Configuration Workbook cell A2 is missing. Info page when the previous process has at least this many labels.
SUMMARY_EVERY_LABELS = 10
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
    """Labels for one process. An info page is included only when include_summary is set."""

    summary_process_number: str
    members: tuple[ProcessGroupResult, ...]
    include_summary: bool = True

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


def bucket_process_groups_for_shared_summaries(
    results: list[ProcessGroupResult],
    *,
    summary_every: int = SUMMARY_EVERY_LABELS,
) -> list[SummaryBucket]:
    """
    Walk processes in order 1, 2, 3… (not 1, 10, 2). A process is never split.

    The first page of each DTF file is always a Batch Summary. After that,
    a summary is added only when the labels it covers reach `summary_every`.
    A later run left under the threshold has labels only.
    """
    if summary_every < 1:
        raise ValueError("summary_every must be >= 1")

    ordered = sorted(
        results,
        key=lambda r: (int(r.source_index), process_number_sort_key(r.process_number)),
    )
    buckets: list[SummaryBucket] = []
    pending: list[ProcessGroupResult] = []
    pending_labels = 0
    opened = False

    def _flush() -> None:
        nonlocal pending, pending_labels, opened
        if not pending:
            return
        include = (not opened) or pending_labels >= summary_every
        buckets.append(
            SummaryBucket(
                summary_process_number=str(pending[0].process_number).strip(),
                members=tuple(pending),
                include_summary=include,
            )
        )
        if include:
            opened = True
        pending = []
        pending_labels = 0

    for r in ordered:
        n = len(r.label_paths)
        if pending and pending[-1].source_key != r.source_key:
            _flush()
            opened = False
        pending.append(r)
        pending_labels += n
        if pending_labels >= summary_every:
            _flush()
    _flush()
    return buckets
