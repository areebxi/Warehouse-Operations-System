""" Backward-compatible wrapper for the Packing List GUI app."""

import sys
from pathlib import Path

# pipeline_* packages live under scripts/ (same pattern as Queue's queue_app.py).
_SCRIPTS = Path(__file__).resolve().parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from scripts.pipeline_packing_list_app.app import PackingListApp, main

__all__ = ["PackingListApp", "main"]


if __name__ == "__main__":
    main()
