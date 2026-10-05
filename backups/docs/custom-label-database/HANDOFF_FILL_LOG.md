# Custom Label Database — Agent snapshot

**Updated:** 2 October 2026 (sorter UNMATCHED fill + N01/ClaPk/Yes-family add_labels)  
**Standing brief:** `AGENTS.md` (handbook) · Parent map: `../AGENTS.md`  
**Facts:** `docs/FINDINGS.md` · **Paths:** `docs/WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/`

---

## Sorter UNMATCHED fill — 2 Oct 2026

Supervisor **fill** from sorter `Input/02-10-2026/1st Shift/UNMATCHED.csv`. **+6** CL rows. Backup: `backups/Custom_Label_Database_preAdd_20261002_092706.csv`. Then `sync_database_transfer.py` → CL Database **132,605** rows; Size References **97,845**. Transfer backups `Workbook_preSync_20261002_092712.xlsx` / `Configuration Workbook_preSync_20261002_092712.xlsx`.

| Packing SKU | Custom Label | Notes |
|---|---|---|
| `166213LG-M-SS-GHR-L-Yes` | `M-SS-GHR-L-Yes` | Mens-Sweatshirt Graphite Heather Large. Peer `M-SS-GHR-L`. |
| `190527LG-F/B-M-T-NVY-S-YES` | `F/B-M-T-NVY-S-YES` | Mens-T-Shirt Navy Small, Front+Back. Family peer `F/B-M-T-NVY-*-YES`. |
| `50BLG-P5-ACPPLQ-A710-PB` | `P5-ACPPLQ-A710-PB` | Photo Acrylic **A7 10mm**. Peer `ACPPLQ-A710-PB` / acrylic paper. |
| `128967LG-W101-ClaPk-O/S-Yes` | `W101-ClaPk-O/S-Yes` | BG-W101 Classic Pink O/S. `ClaPk` colour map. |
| `189385LG-N01-P7-67361` | `N01-P7-67361` | GILDAN Softstyle Youth Red XS via UID peer `M94-67361`. |
| `189356LG-M407-P1-1D114` | `M407-P1-1D114` | Photo Acrylic **A5 15mm** default (no PE/CL peer for `1D114`). |

`add_labels`: mock codes allow `N##` + alphanumeric trailing; `-Yes` shirts clone colour-family size peers; bag `ClaPk` → Classic Pink; alnum mock UID with no peer falls back to `A515-PHOTO`.

---

## Sorter UNMATCHED fill — 30 Sep 2026

Supervisor **fill** from sorter `Input/30-09-2026/1st Shift/UNMATCHED.csv`. **+4** CL rows. Backup: `backups/Custom_Label_Database_preAdd_20260930_084615.csv`. Then `sync_database_transfer.py` → CL Database **132,599** rows; Size References **97,845**. Transfer backups `Workbook_preSync_20260930_084623.xlsx` / `Configuration Workbook_preSync_20260930_084623.xlsx`.

| Packing SKU | Custom Label | Notes |
|---|---|---|
| `164988LG-M-T-VINHRR-2XL` | `M-T-VINHRR-2XL` | Mens-T-Shirt Vintage Heather Red 2XL. Peer `M-T-VINHRR-XL`. On Demand. |
| `129034LG-BG-W830-NVY-L-YES` | `BG-W830-NVY-L-YES` | BG-W830 Navy Large. Customise Yes. Peer `W830-NVY-L`. |
| `PLAIN-ACPPLQ-A710-PB` | `ACPPLQ-A710-PB` | Photo Acrylic **A7 10mm** 74×105. Customise blank. Sorter finish stays **plain** (`plain` in SKU); attributes from CL. |
| `49731LG-ARM-BBe-C1-D6-EF` | `ARM-BBe-C1-D6-EF` | Mens-Hoodie Light Blue Large (`D6-EF` = Large via AS3 peers). Listing title said Womens; catalog ARM series is Mens. |

`add_labels`: acrylic paper now includes **A7**; Amazon size codes `ARM-…-D#-E#` clone colour-family + size-suffix peers.

---

## Role

Warehouse Automation System Engineer on this catalog domain; user is supervisor. No production writes without **yes / do it / fill / run**. One problem at a time. Prefer CSV. **Save everything as we go** (parent CL rules + docs + `AGENTS.md`) — chat is not memory.

**Standing fill chat (from 1 Sep 2026):** this thread is for Custom Label catalog fills and Size References fills. Live files: `database/shared/custom_label/Custom_Label_Database.csv` and `database/custom-label-database/support/Size References.csv`. Propose + dry-run, then wait for **yes / fill / run**. After a catalog seed, run `fill_from_seeds.py` then `fill_size_references_from_cl.py`. **Then** `sync_database_transfer.py` (locked 2026-09-25) so `Database Transfer/Workbook.xlsx` + `Configuration Workbook.xlsx` mirror those CSVs. Size References columns: no `SKU Value 2` / `SKU Value 3` (supervisor removed 2026-09-25).

