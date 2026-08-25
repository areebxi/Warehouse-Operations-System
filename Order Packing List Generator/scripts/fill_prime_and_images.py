"""Backward-compatible CLI wrapper for step 3 (Prime and image columns)."""

from scripts.pipeline_fill_prime_images.cli import main
from scripts.pipeline_fill_prime_images.service import fill_packing_columns

__all__ = ["fill_packing_columns", "main"]


if __name__ == "__main__":
    main()
