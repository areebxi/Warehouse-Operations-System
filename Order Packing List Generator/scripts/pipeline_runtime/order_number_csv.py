"""Coerce Order Number columns from CSV int64/float dtypes to object strings."""

from __future__ import annotations

from numbers import Integral, Real
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

_ORDER_NUMBER_KEYS = frozenset({"order number", "order number (base)"})


def _is_integer_like(val) -> bool:
    if isinstance(val, bool):
        return False
    if isinstance(val, Integral):
        return True
    if isinstance(val, Real) and not isinstance(val, bool):
        try:
            f = float(val)
        except (TypeError, ValueError, OverflowError):
            return False
        return f.is_integer()
    return False


def order_number_to_str(val) -> str:
    """Convert one order-number cell to a clean string (no float .0 suffix)."""
    if pd.isna(val):
        return ""
    if _is_integer_like(val):
        return str(int(val))
    s = str(val).strip() if isinstance(val, str) else str(val)
    if s.endswith(".0"):
        whole, dot, frac = s.partition(".")
        if dot and frac == "0" and whole.lstrip("-").isdigit():
            return whole
    return s.strip() if isinstance(val, str) else s


def _column_keys(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).strip().lower() in _ORDER_NUMBER_KEYS]


def _order_number_dtype_map(columns: Any) -> dict[str, str]:
    return {
        str(c): str
        for c in columns
        if str(c).strip().lower() in _ORDER_NUMBER_KEYS
    }


def coerce_order_number_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with Order Number / Order Number (Base) as object string columns."""
    cols = _column_keys(df)
    if not cols:
        return df
    out = df.copy()
    for col in cols:
        out[col] = out[col].map(order_number_to_str).astype(object)
    return out


def read_csv_with_order_numbers(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    dtype: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV and force Order Number columns to clean string values."""
    path = Path(path)
    header_kwargs = {
        k: v
        for k, v in kwargs.items()
        if k not in ("dtype", "converters", "usecols", "nrows", "skiprows")
    }
    header = pd.read_csv(path, encoding=encoding, nrows=0, **header_kwargs)
    order_dtypes = _order_number_dtype_map(header.columns)
    merged_dtype: dict[str, Any] = {**(dict(dtype) if dtype else {}), **order_dtypes}
    read_kwargs = dict(kwargs)
    if merged_dtype:
        read_kwargs["dtype"] = merged_dtype
    df = pd.read_csv(path, encoding=encoding, **read_kwargs)
    return coerce_order_number_columns(df)


def read_excel_with_order_numbers(
    path: str | Path,
    *,
    dtype: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read an Excel sheet and force Order Number columns to clean string values."""
    path = Path(path)
    kwargs.setdefault("engine", "openpyxl")
    header = pd.read_excel(path, nrows=0, **kwargs)
    order_dtypes = _order_number_dtype_map(header.columns)
    merged_dtype: dict[str, Any] = {**(dict(dtype) if dtype else {}), **order_dtypes}
    read_kwargs = dict(kwargs)
    if merged_dtype:
        read_kwargs["dtype"] = merged_dtype
    df = pd.read_excel(path, **read_kwargs)
    return coerce_order_number_columns(df)