---

## Live now

Live catalog: `database/shared/custom_label/Custom_Label_Database.csv`.

### Warehouse stock colour gate — 23 Sep 2026

Supervisor **fill**. `Supply Method` overwritten on the live CSV. Backup `database/shared/custom_label/backups/Custom_Label_Database.bak_20260923_103520.csv`. Plain / Packs unchanged.

| | Warehouse Stock | In House Manufacture | Supplier On Demand |
|---|---:|---:|---:|
| Before | 84,097 | 458 | 47,669 |
| After (132,224 rows) | 63,399 | 458 | 68,367 |

**21,728** cells written. **21,213** FOTL tees left Warehouse Stock (colour off that department’s list: Mens 11,823 including 73 baseball two-tones, Kids 7,362, Ladies 2,028). **515** entered: C800T 416 + C8030T 99. Re-read matched the rule on every row.

### M25 SPC 61033 + Size References — 22 Sep 2026

Queue warned missing size reference on `DTF Des-P200.xlsx` for `309574LG-M233-171736` / `140211LG-M25-17259`. Both **already** in CL + Size References with correct Front Print A4 mm (267×378 Large / 250×353 7-8Y). Queue CL lookup succeeds when `cl_csv_path` points at the live catalog.

**Same product code + same mock:** M233 / SPC `61430` already complete (188/188). M25 / SPC `61033` was 8/164 — filled the rest.

| Step | Result |
|---|---|
| `add_labels.py --all-spc --skus 140211LG-M25-17259` | **+156** CL `M25-{UID}` (132,068 → **132,224**). Backup `Custom_Label_Database_preAdd_20260922_192956.csv`. |
| Fix 14-15 Years | **24** new rows had wrong **176×250** (3-4Y); set to **237×336** (Small — Print Sizes has no 14-15 band; matches older M25 14-15Y). Backup `…_preFixM25_14_15_20260922_193101.csv`. Same fix on SR (`Size_References_preFixM25_14_15_20260922_193153.csv`). `AGE_TO_PRINT` now maps 14-15 → Small for future fills. |
| `fill_size_references_from_cl.py` | **+156** SR keys `M25 ({UID})` (97,338 → **97,494**). Backup `Size_References_preFill_20260922_193117.csv`. |

Front Print A4 audit vs `Shirts Print Sizes.csv`: M233 / M25 **0** mismatches after fill. Catalog-wide rewrite (supervisor **yes**): script `scripts/rewrite_front_print_a4_from_shirts.py` — **SR 1,750** Front Print A4 mock+UID cells + **CL 5,908** matching front Width/Height → exact A4 band mm. Pocket / A3 / non-front untouched. Backups `Size_References_preRewriteFrontA4_20260922_193426.csv`, `Custom_Label_Database_preRewriteFrontA4_20260922_193428.csv`.

### Acrylic unmatched SKUs — 22 Sep 2026

Supervisor **fill** from sorter `UNMATCHED.csv` (22-09-2026). **+4** CL rows (132,064 → **132,068**). Size References: **not applicable** (A5/A6 already present). Backup: `backups/Custom_Label_Database_preAdd_20260922_072438.csv`.

| Packing SKU | Custom Label | Action |
|---|---|---|
| `48BLG-P5-ACPPLQ-A525-PB` | `P5-ACPPLQ-A525-PB` | New. Photo Acrylic **A5 25mm**. 148×210. Customise Yes (`P5-`). |
| `48BLG-P5-ACPPLQ-A615-PB` | `P5-ACPPLQ-A615-PB` | New. Photo Acrylic **A6 15mm**. 105×148. Customise Yes. |
| `ACPPLQ-A525-PHOTO` | `A525-PHOTO` | New. Same pattern as `A515-PHOTO`. A5 25mm. 148×210. Customise blank (PHOTO suffix, not size-only). |
| `A515` | `A515` | New. Size-only listing SKU. **Always Customise Yes** (supervisor: always personalised). A5 15mm. 148×210. Sorter matches no-dash SKUs on whole Custom Label. |

Skipped: `SET41527` (supervisor will add to Packs); `189364LG-N217-P3-1D77` (next: **neutral database**). Mixed supply-method is a sorter lock, not a catalog fill.

`customise_for_label`: whole-label `A[4-6]`+two digits (`A515`) → Yes. `A515-PHOTO` stays the PHOTO path (blank unless P/Yes).

### Gildan 5000 packing codes — 20 Sep 2026

