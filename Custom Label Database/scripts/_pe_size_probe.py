"""Quick probe: ProductExport Size vs DB Size, Custom Label UID pattern."""
import pandas as pd
from pathlib import Path

BASE = Path(r"d:\Custom Label Database")
pe = pd.read_excel(BASE / "ProductExport.xlsx", usecols=lambda c: str(c).lower() in {
    "uid", "size", "sku", "spc", "product code", "colour", "color"
} or "size" in str(c).lower() or str(c).lower() in {"uid"})
print("PE columns used:", list(pe.columns))
print("PE rows:", len(pe))
# find size col
size_col = [c for c in pe.columns if "size" in str(c).lower()]
print("Size-like cols:", size_col)
if size_col:
    s = pe[size_col[0]].dropna().astype(str).str.strip()
    print("PE Size unique:", s.nunique())
    print(s.value_counts().head(25).to_string())

uid_col = [c for c in pe.columns if str(c).lower() == "uid"]
print("UID col:", uid_col)
if uid_col:
    print("UID sample:", pe[uid_col[0]].head(5).tolist())
    print("UID dtype:", pe[uid_col[0]].dtype)
