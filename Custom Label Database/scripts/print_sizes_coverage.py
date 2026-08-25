"""Estimate print-size fill coverage by tier."""
import pandas as pd
import re
from pathlib import Path

BASE = Path(r"d:\Custom Label Database")
df = pd.read_excel(BASE / "Custom Label Database_Updated.xlsx", usecols=[
    "Supplier Product Code", "Gender Apparel", "Size", "Print Positions", "Category"
])
sr = pd.read_excel(BASE / "Configuration Workbook.xlsx", sheet_name="Size References")
ps_raw = pd.read_excel(BASE / "Print Sizes.xlsx", header=None)
ps = ps_raw.iloc[2:].copy()
ps.columns = ["Apparel Size", "A4_W", "A4_H", "A3_W", "A3_H", "Neck_W", "Neck_H"]
ps = ps.dropna(subset=["Apparel Size"])
ps_index = set(ps["Apparel Size"].astype(str))

def clean(s):
    if pd.isna(s): return ""
    return str(s).strip()

for d in (df, sr):
    for c in d.columns:
        d[c] = d[c].apply(clean)

df["Mock"] = df["Print Positions"].str.extract(r"\(M(\d+)\)", expand=False).apply(lambda x: f"M{x}" if x else "")
df["HasPP"] = df["Print Positions"] != ""

PP_MAP = {
    "Front Center": "Front Print",
    "Front Left Pocket": "Left Chest",
    "Back Center": "Back Print",
    "Front Center, Back Center": "Front & Back Print",
    "Front Left Pocket, Back Center": "Left Chest & Back Print",
    "Back Center, Front Left Pocket": "Left Chest & Back Print",
}

def pp_clean(pp):
    return re.sub(r"\s*\(M\d+\)\s*$", "", pp).strip()

def infer_sr_position(pp):
    base = pp_clean(pp)
    if base in PP_MAP:
        return PP_MAP[base]
    return ""

df["SR_Position"] = df["Print Positions"].apply(infer_sr_position)

def db_gender(ga):
    g = ga.lower()
    if any(x in g for x in ["kid", "child", "youth", "junior", "infant", "baby"]): return "Kids"
    if any(x in g for x in ["women", "ladies", "lady", "girl"]): return "Women"
    return "Men"

def db_size(sz):
    m = {
        "1-2 Years": "1-2Y", "2-3 Years": "2-3Y", "3-4 Years": "3-4Y",
        "5-6 Years": "5-6Y", "7-8 Years": "7-8Y", "9-11 Years": "9-11Y",
        "12-13 Years": "12-13Y", "12-14 Years": "14-15Y", "14-15 Years": "14-15Y",
        "Small": "Small", "Medium": "Medium", "Large": "Large",
        "Extra Large": "XL", "Extra Small": "XS", "2XL": "2XL", "3XL": "3XL",
        "4XL": "4XL", "5XL": "5XL",
    }
    return m.get(sz, sz)

df["Gender"] = df["Gender Apparel"].apply(db_gender)
df["SizeKey"] = df["Size"].apply(db_size)

# Build SR index: (mock, gender, size, printing_position) -> count suffix rows
sr["Mock"] = sr["SKU Value"].str.extract(r"^(M\d+)", expand=False)
sr_idx = set()
sr_pc_idx = {}  # (spc, gender, size, printing_position) -> set of (w,h) tuples
for _, r in sr.iterrows():
    if r["Mock"]:
        sr_idx.add((r["Mock"], r["Gender"], r["SizeKey"] if "SizeKey" in r else r["Size"], r["Printing Position"]))
    if r["Product Code"] and r["Printing Position"] and r["Gender"] and r["Size"]:
        for code in r["Product Code"].split("-"):
            key = (code, r["Gender"], r["Size"], r["Printing Position"])
            sr_pc_idx.setdefault(key, set()).add((r["Size Width"], r["Size Height"]))

# fix size in loop
for k in list(sr_pc_idx.keys()):
    pass