Supervisor **fill** from Queue Missing Logo on `DTF Des-P50.xlsx` (orders `204-6556766-6800323` / `205-2632137-2622749`). Packing SKUs `128357LG-5000-NAT-S` / `128357LG-5000-LPNK-XL` → Custom Labels **`5000-NAT-S`** / **`5000-LPNK-XL`**. **+2** rows (132,062 → **132,064**). Backup: `backups/Custom_Label_Database_preAdd_20260920_073706.csv`. Cloned GA/colour/size from existing `A3-5000-…` peers; millimetres from Shirts Print Sizes. Did **not** add an `A3-` matcher join. Size References: **not applicable**.

Apparel Image on those two rows: supervisor **fix** `TShirt` → `T-Shirt` (live write after CSV unlocked). Backup `Custom_Label_Database_preFixApparel_20260920_074610.csv`. New `add_labels` clones hyphen `TShirt` going forward. Do not bulk-rename the rest of the catalog.

### W-H-BLK-M — 18 Sep 2026

Supervisor **add** from Packing preflight `Preflight Issues_18-09-2026_16-05-44.csv` (order 49892, Unmatched SKU only). Packing SKU `75931-W-H-BLK-M` → Custom Label **`W-H-BLK-M`**. **+1** row (132,061 → **132,062**). Backup: `backups/Custom_Label_Database_preAdd_20260918_161230.csv`. Size References: **not applicable** (not mock+UID; Medium A4 from Shirts Print Sizes).

Same warehouse-code family as `M-H-BLK-M` / `M-T-BLK-M`. Prefix `75931` is BTC UID for FOTL Ladies Classic Hooded Sweat 62038 Black M (matches Item Name). Gender Apparel **`Womens-Hoodie`** (added to `CL_STANDARD_RULES`). On Demand (hoodie, not a FOTL tee). Customise blank. 267×378 Front Center DTF. `add_labels` now seeds `M|W|K`-`T|H|…`-colour-size labels.

### C800T age-token twins — 17 Sep 2026

Supervisor **fill**. No sorter decoding: `&gt;` / `>` / `-` stay distinct Custom Labels. **+11** rows (132,050 → **132,061**) so each existing M281 C800T series has all three spellings. Backup: `backups/Custom_Label_Database_preAdd_20260917_132821.csv`. Size from the age token (0-3 Months on `0-3` / `0&gt;3`, not the old `0>3` P5 row which is still 3-6 Months). P5/P3 Customise Yes; no-P blank. Absolute / On Demand / DTF / 110×150. Size References unchanged.

| Series | Already had | Added |
|---|---|---|
| `M281-P5-C800T-30-` ages 0–3 / 3–6 / 6–12 / 12–18 / 18–24 | mix of `>` `&gt;` `-` | `0-3`, `3-6`, `6-12`, `6&gt;12`, `12>18`, `12-18`, `18>24` |
| `M281-P3-C800T-30-` 0–3 | `0>3` | `0&gt;3`, `0-3` |
| `M281-C800T-30-` 3–6 (no P) | `3>6` | `3&gt;6`, `3-6` |

Did **not** invent extra P3 / no-P ages. Did **not** rewrite existing rows.

### Unmatched sorter SKUs — 17 Sep 2026

Supervisor **add** from the 17 Sep unmatched list. **+8** CL rows (132,042 → **132,050**). Backup: `backups/Custom_Label_Database_preAdd_20260917_103000.csv`. Size References: **not applicable** (none are plain `M##-UID`; `C800T` / `A4` / `A6` keys already exist).

Skipped on purpose:

| Packing SKU | Why |
|---|---|
| `189364LG-N217-P3-1D77` | Supervisor: do not add; teach N217 structure later. Blank-GA `N217-P3-1D77` was deleted 16 Sep. |
| `SET5722` | Already in Packs (`Channel Child SKU`). Do **not** put in CL (sorter would treat the pack as printed). |
| `208544` | Already in Plain Database (Beechfield B655 Vintage Sage Green). Unmatched this run because **blank ship-by**, not missing catalog. Sorter CL key needs a dash, so a CL row would not help. |

