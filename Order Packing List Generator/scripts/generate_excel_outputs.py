"""Backward-compatible CLI wrapper for step 7 (Excel export)."""

from pipeline_generate_excel_outputs.cli import main
from pipeline_generate_excel_outputs.service import run

__all__ = ["main", "run"]


if __name__ == "__main__":
    main()
