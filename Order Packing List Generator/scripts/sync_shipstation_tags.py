"""CLI: sync Data/ShipStation Tags.xlsx with live ShipStation tags."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python scripts/sync_shipstation_tags.py` from any cwd.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.pipeline_shipstation.sync_tags_xlsx import main

if __name__ == "__main__":
    raise SystemExit(main())