| Packing SKU | Custom Label | Action |
|---|---|---|
| `DTF-Transfer-1M-1` | `Transfer-1M-1` | Re-added with GA **`Only-Design`** (blank-GA row was deleted 16 Sep). Size 1M. Iron-On / Iron-On Transfer / Standard. On Demand. Not in-house (DTF gang sheet is not iron-on/sticker in the SKU). |
| `DTF-Transfer-3M` | `Transfer-3M` | Same. Size 3M. |
| `802152LG-STICKERS-L(50cmx50cm)-YES` | `STICKERS-L(50cmx50cm)-YES` | New. Cloned L 40cm sticker. Size **50cm x 50cm**. In House. Customise Yes. |
| `112632LG-BG-BG140S-ClaRdOW-O/S-YES` | `BG-BG140S-ClaRdOW-O/S-YES` | New. **ClaRdOW** = Classic Red-Off White (PE UID 147042). Cloned BG140S cousin. Customise Yes. On Demand. |
| `19BLG-P5-ACPPLQ-A425-PB` | `P5-ACPPLQ-A425-PB` | New. Photo Acrylic **A4 25mm**. 210×297. Customise Yes. |
| `11202ALG-M281-P5-C800T-30-18&gt;24` | `M281-P5-C800T-30-18&gt;24` | New. Literal `&gt;` kept distinct from `18-24`. White 18-24 Months. 110×150. Absolute. Customise Yes. |
| `1803ALG-M281-P3-C800T-30-0>3` | `M281-P3-C800T-30-0>3` | New. P3 (not P5). Size **0-3 Months** from the age token. Absolute. Customise Yes. |
| `ACPPLQ-A625-PHOTO` | `A625-PHOTO` | New. Same pattern as `A515-PHOTO` (sorter after-first-dash). A6 25mm. 105×148. Customise blank (no P/Yes). |

`add_labels` now clones `BG-BG#` colour tokens (`ClaRdOW`), sticker cm from the label (not A4 iron-on), and DTF `Transfer-*` with `Only-Design`.

### M76 × SPC 61082 — 16 Sep 2026

Supervisor **fill**. UID `3263` product code **61082** (FOTL Mens Original T). All **134** BTC UIDs now `M76-{UID}` in CL and `M76 ({UID})` in Size References. `M76-3263` already present; **+133** CL (131,909 → **132,042**); **+133** SR (97,204 → **97,337**). Cloned GA/Colour/Size from same-UID Front Center FOTL cousins (not Black Small on every row). Print Positions Front Center. Warehouse Stock. Customise blank. `add_labels.py --all-spc M76-3263` then `fill_size_references_from_cl.py`. Backups: `Custom_Label_Database_preAdd_20260916_121240.csv`, `Size_References_preFill_20260916_121306.csv`. `add_labels` same-UID peer now scores Front Center + FOTL over pocket mocks.

### Size References — M76 (3263) — 16 Sep 2026

Supervisor **add** packing SKU `419894LG-M76-3263`. Custom Label `M76-3263` **already in CL** (15 Sep unmatched add) — no second CL row. Size References was missing. **+1** SR row `M76 (3263)`: Men / Small / Front Print / 237×336 / A4 / Product Code `61430-61036` (M76 mock). Backup: `database/custom-label-database/support/backups/Size_References_preFill_20260916_115442.csv`.

### Hashim #038 Areeb pick-list — 16 Sep 2026

Supervisor **refill live catalog, CL only** (Plain / Packs stay supplier product data). Four blank-GA rows deleted by supervisor: `N217-P3-1D77`, `Transfer-3M`, `Transfer-1M-1`, `208544` (131,913 → **131,909**). Morning rewrite (`--target cl`) changed **0** Areeb cells (old harvest already matched). Backup `Custom_Label_Database.bak_20260916_083255.csv`.

**Squeezed refill 10:17** (supervisor **fill**): same script `--target cl`. **131,909** rows; **131,741** rewritten; **298,338** Areeb cells; **168** already matching; **0 blank / 0 off-list**. Backup `Custom_Label_Database.bak_20260916_101719.csv`. Live cells: Title Case; Product Type has no gender; Product Style is a named product (never a code); Department is gender only. Source `shared/taxonomy_catalog.py`. Pick-list: `database/order-grouping-sorter/taxonomy_picklists.csv`.

### Supplier Name grouping — 9 Sep 2026

Canonical cells: `BTC Activewear` / `Uneek Clothing` / `Absolute Apparels`. **Filled 2026-09-09.** CL: 123,948 / 6,992 / 499 Absolute / 453 in-house blank. Plain: 71,047 BTC / 6,992 Uneek. Packs: 38,452 BTC Activewear. Backups: `Custom_Label_Database.bak_20260909_185544.csv`, `Plain Database.bak_20260909_185710.xlsx`, `Packs Database.bak_20260909_185937.xlsx`. Rule: parent `supplier-name.mdc`. Code: `shared/supplier_name.py`.

Main filler: `python scripts/fill_from_seeds.py`. Fast add: `python scripts/add_labels.py --skus …` (named-only, append-only). Size References reverse fill: `python scripts/fill_size_references_from_cl.py --dry-run`.

### Unmatched sorter SKUs — 15 Sep 2026

Supervisor **add** from `Order Packing List Generator/Input/15-09-2026/1st Shift/UNMATCHED.csv` (18 rows, 16 unique Item SKUs). **+11** rows (131,902 → **131,913**). 5 already in CL (casefold). Backups: `backups/Custom_Label_Database_preAdd_20260915_132106.csv`, `…_preFill_20260915_132541.csv`.

