"""Deeper print-size fill simulation."""
import pandas as pd
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"d:\Custom Label Database")
UPDATED = BASE / "Custom Label Database_Updated.xlsx"
CONFIG = BASE / "Configuration Workbook.xlsx"
PRINT_SIZES = BASE / "Print Sizes.xlsx"

# --- Load references ---
size_ref = pd.read_excel(CONFIG, sheet_name="Size References")
overrides = pd.read_excel(CONFIG, sheet_name="Override Print Size")
ps_raw = pd.read_excel(PRINT_SIZES, sheet_name=0, header=None)

# Parse Print Sizes table (row 0 = group headers, row 1 = Width/Height)
ps = ps_raw.iloc[2:].copy()
ps.columns = ["Apparel Size", "A4_W", "A4_H", "A3_W", "A3_H", "Neck_W", "Neck_H"]
ps = ps.dropna(subset=["Apparel Size"])
for c in ["A4_W", "A4_H", "A3_W", "A3_H", "Neck_W", "Neck_H"]:
    ps[c] = pd.to_numeric(ps[c], errors="coerce")
print("=== Print Sizes lookup table ===")
print(ps.to_string())

# --- Size References profiling ---
def nonempty(s):
    if pd.isna(s): return False
    return str(s).strip() not in ("", "nan")

print("\n=== Size References row profiles ===")
sr = size_ref.copy()
for col in sr.columns:
    sr[col] = sr[col].apply(lambda x: str(x).strip() if nonempty(x) else "")

# Classify rows
has_gender_size = (sr["Gender"] != "") & (sr["Size"] != "")
has_print_pos = sr["Printing Position"] != ""
has_product = sr["Product Code"] != ""
has_suffix = sr["Suffix"] != ""
has_print_size = sr["Printing Size"] != ""

print(f"Total rows: {len(sr)}")
print(f"  With Gender+Size: {has_gender_size.sum():,}")
print(f"  With Printing Position: {has_print_pos.sum():,}")
print(f"  With Product Code: {has_product.sum():,}")
print(f"  With Suffix only (no gender): {(has_suffix & ~has_gender_size).sum():,}")
print(f"  With Printing Size: {has_print_size.sum():,}")
print(f"  Unique SKU Value: {sr['SKU Value'].nunique():,}")

# Sample gender+size rows
print("\nGender+Size sample:")
print(sr[has_gender_size].head(10).to_string())

print("\nPrinting Position sample:")
print(sr[has_print_pos].drop_duplicates("Printing Position").head(10).to_string())

print("\nSuffix distribution:")
print(sr["Suffix"].value_counts().head(10))

print("\nPrinting Size values:", sr["Printing Size"].value_counts().to_dict())

# SKU Value patterns
sku_samples = sr["SKU Value"].value_counts().head(20)
print("\nTop SKU Value entries:")
print(sku_samples)

# Rows where SKU looks like paper size
paper = sr[sr["SKU Value"].isin(["A3", "A4", "A5", "A6", "A9", "A10"])]
print("\nPaper size rows:")
print(paper.to_string())

# Product code rows
print("\nProduct Code unique values:")
for pc in sr["Product Code"].unique():
    if pc:
        cnt = (sr["Product Code"] == pc).sum()
        print(f"  {pc[:60]}... : {cnt}" if len(pc) > 60 else f"  {pc}: {cnt}")

# --- Load DB subset (key columns only) ---
usecols = [
    "Custom Label", "Supplier SKU", "Supplier Product Code", "Supplier Name",
    "Category", "Sub-Category", "Gender Apparel", "Size", "Colour",
    "Print Positions", "Print Position Code",
    "Position 1 Name", "Print Size 1", "Width 1 (mm)", "Height 1 (mm)",
]
df = pd.read_excel(UPDATED, usecols=usecols)
print(f"\n=== Database: {len(df):,} rows ===")

# Normalize
for c in df.columns:
    df[c] = df[c].apply(lambda x: str(x).strip() if nonempty(x) else "")

# Extract mock code from Print Positions
def extract_mock(pp):
    m = re.search(r"\(M(\d+)\)", pp)
    return f"M{m.group(1)}" if m else ""

df["Mock Code"] = df["Print Positions"].apply(extract_mock)

