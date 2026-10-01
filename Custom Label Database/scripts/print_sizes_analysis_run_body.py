from __future__ import annotations

from print_sizes_analysis_cl_fill import run_cl_fill
from print_sizes_analysis_sources import run_sources


def run():
    run_sources()
    return run_cl_fill()