| Packing SKU | Custom Label | Action |
|---|---|---|
| `DTF-Transfer-3M` | `Transfer-3M` | New. DTF gang sheet. Seed blank on purpose. On Demand / BTC leftover. |
| `DTF-Transfer-1M-1` | `Transfer-1M-1` | New. Same. First fill leaked UID `1` → Gildan — **cleared**. `uid_from_custom_label` now skips `Transfer`. |
| `419894LG-M76-3263` | `M76-3263` | New 15 Sep. Same UID as `M260-P5-3263` (FOTL Original T Black Small). Warehouse Stock. 237×336. Size References `M76 (3263)` added 16 Sep. |
| `11890ALG-M281-P5-C800T-30-12&gt;18` | `M281-P5-C800T-30-12&gt;18` | New. Literal `&gt;` kept distinct. Cloned C800T-BS White. Size **12-18 Months**. 110×150. Absolute. Customise Yes. |
| `178567LG-M-T-NAV-XL-YES` | `M-T-NAV-XL-YES` | New. Supervisor: **NAV = Navy**. Cloned Mens-T-Shirt Navy Extra Large (`NVY` peer). Warehouse Stock. Customise Yes. 267×378. Label keeps `NAV`. |
| `178567LG-M-T-PUE-L-YES` | `M-T-PUE-L-YES` | New. Supervisor: **PUE = Purple**. Cloned Mens-T-Shirt Purple Large (`PRP` peer). Warehouse Stock. Customise Yes. 267×378. Label keeps `PUE`. |
| `13405LG-F/F-K-T-CBLU-YXL-Yes` | `F/F-K-T-CBLU-YXL-Yes` | New. Cloned CBLU Yes cousin. Size **12-14 Years** (YXL + RED YXL sibling). Warehouse Stock. |
| `13405LG-F/F-K-T-RED-YXL-Yes` | `F/F-K-T-RED-YXL-YES` | Already in CL. |
| `802135LG-STICKERS-L(40cmx40cm)-YES` | `STICKERS-L(40cmx40cm)-YES` | New. Cloned sticker L. In House. Customise Yes. |
| `802059LG-STICKERS-L(40cmx40cm)` | `STICKERS-L(40cmx40cm)` | New. Cloned sticker L. In House. Customise blank. |
| `129058LG-K-T-FGRN-YS-YES` | `K-T-FGRN-YS-YES` | New. Cloned `K-T-FGRN-YS`. Forest Green 5-6. Warehouse Stock. Customise Yes. |
| `98765LG-BG-BG125-MUD-O/S-YES` | `BG-BG125-MUD-O/S-YES` | Already in CL. |
| `77009LG-F/F-SH1808-REDGY-O/S-Yes` | `F/F-SH1808-REDGY-O/S-Yes` | Already in CL. |
| `208544` | `208544` | New. Whole-SKU BTC UID (Beechfield B655). Brand/Category filled. GA blank (no mock seed). |
| `-C8030T-WHI-0-3M` | `C8030T-WHI-0-3M` | Already in CL (after first dash). |
| `189382LG-N220-P3-55713` | `N220-P3-55713` | Already in CL. |

`uid_from_custom_label`: skip `Transfer`; all-digit label is a UID (`208544`). Shirt colour aliases for peer lookup only: **NAV → NVY (Navy)**, **PUE → PRP (Purple)**.

### Unmatched sorter SKUs — 14 Sep 2026

Supervisor **fill**. **+7** rows (131,895 → **131,902**). Backup: `backups/Custom_Label_Database_preAdd_20260914_092337.csv`.

| Packing SKU | Custom Label | Action |
|---|---|---|
| `1636ALG-M263-P5-DTF-IronOn-A4` | `M263-P5-DTF-IronOn-A4` | New. Cloned `DTF-IronOn-A4`. In House. Customise Yes (`-P5-`). |
| `922ALG-M260-P2-17259` | `M260-P2-17259` | New. Cloned `M260-P5-17259` (Kids Valueweight Light Pink 7-8). Warehouse Stock. Customise Yes (`-P2-`). |
| `189364LG-N217-P3-1D77` | `N217-P3-1D77` | New. **No peer** (photo slate; not in CL/Mocks). Customise Yes. Supply On Demand / BTC leftover. Gender Apparel blank on purpose — do not guess slate. |
| `110419LG-F4-M-T-NVY-M-Yes` | `F4-M-T-NVY-M-Yes` | New. Cloned `F4-M-T-NVY-M`. Warehouse Stock Navy Medium. Customise Yes token. |
| `802058LG-STICKERS-M(30cmx30cm)` | `STICKERS-M(30cmx30cm)` | New. Cloned `STCKR-M(30cmx30cm)`. In House. Customise blank (no P/Yes). |
| `47BLG-P5-ACPPLQ-A625-PB` | `P5-ACPPLQ-A625-PB` | New. Photo Acrylic. Size **A6 25mm**. 105×148. Customise Yes. |
| `50BLG-P5-ACPPLQ-A415-PB` | `P5-ACPPLQ-A415-PB` | New. Photo Acrylic. Size **A4 15mm**. 210×297. Customise Yes. |

