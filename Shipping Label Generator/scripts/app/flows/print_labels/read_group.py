from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from scripts.app.logging.orders_audit import OrderAuditLogger


_PROCESS_PREFIX_RE = re.compile(r"^Process\s*", re.IGNORECASE)


@dataclass(frozen=True)
class OrderInput:
    order_number: str
    customer_name: str = ""


@dataclass(frozen=True)
class GroupedOrders:
    process_number: str
    orders: list[OrderInput]
    source_file: str = ""
    source_index: int = 0

    @property
    def order_numbers(self) -> list[str]:
        return [o.order_number for o in self.orders]


def _norm(s: str) -> str:
    return str(s).lower()


def _normalize_order_number(raw: str) -> str:
    """Strip whitespace and remove line breaks often introduced by Excel/CSV."""
    s = str(raw).strip()
    return s.replace("\r", "").replace("\n", "").replace(" ", "")


def _normalize_process_number(raw: str) -> str:
    """Match convert/excel behavior: 'Process 5502' -> '5502'."""
    s = _PROCESS_PREFIX_RE.sub("", str(raw).strip()).strip()
    return s or "1"


def _build_group(
    *,
    process_number: str,
    frame: pd.DataFrame,
    order_col: str,
    customer_col: str | None,
    source_file: str,
    source_index: int,
    audit: OrderAuditLogger | None,
) -> GroupedOrders:
    orders: list[OrderInput] = []
    # DTF inputs may contain repeated rows for the same order (one per item).
    # For label printing we only want one label per (order_number + customer_name) within a process.
    seen: set[tuple[str, str]] = set()
    proc = str(process_number)
    for _, row in frame.iterrows():
        on = _normalize_order_number(row[order_col])
        if not on:
            continue

        cust = ""
        if customer_col is not None:
            cust = str(row[customer_col]).strip()

        key = (on, cust)
        if key in seen:
            if audit is not None:
                audit.record(
                    outcome="print_deduped",
                    order_number=on,
                    process_number=proc,
                    customer_name=cust,
                    source_file=source_file,
                )
            continue
        seen.add(key)
        orders.append(OrderInput(order_number=on, customer_name=cust))
        if audit is not None:
            audit.record(
                outcome="print_queued",
                order_number=on,
                process_number=proc,
                customer_name=cust,
                source_file=source_file,
            )
    return GroupedOrders(
        process_number=proc,
        orders=orders,
        source_file=str(source_file or ""),
        source_index=int(source_index),
    )


def read_and_group_orders(csv_path: Path, *, audit: OrderAuditLogger | None = None) -> list[GroupedOrders]:
    df = pd.read_csv(csv_path)
    cols = list(df.columns)
    norm_cols = [_norm(c) for c in cols]

    proc_col = None
    for c, nc in zip(cols, norm_cols):
        if "process" in nc and "number" in nc:
            proc_col = c
            break

    order_col = None
    for c, nc in zip(cols, norm_cols):
        if "order" in nc:
            order_col = c
            break
    if order_col is None:
        for c, nc in zip(cols, norm_cols):
            if "num" in nc:
                order_col = c
                break

    if order_col is None:
        raise ValueError(f"Could not identify order column in {csv_path}. Columns: {cols}")

    if proc_col is None:
        df["_process"] = "1"
        proc_col = "_process"
    else:
        df[proc_col] = df[proc_col].astype("string")
        df[proc_col] = df[proc_col].fillna("").astype("string").str.strip()
        df[proc_col] = df[proc_col].map(_normalize_process_number)
        df.loc[(df[proc_col] == "") | (df[proc_col].str.lower() == "nan"), proc_col] = "1"

    df[order_col] = df[order_col].astype("string").fillna("").astype("string").str.strip()
    df = df[df[order_col].notna() & (df[order_col] != "")]

    customer_col = None
    for c, nc in zip(cols, norm_cols):
        if ("customer" in nc and "name" in nc) or ("ship to" in nc and "name" in nc) or ("ship-to" in nc and "name" in nc):
            customer_col = c
            break
    if customer_col is None and "Customer Name" in df.columns:
        customer_col = "Customer Name"
    if customer_col is None:
        customer_col = None
    else:
        df[customer_col] = df[customer_col].astype("string").fillna("").astype("string").str.strip()

    source_file_col = None
    for c, nc in zip(cols, norm_cols):
        if nc.replace(" ", "") in {"sourcefile", "source_file"} or nc == "source file":
            source_file_col = c
            break

    source_index_col = None
    for c, nc in zip(cols, norm_cols):
        if nc.replace(" ", "") in {"sourceindex", "source_index"} or nc == "source index":
            source_index_col = c
            break

    if source_file_col is not None:
        df[source_file_col] = df[source_file_col].astype("string").fillna("").astype("string").str.strip()
    if source_index_col is not None:
        df[source_index_col] = pd.to_numeric(df[source_index_col], errors="coerce").fillna(0).astype(int)

    groups: list[GroupedOrders] = []
    if source_index_col is not None:
        for (src_idx, proc), g in df.groupby([source_index_col, proc_col], sort=False):
            src_file = ""
            if source_file_col is not None and len(g) > 0:
                src_file = str(g.iloc[0][source_file_col] or "").strip()
            groups.append(
                _build_group(
                    process_number=str(proc),
                    frame=g,
                    order_col=order_col,
                    customer_col=customer_col,
                    source_file=src_file,
                    source_index=int(src_idx),
                    audit=audit,
                )
            )
    else:
        for proc, g in df.groupby(proc_col, sort=False):
            src_file = ""
            if source_file_col is not None and len(g) > 0:
                src_file = str(g.iloc[0][source_file_col] or "").strip()
            groups.append(
                _build_group(
                    process_number=str(proc),
                    frame=g,
                    order_col=order_col,
                    customer_col=customer_col,
                    source_file=src_file,
                    source_index=0,
                    audit=audit,
                )
            )

    return groups
