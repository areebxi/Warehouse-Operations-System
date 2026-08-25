"""Mock code and position mapping analysis."""
import pandas as pd
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"d:\Custom Label Database")
CONFIG = BASE / "Configuration Workbook.xlsx"
UPDATED = BASE / "Custom Label Database_Updated.xlsx"

sr = pd.read_excel(CONFIG, sheet_name="Size References")
df = pd.read_excel(UPDATED, usecols=[
    "Supplier SKU", "Supplier Product Code", "Gender Apparel", "Size",
    "Print Positions", "Category"
])

def clean(s):
    if pd.isna(s): return ""
    return str(s).strip()

for c in df.columns:
    df[c] = df[c].apply(clean)
for c in sr.columns:
    sr[c] = sr[c].apply(lambda x: clean(x) if not pd.isna(x) else "")

# Extract mock from Print Positions
def extract_mock(pp):
    m = re.search(r"\(M(\d+)\)", pp)
    return f"M{m.group(1)}" if m else ""

df["Mock"] = df["Print Positions"].apply(extract_mock)

print("=== DB Mock codes in Print Positions ===")
mock_counts = df["Mock"].value_counts()
print(mock_counts.head(15))
print(f"Rows with mock code: {(df['Mock']!='').sum():,}")
print(f"Rows without mock: {((df['Print Positions']!='') & (df['Mock']=='')).sum():,}")

# Print Positions by mock code
print("\n=== Print Positions pattern per Mock code ===")
for mock in ["M118", "M262", "M180", "M263", "M42", "M195"]:
    sub = df[df["Mock"]==mock]["Print Positions"].value_counts()
    print(f"\n{mock}:")
    for val, cnt in sub.head(3).items():
        print(f"  {cnt:5d}  {val}")

# Size References SKU Value mock patterns
sr["Mock"] = sr["SKU Value"].str.extract(r"^(M\d+)", expand=False)
print("\n=== Size Ref mock codes (unique) ===")
mock_sr = sr[sr["Mock"]!=""]["Mock"].value_counts()
print(f"Unique mocks in Size Ref: {len(mock_sr)}")
print("Top:", mock_sr.head(15).to_dict())

# Overlap
db_mocks = set(df["Mock"].unique()) - {""}
sr_mocks = set(sr["Mock"].unique()) - {""}
print(f"\nDB mocks: {sorted(db_mocks)}")
print(f"In Size Ref: {sorted(db_mocks & sr_mocks)}")
print(f"Missing from Size Ref: {sorted(db_mocks - sr_mocks)}")

# For each DB mock, what Printing Positions exist in Size Ref?
print("\n=== Size Ref Printing Position per DB mock ===")
for mock in sorted(db_mocks):
    sub = sr[sr["Mock"]==mock]
    if len(sub)==0:
        print(f"{mock}: NOT IN SIZE REF")
        continue
    ppos = sub["Printing Position"].value_counts()
    suffixes = sub["Suffix"].value_counts().to_dict()
    print(f"{mock}: {len(sub)} rows, positions={dict(ppos)}, suffixes={suffixes}")

# SKU Value number in parens - is it Supplier SKU?
print("\n=== SKU Value parenthetical number vs Supplier SKU ===")
sr_with_paren = sr[sr["SKU Value"].str.contains(r"\(\d+\)", regex=True)].copy()
sr_with_paren["ParenID"] = sr_with_paren["SKU Value"].str.extract(r"\((\d+)\)", expand=False)

# sample match attempt for M118
m118_db = df[df["Mock"]=="M118"].head(5)
print("Sample M118 DB rows:")
print(m118_db[["Supplier SKU","Supplier Product Code","Size","Print Positions"]].to_string())

m118_sr = sr[sr["Mock"]=="M118"].head(10)
print("\nSample M118 Size Ref:")
print(m118_sr[["SKU Value","Suffix","Gender","Size","Printing Position","Size Width","Size Height","Printing Size"]].to_string())

# Try matching: Mock + Supplier SKU in paren
match_mock_sku = 0
match_mock_only = 0
match_details = Counter()

for _, row in df[df["Mock"]!=""].iterrows():
    mock = row["Mock"]
    sku = row["Supplier SKU"]
    # find ref rows
    candidates = sr[sr["Mock"]==mock]
    if len(candidates)==0:
        match_details["no_mock_in_ref"] += 1
        continue
    # try paren match
    if sku:
        paren_match = candidates[candidates["SKU Value"].str.contains(f"({sku})", regex=False)]
        if len(paren_match) > 0:
            match_mock_sku += 1
            match_details["mock+sku_paren"] += 1
            continue
    # try gender+size
    match_details["mock_only_no_sku"] += 1
    match_mock_only += 1