`add_labels` now clones iron-on `M##-P#-DTF-IronOn-A#`, sticker `STICKERS-M(…)`, `-Yes` shirt cousins, and acrylic A6.

### Unmatched sorter SKUs — 11 Sep 2026

Supervisor **fill**. **+3** rows (131,892 → **131,895**). Backup: `backups/Custom_Label_Database_preAdd_20260911_145305.csv`.

| Packing SKU | Custom Label | Action |
|---|---|---|
| `11828ALG-M281-P5-C800T-30-6>12` | `M281-P5-C800T-30-6>12` | New. Cloned `M281-P5-C800T-30-3>6` (C800T-BS White). Size **6-12 Months**. 110×150. Customise Yes. Absolute Apparels. |
| `10182ALG-M281-C800T-30-3>6` | `M281-C800T-30-3>6` | New. Listing omitted `-P5-`. Cloned P5 cousin. Size 3-6 Months. Customise **blank** (no P-token — do not guess P5). Absolute Apparels. |
| `32BLG-P5-ACPPLQ-A410-PB` | `P5-ACPPLQ-A410-PB` | New. Photo Acrylic peer `A515-PHOTO`. Size **A4 10mm** from A410 (same pattern as A515 = A5 15mm). 210×297. Customise Yes (leading `P5-`). BTC Activewear leftover. |

`add_labels` now clones C800T without `-P#-`, seeds ACPPLQ acrylic from `A515-PHOTO`, and `customise_for_label` treats leading `P{digit}-` as personalised. Areeb / Supply Method / Printing Type / Supplier Name run on the new rows before append.

### Customise = Yes token — 4 Sep 2026

Supervisor: **`Yes` anywhere in our SKU/Custom Label = personalised** ⇒ `Customise` = **Yes** (e.g. `W101-SkyBe-O/S-Yes`, `M-T-NAVBE-3XL-Yes`). Still also `-P{digit}-`. Supervisor already set Customise Yes on `W101-SkyBe-O/S-Yes` and matching SKUs in live CL. `customise_for_label` / `--steps customise` updated for future adds.

### Fast add_labels — 4 Sep 2026

`scripts/add_labels.py`: same seed/fill rules as `fill_from_seeds`, but **does not rewrite** existing CL rows (append only). Default = named labels only; `--all-spc` for full BTC SPC series. Size References index cached as `support/Size References.index_cache.pkl` (rebuilds when the CSV changes). `fill_from_seeds` reuses one PE load for sizes (no double read).

### Named packing SKUs — 4 Sep 2026

Supervisor SKUs → Custom Label tails. **+136** rows (131,754 → **131,890**). `M281-P5-C800T-30-3>6` already existed (Print Positions blank → Front Center).

| Packing SKU | Custom Label | Action |
|---|---|---|
| `10428ALG-M260-P3-3265` | `M260-P3-3265` | New. Policy: all PE UIDs for SPC **61082** as `M260-P3-{UID}` → **134** rows, cloned from `M260-P5-{UID}` (FOTL Mens Original T). Front Center, Customise Yes. |
| `128967LG-W101-SkyBe-O/S-Yes` | `W101-SkyBe-O/S-Yes` | New. Sky Blue bag; peer `W101-ClaRd-O/S-Yes`. 320×350. **Customise Yes** (`Yes` token = personalised; supervisor corrected 4 Sep). |
| `11828ALG-M281-P5-C800T-30-3>6` | `M281-P5-C800T-30-3>6` | Already in CL. Filled blank Print Positions / Position 1 Name = Front Center. |
| `11434ALG-M281-P5-C800T-30-18-24` | `M281-P5-C800T-30-18-24` | New. White, 18-24 Months, 110×150. Cleared false Supplier SKU `24` (age token). |

Backups: `backups/Custom_Label_Database_before_named_skus_20260904_182959.csv`, `…_preFill_20260904_183057.csv`. `fill_from_seeds.py --iloc-from 131754`. Size References reverse fill skips `M260-P3-*` (hybrid P-token; `M260 (3265)` already present).

### Customise rule enforced — 28 Aug 2026 06:51

`-P{digit}-` in Custom Label ⇒ `Customise` = **Yes** (personalised; e.g. `M260-P5-*`, `N220-P3-*`). Plain mock+UID (`M55-{UID}`, `M56-{UID}`) ⇒ **blank** (not Yes). Fixed live CL: cleared **28,043** wrong `Yes`; set **2,063** missing `Yes` on `-P#-` rows. `fill_from_seeds.py` now has `--steps customise`. Backup: `backups/Custom_Label_Database_preFill_20260828_065100.csv`.

