"""Skip Batches sheet: batches that must not get Design Queues PNGs."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Set

from shared.skip_batches import (
    batch_digits_from_name,
    load_skip_batches,
    output_stem_from_dtf_name,
    remove_queue_pngs_for_stem,
    should_skip_batch,
)

__all__ = [
    "load_skip_batches",
    "batch_digits_from_name",
    "should_skip_batch",
    "output_stem_from_dtf_name",
    "remove_queue_pngs_for_stem",
    "apply_skip_batches",
]


def apply_skip_batches(
    path: Path,
    ctx: SimpleNamespace,
    skips: Set[str],
    *,
    log,
    under_inbox: Callable[[Path], bool],
    move_to_processed: Callable[[Path], Path],
) -> bool:
    """If path is a Skip Batch: remove leftover PNGs, optionally move inbox file. True = skipped."""
    if not should_skip_batch(path, skips):
        return False
    log.info("Skip Batches: skipping queues for %s", path.name)
    removed = remove_queue_pngs_for_stem(
        output_stem_from_dtf_name(path.name),
        dtf_queues_folder=getattr(ctx, "dtf_queues_folder", None),
    )
    for p in removed:
        log.info("Skip Batches: removed leftover %s", p)
    if under_inbox(path):
        dest = move_to_processed(path)
        log.info("Moved skipped file to %s", dest)
    return True


if __name__ == "__main__":
    assert batch_digits_from_name("DTF Des-PB70-S1.xlsx") == "70"
    assert batch_digits_from_name("PB3500-S1") == "3500"
    assert batch_digits_from_name("DTF Des-PB370-S1.xlsx") == "370"
    assert not should_skip_batch(Path("DTF Des-PB370-S1.xlsx"), {"70"})
    assert should_skip_batch(Path("DTF Des-PB70-S1.xlsx"), {"70"})
    assert batch_digits_from_name("DTF Des-P100.xlsx") == "100"
    assert batch_digits_from_name("DTF Des-P3570.xlsx") == "3570"
    assert should_skip_batch(Path("DTF Des-P3570.xlsx"), {"3570"})
    assert should_skip_batch(Path("DTF Des-P5570.xlsx"), {"5570"})
    print("design_queues_skip self-check OK")
