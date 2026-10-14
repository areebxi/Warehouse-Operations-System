"""Read Plain Database.csv (xlsx still accepted)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pdf_constants import COLUMN_NAMES


def read_plain_database(path: Path) -> pd.DataFrame:
    dtype = {COLUMN_NAMES["db_sku"]: str, COLUMN_NAMES["product_code"]: str}
    if Path(path).suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=dtype, encoding="utf-8-sig")
    return pd.read_excel(path, dtype=dtype)