**Extended 4 Sep 2026:** a `Yes` segment in the label also ⇒ Customise Yes (bags/personalised SKUs). See note above.

### M55 full SPC 61082 — 28 Aug 2026 05:36

Preflight unmatched `422991LG-M55-120852` / `421612LG-M55-3257` — UIDs existed as **M56** only. Policy: **all PE UIDs for SPC**. Seeded **132** more `M55-{UID}` (130 net new + 2 earlier) → **134/134** for SPC `61082` Original T; cloned from `M56-{UID}` peers; Front Center; print sizes filled. `fill_size_references_from_cl.py` +**130** keys `M55 ({UID})`. CL 124,630→**124,762**; SR 97,073→**97,203**. Backups: `backups/Custom_Label_Database_before_m55_spc61082_20260828_053615.csv`, `…_preFill_20260828_053638.csv`, `support/backups/Size_References_preFill_20260828_053655.csv`.

### Size References ← N220 — 27 Aug 2026 15:02

Appended **7** keys `N220-P3-{UID}` (**80×45**, Front Print). Also wrongly added product-code `DIAMOND` (not a SKU) — removed in fallback write. Live `Size References.csv` was locked; clean file: `support/Size_References_write_fallback.csv` (97,072→**97,071**, no DIAMOND). Backup: `support/backups/Size_References_preN220_20260827_150252.csv`.

### Apparel Images ← recent adds — 27 Aug 2026 15:09

Downloaded **84** unique PE `colour image 01` files for `iloc[124138:]` (N220 + M56 + M260-P3 + F/P) into `Apparel Images/`. 0 failed. Fixed `download_apparel_images.py` PE encoding fallback (utf-8 → cp1252/latin-1).

### Size References ← M56 batch — 27 Aug 2026 14:59

`fill_size_references_from_cl.py` appended **320** keys (`M56 ({UID})`) from the midday CL seed. 96,744 → **97,064** rows. Backup: `support/backups/Size_References_preFill_20260827_145900.csv`.  
M260-P3 UIDs already had `M260 ({UID})` in SR (all 164). F/P compound not mock+UID — still not in SR.

### M56 + M260-P3 + F/P-F8 compound — 27 Aug 2026 11:55

Appended **485** rows (`iloc[124145:]`), then `fill_from_seeds` sku+pe+suppliers+image+print. Print Positions from `Mocks Databse.csv` (`M56`/`M260` = Front Print → **Front Center**). Seed Colour/Size/GA cloned from existing `M261-*` / `M260-*` peers for the same UID.

| Block | Count | Custom Label |
|--|--|--|
| Old compound token | 1 | `F/P-F8-M-T-BLK-5XL 161121LG-B4-M-T-BLK-5XL` (F/P = Front Center + Front Left Pocket; 357×504 + 80×100) |
| M56 SPC `61082` Original T | 134 | `M56-{UID}` |
| M56 SPC `61430` Iconic 150 | 186 (2 already existed) | `M56-{UID}` → **188/188** |
| M260-P3 SPC `61033` kids VW | 164 | `M260-P3-{UID}` |

Backups: `backups/Custom_Label_Database_before_m56_m260p3_fp_20260827_115521.csv`, `…_preFill_20260827_115540.csv`.

### N220 DIAMOND helmets — 27 Aug 2026 09:12

Appended all **7** PE UIDs for SPC `DIAMOND` (Delta Plus Hi-Vis Baseball Safety Helmet) as `N220-P3-{UID}`. Design-prefix SKUs (`189381LG-…`) stay out of Custom Label. Seeds: Front Center / Yes / Standard Size / 80×45. Filled sku+pe+suppliers+image on `iloc[124138:]`.

| | |
|--|--|
| Labels | `N220-P3-55708` … `55713`, `N220-P3-99823` |
| Colours | Blue, Green, Red, Orange, White, Yellow, Black |
| Backups | `backups/Custom_Label_Database_preN220Diamond_20260827_091234.csv`, `…_preFill_20260827_091247.csv` |

### Size References reverse fill — 25 Aug 2026 20:23

Filled `support/Size References.csv` from the catalog, mock+UID only (`M123-45678` → `M123 (45678)`). Appended missing keys; blank-only on existing millimetres; Gender / Size / Printing Position / Product Code / Printing Size filled where blank. Multi-design CL slots exploded to extra SR rows.

| | |
|--|--|
| Before → after | 22,727 → **96,744** rows |
| New keys / new rows | 59,608 / 74,017 (12,719 keys with 2+ designs) |
| Existing Gender fills | 8,542 |
| Existing Printing Position, Product Code, Printing Size | 188 each |
| Untouched non-mock rows | 133 (`A4`, `BG125`, …) |
| Backup | `support/backups/Size_References_preFill_20260825_202358.csv` |

