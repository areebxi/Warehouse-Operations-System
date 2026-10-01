"""Clear Package Type / Weight / Service values that leaked into CL BTC columns.

  python scripts/fix_cl_btc_leaked_shipping.py --dry-run
  python scripts/fix_cl_btc_leaked_shipping.py
"""
from __future__ import annotations
import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from shared import paths as wh
COL_SKU = "BTC SKU"
COL_PC = "BTC Product Code"
COL_STOCK = "BTC Supplier Stock"
COL_PKG = "Package Type"
COL_WEIGHT = "Weight"
COL_SERVICE = "Service"
COL_SUP_NAME = "Supplier Name"
COL_SUP_SKU = "Supplier SKU"
COL_SUP_PC = "Supplier Product Code"
COL_SUP_STOCK = "Supplier Stock"
PACKAGE_TYPES = frozenset(
    {
        "large letter",
        "parcel",
        "small parcel",
        "rm small parcel",
        "rm large letter",
        "letter",
        "large parcel",
        "packet",
        "prime parcel",
        "prime letter",
    }
)
SERVICE_EXACT = frozenset(
    {
        "royal mail48",
        "royal mail 48 - crl",
        "tracked 24 - tpn",
        "uk_royalmail48",
    }
)
SERVICE_HINTS = ("royal mail", "tracked 24", "tracked 48", "letterbox", "parcelforce")
def cell(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return s
def is_package_type(val: str) -> bool:
    return cell(val).casefold() in PACKAGE_TYPES
def is_shipping_service(val: str) -> bool:
    v = cell(val).casefold()
    if not v:
        return False
    if v in SERVICE_EXACT:
        return True
    return any(h in v for h in SERVICE_HINTS)
def is_btc_name(val: str) -> bool:
    return "btc" in cell(val).casefold()
def sku_is_leaked(sku: str) -> bool:
    return bool(cell(sku)) and is_package_type(sku)
def stock_is_leaked(stock: str) -> bool:
    return bool(cell(stock)) and is_shipping_service(stock)
def pc_is_leaked(pc: str, *, sku: str, stock: str, weight: str, supplier_pc: str) -> bool:
    """True when BTC Product Code is a Weight (g) copy, not an SPC."""
    pc = cell(pc)
    if not pc:
        return False
    if cell(weight) and pc == cell(weight):
        return True
    if (sku_is_leaked(sku) or stock_is_leaked(stock)) and pc != cell(supplier_pc):
        return True
    return False
def plan_row(row: dict) -> dict:
    """Return patched fields for one CL row. Unchanged keys are omitted."""
    sku = cell(row.get(COL_SKU))
    pc = cell(row.get(COL_PC))
    stock = cell(row.get(COL_STOCK))
    pkg = cell(row.get(COL_PKG))
    weight = cell(row.get(COL_WEIGHT))
    service = cell(row.get(COL_SERVICE))
    sup_sku = cell(row.get(COL_SUP_SKU))
    sup_pc = cell(row.get(COL_SUP_PC))
    sup_stock = cell(row.get(COL_SUP_STOCK))
    btc = is_btc_name(row.get(COL_SUP_NAME))

    out: dict[str, str] = {}
    if sku_is_leaked(sku):
        if not pkg:
            out[COL_PKG] = sku
        out[COL_SKU] = sup_sku if btc and sup_sku else ""
    if pc_is_leaked(pc, sku=sku, stock=stock, weight=weight, supplier_pc=sup_pc):
        if not weight and pc.isdigit():
            out[COL_WEIGHT] = pc
        out[COL_PC] = sup_pc if btc and sup_pc else ""
    if stock_is_leaked(stock):
        if not service:
            out[COL_SERVICE] = stock
        out[COL_STOCK] = sup_stock if btc and sup_stock else ""
    return {k: v for k, v in out.items() if cell(row.get(k)) != v}
