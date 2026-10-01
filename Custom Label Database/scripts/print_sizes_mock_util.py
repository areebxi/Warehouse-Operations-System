"""Helpers for print_sizes_mock_analysis."""
from __future__ import annotations

import re

import pandas as pd

PP_TO_SR = {
    "Front Left Pocket, Back Center": "Left Chest & Back Print",
    "Front Center, Back Center": "Front & Back Print",
    "Back Center, Front Left Pocket": "Left Chest & Back Print",
    "Front Center, Sleeve": "?",
    "Front Center": "Front Print",
    "Front Left Pocket": "Left Chest",
    "Back Center": "Back Print",
    "Front Left Pocket, Front Bottom Left Corner": "?",
}


def clean(s) -> str:
    if pd.isna(s):
        return ""
    return str(s).strip()


def extract_mock(pp: str) -> str:
    m = re.search(r"\(M(\d+)\)", pp)
    return f"M{m.group(1)}" if m else ""


def db_gender(ga: str) -> str:
    g = ga.lower()
    if "kid" in g or "child" in g or "youth" in g or "junior" in g:
        return "Kids"
    if "men" in g or "boy" in g:
        return "Men"
    if "women" in g or "ladies" in g or "girl" in g:
        return "Women"
    return "Men"


def db_size(sz: str) -> str:
    m = {
        "1-2 Years": "1-2Y",
        "2-3 Years": "2-3Y",
        "3-4 Years": "3-4Y",
        "5-6 Years": "5-6Y",
        "7-8 Years": "7-8Y",
        "9-11 Years": "9-11Y",
        "12-13 Years": "12-13Y",
        "12-14 Years": "14-15Y",
        "14-15 Years": "14-15Y",
        "Small": "Small",
        "Medium": "Medium",
        "Large": "Large",
        "Extra Large": "XL",
        "Extra Small": "XS",
        "2XL": "2XL",
        "3XL": "3XL",
        "4XL": "4XL",
        "5XL": "5XL",
    }
    return m.get(sz, sz)


def infer_printing_position(pp: str) -> str:
    pp_clean = re.sub(r"\s*\(M\d+\)\s*$", "", pp)
    if pp_clean in PP_TO_SR:
        return PP_TO_SR[pp_clean]
    parts = re.split(r",\s*", pp_clean)
    has_front = any("front" in p.lower() and "back" not in p.lower() for p in parts)
    has_back = any("back" in p.lower() for p in parts)
    has_pocket = any("pocket" in p.lower() or "chest" in p.lower() for p in parts)
    if has_pocket and has_back:
        return "Left Chest & Back Print"
    if has_front and has_back:
        return "Front & Back Print"
    if has_pocket:
        return "Left Chest"
    if has_back and not has_front:
        return "Back Print"
    if has_front:
        return "Front Print"
    return ""
