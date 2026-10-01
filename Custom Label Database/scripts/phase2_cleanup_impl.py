from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

def apply_map(series: pd.Series, mapping: dict[str, str]) -> tuple[pd.Series, dict[str, int]]:
    counts: dict[str, int] = {}
    out = series.copy()
    for src, dst in mapping.items():
        mask = out == src
        n = int(mask.sum())
        if n:
            counts[f"{src} -> {dst}"] = n
            out = out.mask(mask, dst)
    return out, counts
