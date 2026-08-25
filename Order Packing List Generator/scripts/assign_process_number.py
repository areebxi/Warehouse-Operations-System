"""Backward-compatible CLI wrapper for step 5 (process number assignment)."""

from scripts.pipeline_assign_process_number.cli import main
from scripts.pipeline_assign_process_number.service import run

__all__ = ["main", "run"]


if __name__ == "__main__":
    main()
