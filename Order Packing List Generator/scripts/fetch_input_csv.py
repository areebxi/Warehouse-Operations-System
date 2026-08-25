"""Backward-compatible CLI wrapper for step 1 (ShipStation CSV fetch)."""

from scripts.pipeline_cl_lookup.fetch_input_csv import (
    OUTPUT_COLUMNS,
    fetch_input_csv,
    main,
    write_fetched_csv,
)

__all__ = [
    "OUTPUT_COLUMNS",
    "fetch_input_csv",
    "write_fetched_csv",
    "main",
]


if __name__ == "__main__":
    main()
