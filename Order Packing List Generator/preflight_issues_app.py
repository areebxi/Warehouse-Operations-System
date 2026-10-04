from __future__ import annotations

"""
Preflight Issues App entrypoint.

Launch with `python preflight_issues_app.py`.
"""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from scripts.preflight_issues_app import main


if __name__ == "__main__":  # pragma: no cover - GUI entrypoint
    main()
