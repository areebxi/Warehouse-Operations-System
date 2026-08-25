"""Pipeline runtime package.

Runner symbols are loaded lazily so importing submodules (e.g. order_number_csv)
does not pull in enrich_cl_lookup and cause circular imports.
"""

from __future__ import annotations

from typing import Any

__all__ = ["run_pipeline", "run_missing_logos_pipeline"]


def __getattr__(name: str) -> Any:
    if name == "run_pipeline":
        from .runner import run_pipeline

        return run_pipeline
    if name == "run_missing_logos_pipeline":
        from .runner import run_missing_logos_pipeline

        return run_missing_logos_pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