# Rebuild properly
sr_pc_idx = {}
for _, r in sr.iterrows():
    if not (r["Product Code"] and r["Printing Position"] and r["Gender"] and r["Size"]):
        continue
    for code in r["Product Code"].split("-"):
        key = (code, r["Gender"], r["Size"], r["Printing Position"], r["Suffix"])
        sr_pc_idx[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

n = len(df)
tier1 = (df["Mock"] != "") & df.apply(
    lambda r: (r["Mock"], r["Gender"], r["SizeKey"], r["SR_Position"]) in 
    {(m,g,s,p) for m,g,s,p in sr_idx} if r["SR_Position"] else False, axis=1
)

# Simpler tier counts
t1 = (df["Mock"] != "").sum()
t0_blank_pp = (~df["HasPP"]).sum()
t_single = df["HasPP"] & (df["Mock"] == "") & df["SR_Position"].isin(["Front Print", "Left Chest", "Back Print"])
t_dual_ambig = df["HasPP"] & (df["Mock"] == "") & df["SR_Position"].isin(["Front & Back Print", "Left Chest & Back Print"])
t_other = df["HasPP"] & (df["Mock"] == "") & ~t_single & ~t_dual_ambig

# Single position: product code lookup unique?
def pc_lookup_ok(row):
    if not row["Supplier Product Code"] or not row["SR_Position"]:
        return False
    suffixes = ["P", "F", "B", ""]
    found = []
    for suf in suffixes:
        k = (row["Supplier Product Code"], row["Gender"], row["SizeKey"], row["SR_Position"], suf)
        if k in sr_pc_idx:
            found.append(sr_pc_idx[k])
    return len(found) >= 1

single_ok = t_single & df.apply(pc_lookup_ok, axis=1)

print(f"Total rows: {n:,}")
print(f"Tier 0 - Blank Print Positions (cannot fill): {t0_blank_pp:,} ({100*t0_blank_pp/n:.1f}%)")
print(f"Tier 1 - Has mock code (M###): {t1:,} ({100*t1/n:.1f}%)")
print(f"Tier 2a - Single position, no mock: {t_single.sum():,}")
print(f"  - with Size Ref PC lookup hit: {single_ok.sum():,}")
print(f"Tier 2b - Dual position, no mock (AMBIGUOUS): {t_dual_ambig.sum():,}")
print(f"Tier 3 - Other/kebab/edge: {t_other.sum():,}")

# Print Sizes fallback for Front Center only without SR hit
fc = df["Print Positions"].apply(pp_clean) == "Front Center"
# apparel key quick check
AGE = {"1-2 Years":"1-2Y","2-3 Years":"2-3Y","3-4 Years":"3-4Y/YXS","5-6 Years":"5-6Y/YS",
       "7-8 Years":"7-8Y/YM","9-11 Years":"9-11Y/YL","12-13 Years":"12-13Y/YXL"}
def apparel_key(row):
    s = row["Size"]
    if s in AGE: return AGE[s]
    if "Men" in row["Gender"] or row["Gender"]=="Men":
        m = {"Small":"Men Small","Medium":"Men Medium","Large":"Men Large","XL":"Men XL","Extra Large":"Men XL","2XL":"Men 2XL","3XL":"Men 3XL","4XL":"Men 4XL","5XL":"Men 5XL"}
        return m.get(s,"")
    return ""
df["ApparelKey"] = df.apply(apparel_key, axis=1)
ps_fallback = fc & (df["ApparelKey"].isin(ps_index))
print(f"Print Sizes fallback (Front Center + apparel key): {ps_fallback.sum():,}")

est_fill = t1 + single_ok.sum()  # conservative
print(f"\nConservative high-confidence fill estimate: {est_fill:,} ({100*est_fill/n:.1f}%)")
est_fill_opt = t1 + t_single.sum() + t_dual_ambig.sum() * 0.5  # if we pick default mock for dual
print(f"Optimistic (incl. dual w/ default mock policy): ~{int(est_fill_opt):,}")