print(f"\nMock rows: {(df['Mock']!='').sum():,}")
print(f"  mock+sku paren match: {match_mock_sku:,}")
print(f"  mock only (no sku paren): {match_mock_only:,}")
print(f"  details: {dict(match_details)}")

# Map DB Print Positions (without mock) to Size Ref Printing Position
print("\n=== DB position text -> Size Ref Printing Position mapping (manual inference) ===")
PP_TO_SR = {
    "Front Left Pocket, Back Center": "Left Chest & Back Print",
    "Front Center, Back Center": "Front & Back Print",
    "Back Center, Front Left Pocket": "Left Chest & Back Print",  # M42 reversed order
    "Front Center, Sleeve": "?",  # sleeve combo
    "Front Center": "Front Print",
    "Front Left Pocket": "Left Chest",
    "Back Center": "Back Print",
    "Front Left Pocket, Front Bottom Left Corner": "?",
}

# Count rows matchable via mock + printing position + gender + size
def db_gender(ga):
    g = ga.lower()
    if "kid" in g or "child" in g or "youth" in g or "junior" in g: return "Kids"
    if "men" in g or "boy" in g: return "Men"
    if "women" in g or "ladies" in g or "girl" in g: return "Women"
    return "Men"  # default?

def db_size(sz):
    # map Phase-standardized sizes to Size Ref format
    m = {
        "1-2 Years": "1-2Y", "2-3 Years": "2-3Y", "3-4 Years": "3-4Y",
        "5-6 Years": "5-6Y", "7-8 Years": "7-8Y", "9-11 Years": "9-11Y",
        "12-13 Years": "12-13Y", "12-14 Years": "14-15Y", "14-15 Years": "14-15Y",
        "Small": "Small", "Medium": "Medium", "Large": "Large",
        "Extra Large": "XL", "Extra Small": "XS",
        "2XL": "2XL", "3XL": "3XL", "4XL": "4XL", "5XL": "5XL",
    }
    return m.get(sz, sz)

def infer_printing_position(pp):
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

# Build index: (mock, gender, size, printing_position, suffix) -> wh
idx = {}
for _, r in sr.iterrows():
    if not r["Mock"]:
        continue
    key = (r["Mock"], r["Gender"], r["Size"], r["Printing Position"], r["Suffix"])
    idx[key] = (r["Size Width"], r["Size Height"], r["Printing Size"], r["Number of Designs"])

full_match = 0
partial_match = 0
no_match = 0

for _, row in df[df["Mock"]!=""].iterrows():
    mock = row["Mock"]
    g = db_gender(row["Gender Apparel"])
    sz = db_size(row["Size"])
    ppos = infer_printing_position(row["Print Positions"])
    if not ppos:
        no_match += 1
        continue
    # find rows for this combo
    found = False
    for suffix in ["P", "B", "F", ""]:
        key = (mock, g, sz, ppos, suffix)
        if key in idx:
            found = True
            break
    if found:
        full_match += 1
    else:
        # try without size
        found2 = False
        for suffix in ["P", "B", "F", ""]:
            for k, v in idx.items():
                if k[0]==mock and k[3]==ppos and k[4]==suffix:
                    found2 = True
                    break
        if found2:
            partial_match += 1
        else:
            no_match += 1

print(f"Mock rows full key match: {full_match:,}")
print(f"Mock rows partial: {partial_match:,}")
print(f"Mock rows no match: {no_match:,}")

# No-mock rows: product code path
print("\n=== No-mock rows: Product Code path ===")
no_mock = df[(df["Print Positions"]!="") & (df["Mock"]=="")]
print(f"Count: {len(no_mock):,}")
print("Top patterns:")
print(no_mock["Print Positions"].value_counts().head(10))

# product code lookup simulation for Front Center only
pc_idx = defaultdict(list)
for _, r in sr[sr["Product Code"]!=""].iterrows():
    for code in r["Product Code"].split("-"):
        pc_idx[code].append(r)

fc_only = no_mock[no_mock["Print Positions"]=="Front Center"]
pc_match_fc = 0
for _, row in fc_only.iterrows():
    spc = row["Supplier Product Code"]
    if spc and spc in pc_idx:
        pc_match_fc += 1
print(f"Front Center only ({len(fc_only):,}): SPC in product code index: {pc_match_fc:,}")

print("\nDONE")
