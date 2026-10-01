"""Backward-compatible CLI wrapper for step 4 (position codes and logo expansion)."""

from pipeline_split_position.cli import main
from pipeline_split_position.service import run

__all__ = ["main", "run"]


if __name__ == "__main__":
    main()
