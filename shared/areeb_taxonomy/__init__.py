"""Four Areeb 30-chain columns: maps + classify.

Plain / Packs: blank-only copy from BTC / Uneek.
Plain leftover (no UID / Short Code / SPC): Brand + Description; Category/Type from Description in BTC language.
Custom Label: warehouse `cl_standard` from Gender Apparel only. Never BTC, Uneek, Brand, or PE cells.
CL fill snaps to Hashim #038 Title Case pick-lists (type has no gender; style is a product name).
"""

from shared.areeb_taxonomy.catalogs import AreebCatalogs
from shared.areeb_taxonomy.cl_classify import classify_cl, cl_standard, leftover_cl
from shared.areeb_taxonomy.cl_rules import (
    CL_LEFTOVER_RULES,
    CL_LEFTOVER_RULES_FOLD,
    CL_STANDARD_RULES,
    CL_STANDARD_RULES_FOLD,
)
from shared.areeb_taxonomy.consts import (
    AREEB_COLS,
    BTC_SRC,
    GENDER_GENERAL,
    GENDER_KIDS,
    GENDER_MENS,
    GENDER_UNISEX,
    GENDER_WOMENS,
    SOURCE_BTC_SPC,
    SOURCE_BTC_UID,
    SOURCE_CL_EXISTING,
    SOURCE_CL_GA,
    SOURCE_CL_STANDARD,
    SOURCE_NONE,
    SOURCE_PLAIN_LEFTOVER,
    SOURCE_UNEEK_CODE,
    SOURCE_UNEEK_SHORT,
    UNEEK_SRC,
)
from shared.areeb_taxonomy.load import (
    apply_areeb,
    apply_blank_only,
    load_btc_csv,
    load_btc_into,
    load_catalogs,
    load_uneek_into,
    load_uneek_xlsx,
)
from shared.areeb_taxonomy.plain import plain_leftover
from shared.areeb_taxonomy.values import (
    AreebValues,
    cell,
    coalesce_areeb,
    from_src_row,
    keyfold,
)

__all__ = [
    "AREEB_COLS",
    "BTC_SRC",
    "UNEEK_SRC",
    "GENDER_MENS",
    "GENDER_WOMENS",
    "GENDER_KIDS",
    "GENDER_UNISEX",
    "GENDER_GENERAL",
    "CL_STANDARD_RULES",
    "CL_LEFTOVER_RULES",
    "CL_STANDARD_RULES_FOLD",
    "CL_LEFTOVER_RULES_FOLD",
    "SOURCE_BTC_UID",
    "SOURCE_BTC_SPC",
    "SOURCE_UNEEK_SHORT",
    "SOURCE_UNEEK_CODE",
    "SOURCE_CL_STANDARD",
    "SOURCE_CL_GA",
    "SOURCE_CL_EXISTING",
    "SOURCE_PLAIN_LEFTOVER",
    "SOURCE_NONE",
    "AreebValues",
    "AreebCatalogs",
    "cell",
    "keyfold",
    "coalesce_areeb",
    "from_src_row",
    "cl_standard",
    "leftover_cl",
    "classify_cl",
    "plain_leftover",
    "load_btc_into",
    "load_uneek_into",
    "load_btc_csv",
    "load_uneek_xlsx",
    "load_catalogs",
    "apply_blank_only",
    "apply_areeb",
]
