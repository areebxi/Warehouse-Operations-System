from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_void_order_numbers(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(str(path))

    try:
        df = pd.read_csv(path, dtype=str)
    except UnicodeDecodeError as e:
        raise ValueError(f"Void CSV appears corrupted or not UTF-8 readable: {path}") from e
    except pd.errors.EmptyDataError as e:
        return []
    except pd.errors.ParserError as e:
        raise ValueError(f"Void CSV appears corrupted/malformed: {path}") from e

    if df.shape[1] == 0 or df.shape[0] == 0:
        return []

    # Require a specific column name (case-insensitive).
    wanted = "order number"
    cols = {str(c).strip().lower(): str(c) for c in df.columns}
    if wanted not in cols:
        raise ValueError(
            "Void CSV must contain a column named 'Order Number' (case-insensitive). "
            f"Found columns: {list(df.columns)!r}"
        )
    col = cols[wanted]

    out: list[str] = []
    for v in df[col].astype("string").fillna("").tolist():
        s = str(v).strip()
        if s and s.lower() != "nan":
            out.append(s)
    return out

