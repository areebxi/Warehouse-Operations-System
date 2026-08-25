from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ORDER_COL = "Order - Number"
PROCESS_COL = "Process Num"
CUSTOMER_COL = "Ship To - Name"


@dataclass(frozen=True)
class ExcelParseResult:
    ok: bool
    df: pd.DataFrame | None
    available_columns: list[str]
    reason: str | None = None


def parse_excel_file(path: Path) -> ExcelParseResult:
    # Read as strings to avoid numeric cells becoming "10.0" when stringified.
    df = pd.read_excel(path, engine="openpyxl", dtype=str)
    cols = list(df.columns)
    if ORDER_COL not in df.columns or PROCESS_COL not in df.columns:
        return ExcelParseResult(
            ok=False,
            df=None,
            available_columns=cols,
            reason=f"missing required headers: {ORDER_COL!r}, {PROCESS_COL!r}",
        )

    out = pd.DataFrame()
    out["orders Numbers"] = df[ORDER_COL].astype("string").str.strip()
    out["Process Number"] = df[PROCESS_COL].astype("string").str.strip()
    # Optional; used for error PDFs / failure reporting.
    if CUSTOMER_COL in df.columns:
        out["Customer Name"] = df[CUSTOMER_COL].astype("string").fillna("").str.strip()
    else:
        out["Customer Name"] = ""
    out = out[out["orders Numbers"].notna() & (out["orders Numbers"] != "")]

    out["Process Number"] = out["Process Number"].astype("string").str.replace(
        r"^Process\s*",
        "",
        regex=True,
        flags=re.IGNORECASE,
    )
    out["Process Number"] = out["Process Number"].astype("string").str.strip()

    return ExcelParseResult(ok=True, df=out[["Process Number", "orders Numbers", "Customer Name"]], available_columns=cols)

