# fill_prime_and_images.py — Step 3

Third step in the pipeline: **fill** Prime, Apparel Image, Logo/Design Image, and **Logo ID** from the step-2 enriched CSV. Overwrites Prime, Apparel Image, Logo/Design Image, and adds/overwrites **Logo ID**; other columns are passed through unchanged.

## Purpose

- Read step-2 output CSV (typically `Output/2_enrich_cl_lookup_{token}.csv`).
- **Prime:** If the Tags column contains a tag exactly equal to `"Amazon Prime Order"` (tags are split by comma and stripped), set Prime = `"Yes"`; otherwise leave blank.
- **Apparel Image:** Set equal to Picture Name for each row (copy; empty if Picture Name is empty).
- **Logo/Design Image** and **Logo ID:** Derived from `Customise`, `Order Number`, and `Item SKU` as below.
- Write result to `Output/3_fill_prime_and_images_{token}.csv` by default (you can override the output path).

## Token extraction (LG / TSU / AV / HK / fawad)

**LG / TSU / AV / HK** — pattern:

- `([0-9A-Za-z]+(?:LG|TSU|AV|HK))-[0-9A-Za-z]+`

So each match is the substring **from the start of the token through `LG`, `TSU`, `AV`, or `HK`**, immediately followed by **`-`** and at least one alphanumeric character in the suffix (the suffix matcher stops at the next hyphen, same as for fawad below).

**fawad + digits** — separate pattern (the word **fawad** is matched **case-insensitively**; the value stored in **Logo ID** / **Logo/Design Image** is exactly as it appears in the SKU, e.g. `Fawad22` vs `fawad22`):

- `(fawad\d+)-[0-9A-Za-z]+` with case-insensitive matching on `fawad`.

Example: `fawad22-M-T-BLK-XL` → captured design id **`fawad22`** (same rule as `126888LG-W-...` → `126888LG`).

**Important:** LG/TSU/AV/HK captured tokens are stored **as-is** (trimmed only). The script does **not** strip leading letters before the digits (e.g. `Mehwish21LG-BG747-...` → `Mehwish21LG`; `M39553LG-W-...` → `M39553LG`; `4486HK-White-M-T-BLK-L` → `4486HK`).

When **both** LG/TSU/AV/HK-style matches and fawad matches appear in one SKU, they are merged **by position in the string** (left-to-right), then deduplicated, joined with `", "`.

## PER fallback

When **no** LG/TSU/AV/HK/**fawad** token is found, the script may use a **PER** token from Item SKU:

- Pattern: `[A-Za-z0-9]*\d+PER` (optional letter/number prefix, then digits, then `PER`; case of `PER` unchanged).
- The **first** match is used when a PER fallback is needed.
- Examples: `98765PER` → `98765PER`; `Mehwish123PER-...` → `Mehwish123PER`.

## Rules in detail

### 1. Prime from Tags

- **Source column:** Tags.
- Split by comma, strip each part. If any part equals exactly **"Amazon Prime Order"**, set Prime = **"Yes"**; otherwise Prime is blank.
- Empty or NaN Tags → Prime blank.

### 2. Apparel Image from Picture Name

- For every row: Apparel Image = value of Picture Name (NaN/empty → empty string).

### 3. Logo/Design Image and Logo ID

- **If Customise is "Yes"** (case-insensitive, after trimming):
  - Logo/Design Image = Order Number.
  - Logo ID = all **LG/TSU/AV/HK/fawad** tokens from Item SKU (comma-separated, unique, order preserved) when any exist; if none, Logo ID = first **PER** token (`[A-Za-z0-9]*\d+PER`) or blank.

- **Else (non-custom row initially):**
  - If Item SKU has any **LG/TSU/AV/HK/fawad** tokens: Logo/Design Image and Logo ID both set to the same comma-separated list.
  - Else if Item SKU has a **PER** token:
    - Logo/Design Image = Order Number,
    - Logo ID = that PER token,
    - **Customise** is set to `"Yes"` so PDFs look up custom logos by Order Number in the custom folder.
  - Else: Logo/Design Image and Logo ID are blank.

## Usage

**From the command line:**

```bash
# Required: step-2 CSV path
python scripts/fill_prime_and_images.py Output/2_enrich_cl_lookup_902b934a-7d72-40a4-a371-65c40c2f21e5.csv

# Optional: specify output path
python scripts/fill_prime_and_images.py Output/2_enrich_cl_lookup_902b934a-7d72-40a4-a371-65c40c2f21e5.csv Output/3_fill_prime_and_images_custom.csv
```

If no output path is given, output is written to `Output/3_fill_prime_and_images_{token}.csv`, where `token` is derived from the step-2 filename (e.g. stem `2_enrich_cl_lookup_902b934a-...` → token `902b934a-...`).

**Dependencies:** `pandas` (install with `pip install -r requirements.txt`).

## Required columns

The step-2 CSV must contain: Tags, Order Number, Item SKU, Picture Name, Customise, Prime, Apparel Image, Logo/Design Image. If any are missing, the script exits with an error.

## Related helpers

- **`fill_apparel_and_logo_from_df()`** — Used when re-deriving Apparel Image and Logo/Design Image from a DataFrame (e.g. Missing Logos flow); same Logo/Design rules as above for those columns—**LG/TSU/AV/fawad** from Item SKU (does not add Logo ID in the same way as the full CSV step).

## Where it fits

Pipeline step **3 (Transform)**. Consumes `Output/2_enrich_cl_lookup_{token}.csv` and produces `Output/3_fill_prime_and_images_{token}.csv`. Runs after [enrich_cl_lookup.md](enrich_cl_lookup.md), before [split_and_assign_position_codes.md](split_and_assign_position_codes.md).
