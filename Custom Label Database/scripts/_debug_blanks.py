import pandas as pd, re

sr = pd.read_excel('Configuration Workbook.xlsx', sheet_name='Size References', dtype=str).fillna('')

# C800T entry
c800 = sr[sr['SKU Value'] == 'C800T']
print('C800T entry:')
print(c800.to_string())
print()

# BZ02 entry
bz = sr[sr['SKU Value'] == 'BZ02']
print('BZ02 entry:')
print(bz.to_string())
print()

# Sweatshirt 18500 with 3XL
sw3xl = sr[(sr['Product Code'] == '18500') & (sr['Size'].str.upper().str.contains('3XL|XXX', na=False))]
print(f'SR 18500 3XL rows: {len(sw3xl)}')
print()

# Check what sizes exist for 18500
sw_sizes = sr[sr['Product Code'] == '18500']['Size'].unique()
print(f'18500 sizes: {sorted(sw_sizes)}')
print()

# The blank sweatshirts have "front-chest, left-long sleeve-front-full forearm-shoulder to sleeve"
# front-chest is position 1, sleeve is position 2
# Position 1 should get a size from SR. Let's check why it didn't.

# Check the script's mapping logic
def classify(name):
    n = name.lower().strip()
    if 'pocket' in n: return 'pocket'
    if 'sleeve' in n: return 'sleeve'
    if re.search(r'(front|back|center|chest|full)', n): return 'front_back'
    if re.search(r'(neck|nape|collar)', n): return 'neck'
    return 'other'

positions = 'front-chest, left-long sleeve-front-full forearm-shoulder to sleeve'
parts = [p.strip() for p in positions.split(',')]
for p in parts:
    print(f'  "{p}" -> classify: {classify(p)}')
print()

# The issue: "left-long sleeve-front-full forearm-shoulder to sleeve" contains "sleeve" -> classified as sleeve -> skipped
# But "front-chest" should get front_back classification and get filled
# Let's check what SR has for 18500 without mock code, Men gender, 3XL size
# The script maps "3XL" -> what?

LETTER_TO_SR = {"S": "Small", "M": "Medium", "L": "Large", "XL": "XL", "2XL": "2XL", "3XL": "3XL", "4XL": "4XL", "5XL": "5XL"}

# Check if 3XL exists in SR for 18500
for s in ['3XL', '4XL', '5XL']:
    rows = sr[(sr['Product Code'] == '18500') & (sr['Size'] == s)]
    print(f'SR 18500 Size={s}: {len(rows)} rows')

print()
# Also check Print Sizes.xlsx for 3XL sweatshirts
ps = pd.read_excel('Print Sizes.xlsx', dtype=str).fillna('')
print(f'Print Sizes columns: {list(ps.columns)}')
print(f'Print Sizes rows: {len(ps)}')
# Check if 3XL exists
ps3xl = ps[ps.apply(lambda r: '3XL' in r.values or '3xl' in r.values, axis=1)]
print(f'Print Sizes rows with 3XL: {len(ps3xl)}')
print()

# Check what sizes Print Sizes has
print('Print Sizes sample:')
print(ps.head(3).to_string())
print()
print('Print Sizes columns related to size:')
for c in ps.columns:
    if 'size' in c.lower() or 'xl' in c.lower():
        print(f'  {c}: {ps[c].unique()[:10]}')
