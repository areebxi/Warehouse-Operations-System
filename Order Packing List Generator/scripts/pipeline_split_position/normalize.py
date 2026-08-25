import pandas as pd


def _is_blank(val) -> bool:
    """True if value is missing, empty string, or whitespace-only."""
    if pd.isna(val):
        return True
    if not isinstance(val, str):
        val = str(val)
    return val.strip() == ""


def _normalize_label(val) -> str:
    """Strip and return string for comparison; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def _normalize_logo_design_token(val) -> str:
    """Keep Logo/Design Image as integer order text, not 4055007854.0."""
    if pd.isna(val):
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    s = str(val).strip()
    if s.endswith(".0"):
        whole, dot, frac = s.partition(".")
        if dot and frac == "0" and whole.lstrip("-").isdigit():
            return whole
    return s


def _normalize_position_key(val) -> str:
    """Strip and lowercase for position lookup; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip().lower()


def _normalize_logo_id_key(val) -> str:
    """Strip and lowercase for Logo ID lookup; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip().lower()

