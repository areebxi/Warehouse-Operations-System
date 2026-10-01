"""Match counting for print_sizes_mock_analysis."""
from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd

from print_sizes_mock_util import db_gender, db_size, infer_printing_position


def count_mock_sku_matches(df: pd.DataFrame, sr: pd.DataFrame) -> tuple[int, int, Counter]:
    match_mock_sku = match_mock_only = 0
    match_details: Counter = Counter()
    for _, row in df[df["Mock"] != ""].iterrows():
        mock = row["Mock"]
        sku = row["Supplier SKU"]
        candidates = sr[sr["Mock"] == mock]
        if len(candidates) == 0:
            match_details["no_mock_in_ref"] += 1
            continue
        if sku:
            paren_match = candidates[candidates["SKU Value"].str.contains(f"({sku})", regex=False)]
            if len(paren_match) > 0:
                match_mock_sku += 1
                match_details["mock+sku_paren"] += 1
                continue
        match_details["mock_only_no_sku"] += 1
        match_mock_only += 1
    return match_mock_sku, match_mock_only, match_details


def count_full_key_matches(df: pd.DataFrame, sr: pd.DataFrame) -> tuple[int, int, int]:
    idx = {}
    for _, r in sr.iterrows():
        if not r["Mock"]:
            continue
        key = (r["Mock"], r["Gender"], r["Size"], r["Printing Position"], r["Suffix"])
        idx[key] = (r["Size Width"], r["Size Height"], r["Printing Size"], r["Number of Designs"])

    full_match = partial_match = no_match = 0
    for _, row in df[df["Mock"] != ""].iterrows():
        mock = row["Mock"]
        g = db_gender(row["Gender Apparel"])
        sz = db_size(row["Size"])
        ppos = infer_printing_position(row["Print Positions"])
        if not ppos:
            no_match += 1
            continue
        found = False
        for suffix in ["P", "B", "F", ""]:
            if (mock, g, sz, ppos, suffix) in idx:
                found = True
                break
        if found:
            full_match += 1
            continue
        found2 = False
        for suffix in ["P", "B", "F", ""]:
            for k in idx:
                if k[0] == mock and k[3] == ppos and k[4] == suffix:
                    found2 = True
                    break
            if found2:
                break
        if found2:
            partial_match += 1
        else:
            no_match += 1
    return full_match, partial_match, no_match


def count_product_code_fc(df: pd.DataFrame, sr: pd.DataFrame) -> tuple[int, int]:
    no_mock = df[(df["Print Positions"] != "") & (df["Mock"] == "")]
    pc_idx: dict = defaultdict(list)
    for _, r in sr[sr["Product Code"] != ""].iterrows():
        for code in r["Product Code"].split("-"):
            pc_idx[code].append(r)
    fc_only = no_mock[no_mock["Print Positions"] == "Front Center"]
    pc_match_fc = sum(1 for _, row in fc_only.iterrows() if row["Supplier Product Code"] in pc_idx)
    return len(no_mock), pc_match_fc
