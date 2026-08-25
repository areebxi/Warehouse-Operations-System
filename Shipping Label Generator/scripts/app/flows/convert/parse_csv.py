from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ORDER_ALIASES = ["order - number", "order number", "ordernumber", "order"]
PROCESS_ALIASES = ["process num", "process number", "processnum", "process"]
CUSTOMER_ALIASES = ["customer name", "ship to - name", "ship to name", "ship-to name", "ship to"]


def _norm(s: str) -> str:
    return str(s).lower().strip()


@dataclass(frozen=True)
class CsvParseResult:
    ok: bool
    df: pd.DataFrame | None
    available_columns: list[str]
    reason: str | None = None


def parse_csv_file(path: Path) -> CsvParseResult:
    # Read as strings to avoid pandas numeric inference producing "2.0" etc.
    df = pd.read_csv(path, dtype=str)
    cols = list(df.columns)
    norm_to_actual = {_norm(c): c for c in cols}

    order_col = next((norm_to_actual.get(a) for a in ORDER_ALIASES if a in norm_to_actual), None)
    process_col = next((norm_to_actual.get(a) for a in PROCESS_ALIASES if a in norm_to_actual), None)
    customer_col = next((norm_to_actual.get(a) for a in CUSTOMER_ALIASES if a in norm_to_actual), None)

    if not order_col or not process_col:
        missing = []
        if not order_col:
            missing.append("order")
        if not process_col:
            missing.append("process")
        return CsvParseResult(
            ok=False,
            df=None,
            available_columns=cols,
            reason=f"missing required columns: {', '.join(missing)}",
        )

    out = pd.DataFrame()
    out["orders Numbers"] = df[order_col].astype("string")
    out["Process Number"] = df[process_col].astype("string")
    out["Customer Name"] = df[customer_col].astype("string") if customer_col else ""

    out["orders Numbers"] = out["orders Numbers"].astype("string").str.strip()
    out["Process Number"] = out["Process Number"].astype("string").str.strip()
    out["Customer Name"] = out["Customer Name"].astype("string").fillna("").astype("string").str.strip()

    out = out[out["orders Numbers"].notna() & (out["orders Numbers"] != "")]
    out = out[out["Process Number"].notna() & (out["Process Number"] != "") & (out["Process Number"].str.lower() != "nan")]

    return CsvParseResult(ok=True, df=out[["Process Number", "orders Numbers", "Customer Name"]], available_columns=cols)

