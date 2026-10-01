"""Areeb column headers, source maps, gender tokens, and GA regexes."""
from __future__ import annotations

import re

AREEB_COLS = (
    "Category (Areeb)",
    "Product Type (Areeb)",
    "Product Style (Areeb)",
    "Department (Areeb)",
)

BTC_SRC = {
    "Category (Areeb)": "Department",
    "Product Type (Areeb)": "Sub Department",
    "Product Style (Areeb)": "Brand",
    "Department (Areeb)": "Description",
}

UNEEK_SRC = {
    "Category (Areeb)": "Category",
    "Product Type (Areeb)": "Product Name",
    "Product Style (Areeb)": "Full Description",
    "Department (Areeb)": "Gender",
}

GENDER_MENS = "Mens"
GENDER_WOMENS = "Womens"
GENDER_KIDS = "Kids"
GENDER_UNISEX = "Unisex"
GENDER_GENERAL = "General"

SOURCE_BTC_UID = "btc_uid"
SOURCE_BTC_SPC = "btc_spc"
SOURCE_UNEEK_SHORT = "uneek_short"
SOURCE_UNEEK_CODE = "uneek_code"
SOURCE_CL_STANDARD = "cl_standard"
SOURCE_CL_GA = SOURCE_CL_STANDARD
SOURCE_CL_EXISTING = "cl_existing"
SOURCE_PLAIN_LEFTOVER = "plain_leftover"
SOURCE_NONE = ""

_KIDS_RE = re.compile(
    r"\b(children'?s|childrens?|kids?|child|youth|infant|bab(?:y|ies)|toddler|junior)\b",
    re.I,
)
_WOMENS_RE = re.compile(r"\b(women'?s|womens?|ladies|lady|girl)\b", re.I)
_PLAIN_KIDS_RE = re.compile(
    r"\b(children'?s|childrens?|kids?|youth|infant|bab(?:y|ies)|toddler|junior|girl'?s|girls|boy'?s|boys)\b",
    re.I,
)
_PLAIN_WOMENS_RE = re.compile(r"\b(women'?s|womens?|ladies|lady)\b", re.I)
_MENS_RE = re.compile(r"\b(men'?s|mens?|male|adults?)\b", re.I)
_UNISEX_RE = re.compile(r"\bunisex\b", re.I)
_HIVIS_RE = re.compile(r"hi[-\s]?vi[sz]", re.I)

_CL_BRAND_PREFIXES = (
    "fruit of the loom",
    "westford mill",
    "wfmill",
    "beechfield",
    "bagbase",
    "bagbas",
    "gildan",
    "fotl",
    "folt",
    "uneek",
    "yoko",
    "delta",
    "beech",
)
