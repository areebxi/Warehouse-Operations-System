"""BTC Product Data image filename helpers for packing slips."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from pdf_constants import BTC_PRODUCT_DATA_FILE, PRODUCT_IMAGE_FOLDER

def _image_filename_from_url(url: object) -> str:
    """Extract image filename from a BTC Product Data URL for assets/product_images lookup."""
    if url is None or (isinstance(url, float) and pd.isna(url)):
        return ""
    s = str(url).strip()
    if not s or s.startswith("["):
        return ""
    return Path(s.replace("\\", "/")).name


_COLOUR_IMAGE_BY_UID_CACHE: dict[str, str] | None = None


def _read_btc_product_data_csv(**kwargs) -> tuple[pd.DataFrame, str]:
    """Load BTC Product Data trying common encodings (exports may be cp1252)."""
    last_err: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(BTC_PRODUCT_DATA_FILE, encoding=encoding, low_memory=False, **kwargs), encoding
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
    if last_err is not None:
        raise last_err
    raise RuntimeError(f"Could not read BTC Product Data: {BTC_PRODUCT_DATA_FILE}")


def _load_colour_image_basenames_by_uid() -> dict[str, str]:
    """UID -> colour image 01 basename from BTC Product Data (colour-specific product shot)."""
    global _COLOUR_IMAGE_BY_UID_CACHE
    if _COLOUR_IMAGE_BY_UID_CACHE is not None:
        return _COLOUR_IMAGE_BY_UID_CACHE
    out: dict[str, str] = {}
    try:
        export_df, _encoding = _read_btc_product_data_csv(
            usecols=["UID", "colour image 01"],
            dtype={"UID": str},
        )
    except Exception:
        _COLOUR_IMAGE_BY_UID_CACHE = out
        return out
    if "UID" not in export_df.columns or "colour image 01" not in export_df.columns:
        _COLOUR_IMAGE_BY_UID_CACHE = out
        return out
    export_df = export_df[~export_df["UID"].astype(str).str.startswith("[", na=False)]
    export_df = export_df.drop_duplicates(subset=["UID"], keep="first")
    for _, row in export_df.iterrows():
        uid = str(row.get("UID", "")).strip()
        name = _image_filename_from_url(row.get("colour image 01"))
        if uid and name:
            out[uid] = name
    _COLOUR_IMAGE_BY_UID_CACHE = out
    return out


def _resolve_product_image_path(
    product_filename: object,
    sku_value: object,
    *,
    colour_img_by_uid: dict[str, str] | None = None,
) -> tuple[Path | None, str, str]:
    """Prefer colour-specific BTC Product Data shot, then Database product image, then SKU.ext."""
    sku_str = str(sku_value or "").strip()
    colour_map = (
        colour_img_by_uid
        if colour_img_by_uid is not None
        else _load_colour_image_basenames_by_uid()
    )
    colour01 = colour_map.get(sku_str, "") if sku_str else ""
    if colour01:
        colour_path = PRODUCT_IMAGE_FOLDER / colour01
        if colour_path.exists():
            return colour_path, "colour_image_01", colour01
    if product_filename:
        pf = PRODUCT_IMAGE_FOLDER / str(product_filename)
        if pf.exists():
            return pf, "product_image", str(product_filename)
    if sku_str:
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            candidate = PRODUCT_IMAGE_FOLDER / f"{sku_str}{ext}"
            if candidate.exists():
                return candidate, "sku_fallback", candidate.name
    return None, "none", ""
