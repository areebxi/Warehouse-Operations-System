"""Backward-compatible CLI wrapper for step 2 (CL Database enrichment)."""

from scripts.pipeline_cl_lookup.enrich_cl_lookup import NEW_COLUMNS, enrich_packing_data, main

__all__ = ["NEW_COLUMNS", "enrich_packing_data", "main"]


if __name__ == "__main__":
    main()
