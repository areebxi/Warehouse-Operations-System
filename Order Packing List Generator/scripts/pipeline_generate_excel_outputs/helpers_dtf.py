import re
from pathlib import Path
import pandas as pd
from .config import (
    DTF_COL_COMPANY_LABEL,
    DTF_COL_OLD_LABEL,
    EXCEL_PROCESS_NO_DASH,
    _DTF_DESIGN_HEAD_FAWAD,
    _DTF_DESIGN_HEAD_LG,
    _DTF_DESIGN_HEAD_PER,
)
from .helpers_process import (
    _normalize,
    _tracker_seq_from_val,
    _file_level_seq,
    _process_number_for_excel_from_row,
    _extended_process_and_item_number,
    _process_number_for_excel,
    _process_plus_additional,
    _base_additional_no_dash,
    _item_number_from_extended,
)
def _split_item_sku_by_lg(sku: str) -> list[str]:
    s = _normalize(sku)
    if not s:
        return [s]
    starts = sorted(
        {m.start() for m in re.finditer(r"\d+(?:LG|TSU|AV|HK)", s, re.IGNORECASE)}
        | {m.start() for m in re.finditer(r"(?i)fawad\d+", s)}
    )
    if len(starts) < 2:
        return [s]
    segments = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(s)
        seg = s[start:end].strip()
        if seg:
            segments.append(seg)
    return segments if segments else [s]
def _gender_colour_size_combo_hyphenated(row: pd.Series) -> str:
    g = _normalize(row.get("Gender Apparel", ""))
    c = _normalize(row.get("Colour", ""))
    s = _normalize(row.get("Size", ""))
    return "-".join(filter(None, [g, c, s]))
def _order_number_base(row_or_series) -> str:
    return _normalize(row_or_series.get("Order Number (Base)", ""))
def load_dtf_sku_mapping(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    df = pd.read_csv(path, encoding="utf-8-sig")
    for col in (DTF_COL_COMPANY_LABEL, DTF_COL_OLD_LABEL):
        if col not in df.columns:
            raise ValueError(
                f"New SKU database for DTF must have column {col!r}: {path}"
            )
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        new_l = row.get(DTF_COL_COMPANY_LABEL)
        old_l = row.get(DTF_COL_OLD_LABEL)
        if pd.isna(new_l):
            continue
        key = str(new_l).strip().lower()
        if not key or key in mapping:
            continue
        if pd.isna(old_l):
            continue
        old_str = str(old_l).strip()
        if not old_str:
            continue
        mapping[key] = old_str
    return mapping
def _dtf_split_design_prefix(s: str) -> tuple[str, str] | None:
    m = _DTF_DESIGN_HEAD_LG.match(s)
    if m:
        return m.group(1) + "-", m.group(2).strip()
    m = _DTF_DESIGN_HEAD_FAWAD.match(s)
    if m:
        return m.group(1) + "-", m.group(2).strip()
    m = _DTF_DESIGN_HEAD_PER.match(s)
    if m:
        return m.group(1) + "-", m.group(2).strip()
    return None
def _remap_dtf_item_sku(segment: str, mapping: dict[str, str]) -> str:
    s = _normalize(segment)
    if not s or not mapping:
        return s

    sp = _dtf_split_design_prefix(s)
    if sp is not None:
        design_prefix, company_tail = sp
        old = mapping.get(company_tail.lower())
        if old:
            return design_prefix + old
        return s

    dash = s.find("-")
    if dash != -1:
        leading = s[: dash + 1]
        rest = s[dash + 1 :].strip()
        sp2 = _dtf_split_design_prefix(rest)
        if sp2 is not None:
            design_prefix, company_tail = sp2
            old = mapping.get(company_tail.lower())
            if old:
                return leading + design_prefix + old
            return s
        old = mapping.get(rest.lower())
        if old:
            return leading + old

    old = mapping.get(s.lower())
    return old if old else s
