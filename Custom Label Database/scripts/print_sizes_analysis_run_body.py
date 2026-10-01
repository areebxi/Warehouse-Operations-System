from __future__ import annotations
from scripts.print_sizes_analysis_run_body_part_a import _run_part_a
from scripts.print_sizes_analysis_run_body_part_b import _run_part_b

def run():
    ctx = _run_part_a()
    return _run_part_b(ctx)



