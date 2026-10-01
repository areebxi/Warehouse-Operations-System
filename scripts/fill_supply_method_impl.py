from __future__ import annotations
import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from shared import paths as wh
from shared.areeb_taxonomy import cell
from shared.supply_method import (
    COL,
    classify_cl_row,
    classify_packs_row,
    classify_plain_row,
)

def backup_file(path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest
def header_index(headers: list[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(headers) if h}
