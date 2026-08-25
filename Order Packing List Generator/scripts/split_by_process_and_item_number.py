"""Backward-compatible CLI wrapper for step 6 (split by process and item number)."""

from scripts.pipeline_split_by_process_item.cli import main
from scripts.pipeline_split_by_process_item.service import run

__all__ = ["main", "run"]


if __name__ == "__main__":
    main()