# Split print positions
def split_positions(pp):
    pp = re.sub(r"\s*\(M\d+\)\s*$", "", pp)
    parts = re.split(r",\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]

df["Pos_List"] = df["Print Positions"].apply(split_positions)
df["Pos_Count"] = df["Pos_List"].apply(len)

print("\nPrint position count distribution (non-empty):")
has_pp = df["Print Positions"] != ""
print(df.loc[has_pp, "Pos_Count"].value_counts().sort_index().head(10))

print("\nTop Print Positions values:")
print(df.loc[has_pp, "Print Positions"].value_counts().head(15))

# --- Build lookup indexes from Size References ---

# Index 1: SKU Value + Suffix -> (width, height, print_size if any)
sku_suffix = {}
for _, r in sr.iterrows():
    if r["SKU Value"]:
        key = (r["SKU Value"].upper(), r["Suffix"].upper())
        sku_suffix[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

# Index 2: Gender + Size + Printing Position -> (width, height, printing_size)
gss_lookup = {}
for _, r in sr[has_gender_size].iterrows():
    key = (r["Gender"], r["Size"], r["Printing Position"])
    gss_lookup[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

# Index 3: Gender + Size (no position) - if exists
gs_lookup = {}
for _, r in sr[(sr["Gender"] != "") & (sr["Size"] != "") & (sr["Printing Position"] == "")].iterrows():
    key = (r["Gender"], r["Size"])
    gs_lookup[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

print(f"\nLookup indexes: sku_suffix={len(sku_suffix)}, gss={len(gss_lookup)}, gs={len(gs_lookup)}")

# --- Map DB Size to Print Sizes apparel size ---
SIZE_TO_APPAREL = {
    # will build from Print Sizes + common DB sizes
}
# Read apparel sizes from Print Sizes
apparel_sizes = list(ps["Apparel Size"].astype(str))

def normalize_db_size_for_print(size_val, gender_apparel):
    """Try to map DB Size + Gender Apparel to Print Sizes Apparel Size key."""
    s = size_val.strip()
    ga = gender_apparel.lower()
    # Age bands
    age_map = {
        "1-2 Years": "1-2Y", "2-3 Years": "2-3Y", "3-4 Years": "3-4Y/YXS",
        "5-6 Years": "5-6Y/YS", "7-8 Years": "7-8Y/YM", "9-11 Years": "9-11Y/YL",
        "12-13 Years": "12-13Y/YXL",
    }
    if s in age_map:
        return age_map[s]
    # Letter sizes with gender
    if "men" in ga or "mens" in ga or "male" in ga:
        m = {
            "Small": "Men Small", "Medium": "Men Medium", "Large": "Men Large",
            "Extra Large": "Men XL", "Extra Small": "Men Small",
            "2XL": "Men 2XL", "3XL": "Men 3XL", "4XL": "Men 4XL", "5XL": "Men 5XL",
            "XL": "Men XL", "L": "Men Large", "M": "Men Medium", "S": "Men Small",
        }
        if s in m: return m[s]
    if "women" in ga or "ladies" in ga or "womens" in ga:
        m = {
            "Small": "Women Small", "Medium": "Women Medium", "Large": "Women Large",
            "Extra Large": "Women XL", "XL": "Women XL",
        }
        if s in m: return m[s]
    # direct match
    for a in apparel_sizes:
        if s.lower() == a.lower() or s in a:
            return a
    return ""

df["Apparel_Size_Key"] = df.apply(lambda r: normalize_db_size_for_print(r["Size"], r["Gender Apparel"]), axis=1)
mapped = (df["Apparel_Size_Key"] != "").sum()
print(f"\nDB rows mapped to Print Sizes apparel key: {mapped:,} ({100*mapped/len(df):.1f}%)")
print("Unmapped size samples:", df.loc[df["Apparel_Size_Key"]=="", "Size"].value_counts().head(15).to_dict())

# Map print position to print type column in Print Sizes
POS_TO_PRINT_TYPE = {
    "Front Center": "A4",
    "Front Left Pocket": "Neck",
    "Front Right Pocket": "Neck",
    "Back Center": "A3",
    "Front Left Pocket, Front Right Pocket": "Neck",
    # partial mappings
}
def pos_to_print_type(pos_name):
    p = pos_name.lower()
    if "back" in p and "front" not in p:
        return "A3"
    if "pocket" in p or "chest" in p or "neck" in p or "left corner" in p or "right corner" in p:
        return "Neck"
    if "sleeve" in p:
        return "Neck"  # small print - need separate logic
    if "front" in p or "center" in p or "centre" in p:
        return "A4"
    return "A4"

# --- Match strategy simulations ---
stats = Counter()

# Strategy A: Supplier Product Code + Suffix in Size References
sr_by_sku = defaultdict(list)
for _, r in sr.iterrows():
    if r["SKU Value"]:
        sr_by_sku[r["SKU Value"].upper()].append(r)

match_a = 0
for _, row in df.iterrows():
    spc = row["Supplier Product Code"].upper()
    if spc and spc in sr_by_sku:
        match_a += 1
stats["A: Supplier Product Code in SKU Value"] = match_a

# Strategy B: Supplier SKU in SKU Value
match_b = 0
for _, row in df.iterrows():
    sku = row["Supplier SKU"].upper()
    if sku and sku in sr_by_sku:
        match_b += 1
stats["B: Supplier SKU in SKU Value"] = match_b

# Strategy C: Custom Label suffix extraction
def label_suffixes(label):
    # e.g. Fruit-Of-The-Loom-Mens-T-Shirt-Black-S -> try product codes
    return label.upper()

match_c = 0
for _, row in df.iterrows():
    if row["Custom Label"].upper() in sr_by_sku:
        match_c += 1
stats["C: Custom Label exact in SKU Value"] = match_c

# Strategy D: Gender+Size from Print Sizes
ps_index = ps.set_index("Apparel Size")
match_d = 0
for _, row in df.iterrows():
    if row["Apparel_Size_Key"] and row["Apparel_Size_Key"] in ps_index.index:
        match_d += 1
stats["D: Print Sizes apparel key match"] = match_d

# Strategy E: rows with Print Positions + apparel key
match_e = 0
for _, row in df.iterrows():
    if row["Print Positions"] and row["Apparel_Size_Key"]:
        match_e += 1
stats["E: Has Print Positions + apparel size key"] = match_e

# Strategy F: Gender+Size+Printing Position in size ref
# Map DB gender
def db_gender(ga):
    g = ga.lower()
    if "men" in g or "boy" in g: return "Men"
    if "women" in g or "ladies" in g or "girl" in g: return "Women"
    return ""

match_f = 0
for _, row in df.iterrows():
    g = db_gender(row["Gender Apparel"])
    if g and row["Size"] and (g, row["Size"], "") in gs_lookup:
        match_f += 1
    # try with printing position from size ref values
stats["F: Gender+Size in Size Ref (no pos)"] = match_f

# Count gender+size combos in size ref
print("\nSize Ref Gender+Size combos:")
print(sr[has_gender_size][["Gender","Size","Printing Position","Size Width","Size Height","Printing Size"]].drop_duplicates().to_string())

# Strategy G: Product code field in size ref vs supplier product code
product_codes = set(sr["Product Code"].unique()) - {""}
match_g = 0
for _, row in df.iterrows():
    spc = row["Supplier Product Code"]
    for pc in product_codes:
        if spc and spc in pc.split("-"):
            match_g += 1
            break
stats["G: Supplier Product Code in Product Code list"] = match_g

print("\n=== Match strategy counts (rows) ===")
for k, v in stats.items():
    print(f"  {k}: {v:,} ({100*v/len(df):.1f}%)")

# Deep dive: Supplier Product Code match + suffix logic
print("\n=== Supplier Product Code match detail ===")
spc_matched = df[df["Supplier Product Code"].str.upper().isin(sr_by_sku.keys())]
print(f"Rows with SPC in SKU Value: {len(spc_matched):,}")
if len(spc_matched):
    sample_spc = spc_matched["Supplier Product Code"].value_counts().head(5).index
    for spc in sample_spc:
        rows = sr_by_sku[spc.upper()]
        print(f"\n  SPC={spc}: {len(rows)} ref rows, DB rows={(spc_matched['Supplier Product Code']==spc).sum()}")
        for r in rows[:6]:
            print(f"    suffix={r['Suffix']!r} W={r['Size Width']} H={r['Size Height']} designs={r['Number of Designs']}")

# Analyze suffix meaning from multi-design products
multi = sr[sr["Number of Designs"].astype(str).isin(["4", "4.0", "2", "2.0", "3", "3.0"])]
print(f"\nMulti-design rows: {len(multi):,}")
print("Sample multi-design SKU Values:")
for sku in multi["SKU Value"].value_counts().head(5).index:
    sub = sr[sr["SKU Value"]==sku]
    print(f"\n  SKU={sku}, designs={sub['Number of Designs'].iloc[0]}")
    print(sub[["Suffix","Size Width","Size Height","Printing Size"]].to_string())

# M01 position code pattern
print("\n=== M01 Print Position Code pattern ===")
print("F4 = Front A4, B4 = Back A4, F14/F15 = small corners")
print("Suffix F/B/S in Size Ref likely maps to Front/Back/Sleeve")

# Simulate fill for one common case: Front Center only + apparel size
sim_front = 0
sim_multi = 0
for _, row in df.iterrows():
    if not row["Print Positions"]:
        continue
    positions = row["Pos_List"]
    akey = row["Apparel_Size_Key"]
    if len(positions) == 1 and positions[0] == "Front Center" and akey:
        sim_front += 1
    if len(positions) >= 2 and akey:
        sim_multi += 1

print(f"\nSimulation: Front Center only + apparel key: {sim_front:,}")
print(f"Simulation: 2+ positions + apparel key: {sim_multi:,}")

# Check Override Print Size applicability
print("\n=== Override Print Size ===")
print(overrides.to_string())
ov_match = 0
for _, row in df.iterrows():
    label = row["Custom Label"] + row["Supplier Product Code"] + row["Supplier SKU"]
    for _, ov in overrides.iterrows():
        if str(ov["SKU Contain"]) in label:
            ov_match += 1
            break
print(f"Rows matching override contains: {ov_match:,}")

# Unique DB Supplier Product Codes fill rate
spc_nonempty = df["Supplier Product Code"] != ""
print(f"\nSupplier Product Code filled: {spc_nonempty.sum():,} ({100*spc_nonempty.mean():.1f}%)")
spc_in_ref = df["Supplier Product Code"].str.upper().isin(sr_by_sku.keys()).sum()
print(f"SPC in Size Ref SKU Value: {spc_in_ref:,}")

# Try partial SKU Value match (contains)
partial = 0
for _, row in df[spc_nonempty].iterrows():
    spc = row["Supplier Product Code"].upper()
    for sku_val in sr_by_sku:
        if spc in sku_val or sku_val in spc:
            partial += 1
            break
print(f"SPC partial match to SKU Value: {partial:,}")

print("\nDONE")
