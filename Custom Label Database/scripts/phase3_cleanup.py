"""
Phase 3 cleanup — supervisor choices:
  3A exact dups: YES
  3B same-core keep richest: NO
  3C size typos: YES
  D1 Navy/Royal expand only inside colour-only conflicts: YES
  D2 gender-only prefer brand: NO
  D3 true conflicts report only: NO
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from scripts.phase3_cleanup_part_a import _main_part_a
from scripts.phase3_cleanup_part_b import _main_part_b

def main():
    ctx = _main_part_a()
    return _main_part_b(ctx)

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
BACKUP = BASE / f"Custom Label Database_Updated_prePhase3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
OUT = SRC
LOG = BASE / "docs" / "PHASE_3_CHANGELOG.md"

SIZE_TYPOS = {
    "Meduim": "Medium",
    "ExtraSmall": "Extra Small",
    "Wodium": "Medium",
}

COLOUR_EXPAND_PAIRS = [
    ("Navy", "Navy Blue"),
    ("Royal", "Royal Blue"),
]




if __name__ == "__main__":
    main()
