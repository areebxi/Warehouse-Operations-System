"""Backward-compatible wrapper for Missing Run app."""

from scripts.pipeline_missing_run_app.core import run_missing_run_from_all_orders
from scripts.pipeline_missing_run_app.main import main

__all__ = ["run_missing_run_from_all_orders", "main"]


if __name__ == "__main__":
    main()
