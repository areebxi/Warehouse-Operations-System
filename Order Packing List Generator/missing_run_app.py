""" Backward-compatible wrapper for Missing Run app."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SCRIPTS = _ROOT / "scripts"
_WAREHOUSE = _ROOT.parent
for _p in (_SCRIPTS, _WAREHOUSE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.pipeline_missing_run_app.core import run_missing_run_from_all_orders
from scripts.pipeline_missing_run_app.main import main

__all__ = ["run_missing_run_from_all_orders", "main"]


if __name__ == "__main__":
    main()