25 Aug 20:44 dry-run against the same file: **0** new keys, **0** extra design rows, **0** blank-fills left. CL CSV was not written. M251-class beanies still have blank mm (catalog Width 1 blank).

### PE taxonomy fill — 24 Aug 2026 22:15

Blank-only from `BTC Product Export.csv` (118,230 UID matches). Existing Category/Sub-Category already matched PE (0 differed). Supplier Name / SPC unchanged.

| Column | Filled | Still blank (no PE UID) |
|--------|-------:|------------------------:|
| Department | 118,230 | 5,908 |
| Sub-Department | 118,230 | 5,908 |
| Brand | 118,230 | 5,908 |
| Category | 19 | 5,908 |
| Sub-Category | 19 | 5,908 |

---

## Locked fill rules (short)

| Topic | Rule |
|-------|------|
| Category / Department | PE `Department` (title case). Blank-only first; **overwrite** when PE Department is corrected |
| Sub-Category / Sub-Department | PE `Sub Department` (title case). Blank-only first; **overwrite** when PE Sub Department is corrected |
| Brand | PE `Brand` as-is, **blank only** |
| Apparel Image | **Blanks only** — never rewrite existing names |
| NocoDB | No column-name normalization; supervisor maps uploads |
| Duplicates | Leave in place unless asked to merge/delete |
| Shirts (tee/polo/hoodie/sweat/tank, or Size maps) | **Shirts Print Sizes** (A4) → then Size References |
| Not shirts | Size References only; **never** generic mock prefix |
| Width/Height | Blank cells only unless asked to correct mm |
| Supplier SKU | Last numeric UID on Custom Label |
| Dedicated BTC/Ralawise/Absolute cols | From **Supplier Name**, blank-only |
| Tags / Size (Dimensions) | Do not fill unless asked |

Shirt Size = DB `Size`, else PE `Size` via UID. Pocket 80×100 (kids F8 `-K-` = 65×80). Women use the men print band.

---

## Current leftovers (ask before acting)

1. **BTC dedicated cols** — 10 Sep 2026 cleared Package Type / Weight / Service that had been copied into BTC SKU / Product Code / Supplier Stock (38,697 rows; backup `Custom_Label_Database.bak_20260910_190412.csv`). After that: BTC SKU **35,600**, BTC Product Code **35,771**. Remaining blanks are historical — `fill_from_seeds.py --steps suppliers --dry-run`, then blanks only, still needs ask.
2. **Non-shirt Width 1 blanks** (~485 on 24 Aug): stickers, mugs, caps, bags, aprons, beanies, M251 / M290 / M307. Mock+UID keys are now in Size References; mm stay blank until the catalog (or an override) has Width/Height.
3. **`--all-mocks` image download** — ~189 unique remaining `M##` Apparel Image files. Does not change the CSV.
4. **`generate_from_mocks`** — ~293 guide IDs not in the DB. Pass current support CSV paths if script defaults still name old xlsx/guide files.
5. **`Tags` / `Size (Dimensions)`** — still blank; not filled from PE unless asked.
6. **24 Aug tail seed drift** (29 appended rows; duplicates kept): apostrophes in a few FOTL Gender Apparel values; `M281-P5-C800T-30-0>3` Size 3-6 Months vs 0-3; `K-H-DHR-YXS` Colour `Dark Heather` vs sibling `Dark Heather Grey`; 12/29 Print Positions blank.
7. **No PE UID** — ~5,908 rows stay blank on PE `Category` / `Department` / `Brand` (iron-ons, bags without trailing UID, etc.). Areeb on **every** CL row is warehouse `cl_standard` from Gender Apparel (Department = gender only; Product Style is not Brand). See `areeb-taxonomy.mdc`.
8. **PE Department / Sub Department corrections** — when the product worksheet is fixed, run `--overwrite-pe-taxonomy` (dry-run first) so Category, Sub-Category, Department, and Sub-Department match the new PE. Brand stays blank-only.

Shirt print sizes on the 24 Aug block are filled, including hoodie `M138-38262`, tank `77123-BTC`, and `K-H-DHR-YXS` → 176×250.

---

## Useful commands

```text
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
python scripts/fill_from_seeds.py --steps print --shirts-only --w1-blank
python scripts/fill_from_seeds.py --iloc-from 124109
python scripts/generate_from_mocks.py --dry-run
python scripts/db_export.py
python scripts/db_update.py
```

If the live CSV is locked: filler writes `Custom_Label_Database_write_fallback.csv`. Close the live file, then swap.

---

## Do not reopen as a project plan

Old dated approval/changelog files are in this folder. They refer to `Custom Label Database_Updated.xlsx` and numbered work packets. The living way of working is this file + `FINDINGS.md` + parent `.cursor/rules/custom-label-database/`.
