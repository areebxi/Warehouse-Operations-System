# Findings — Order Grouping Sorter

## Mixed supply-method 2026-09-22

Warehouse Stock / In House / On Demand in one order is **not** unmatched. Whole order **Supplier On Demand** (on-demand item arrives later). Live example: `206-1401791-6245942` (FOTL t-shirt warehouse + jute bag on-demand). Code: `left_slots` in `scripts/grouping.py`.

## No-dash CL key 2026-09-22

If Item SKU has no dash, sorter matches **whole SKU** on Custom Label (`A515` → `A515`). Dashed SKUs stay after-first-dash only. Do not put packs/plain SKUs in CL.

## Blank ship-by 2026-09-17

Leave it. Do not invent a date, skip the unmatched gate, or fill catalog to paper over a missing `shipByDate`. ShipStation must have the date. 17 Sep run: 15 blank-ship-by orders stay `UNMATCHED`.

## Mixed customised 2026-09-17

Printed P vs R in one order is **not** unmatched. Whole order follows **majority printed units**; **tie → readymade**. Live example that run: `4176472144` (3 readymade + 1 customised). Code: `mixed_customised_slot` in `scripts/grouping.py`.

## Taxonomy pick-lists 2026-09-15 (Hashim #038)

Closed lists for category / subcategory / product type / product style in `database/order-grouping-sorter/taxonomy_picklists.csv`. New products pick from those rows. Subcategory is PE `Sub-Category` (not a 30-chain split). CL fill snaps Areeb category / type / style; unknown style stays blank. Do not dump Plain Brand / Uneek descriptions into product style.

## Shift / today mix 2026-09-15

**Hashim #037:** Shift 1 **order** volume above 300 → split process CSVs today vs later dates; ≤300 may mix. Do not dump overflow into Shift 2/3 (no 300/100/100 caps). Testing: every `--run` rewrites `1st Shift`. Production later: nth `--run` of the day = nth shift.

## Filename 2026-09-14

On-disk names are six fields (`S1-PRINTED-2-WAREHOUSE STOCK-P-1`). **Fixed batches** prefix `B{n}` before shift (`B100-S1-…` / `B100-S2-…`). Long Graph leftover names hit Windows MAX_PATH in Packing Output; this is the fix. 30-chain still peels leftover bins; those values are not in the filename. Priority (field 6, per shift): today first, then prime first, then as files are made. **Shift-first field order locked 2026-09-22**. **Cousin numbers retired 2026-09-23**. **Fixed batch `B` prefix + rename 2026-09-23**.

## Manual floor files (analysed 2026-09-12)

Supervisor added `Order Grouping Sorter/Manually Made Files/` (Jul–Sep). Only the shift-folder `*.csv` are ShipStation exports (full current-view, **no tags**). The rest (`*-Picking.xlsx`, `DTF Des-P*.xlsx`, rare PDF/JPG) are Packing List Generator output from those CSVs.

How the floor used to build a pile: ShipStation filter → export CSV → save as the process number in `{date}/{1st|2nd|3rd} Shift/`. Manual exports once used different numbers per shift (100 / 200 / 300). **Live sorter** uses **fixed batches** `B100` / `B80` / … — same code every shift; only `S{n}` changes (cousins retired; `B` prefix 2026-09-23). Date is the folder, not the filename.

Live grouping still uses the API (tags + store). Export `Custom - Field 2` was the old filter: `PER` ≈ personalised, `Prime Letter` / `Prime Parcel` ≈ Prime. Those fields are not a grouping source now.

| Batch | What the CSVs actually were |
|---|---|
| B80 | MAS Clothing FOTL short-sleeve readymade. |
| B90 | Fawad personalised FOTL (supervisor 2026-09-14). |
| B100 | Own-store FOTL short-sleeve readymade (men / women / kids together). |
| B1000 | Iron-on readymade (not sticker). Mostly Amazon `Prime Letter` — so iron-on does **not** split Prime. |
| B1080 | MAS Clothing iron-on readymade. |
| B4000 | FOTL short-sleeve, `Customise` / export PER. |
| B5000 | Iron-on personalised. |
| B5080 | MAS Clothing iron-on personalised. |
| B8000 | Amazon FOTL short-sleeve readymade Prime. |
| B8060 | Amazon FOTL short-sleeve personalised Prime. |

Other numbers seen historically in manual folders (not all live fixed batches): 10 Gildan cousin, 50/350 design-token FOTL (stays in **B100**), 70 mugs, old 2nd/3rd cousins 200/280/…, 1200, 3100 hoodies, 6000/7000/9200/9300 etc. **Now live:** `B40` Gildan T-Shirts, `B1050` SKU contains STICKER, `B3700` Sweatshirts (2026-09-24).

## Run 2026-09-14 09:14 (`Logs/run_20260914_091438.txt`)

Supervisor **run**. Fetch=82. **17 CSVs** into `Input/14-09-2026/1st Shift/`. 1st used 64 of 300 (2nd/3rd empty). Named files this run: `90` (1), `100` (13), `1000` (1), `4000` (9), `5080` (4), `8000` (3). Leftover Graph names: Uneek plain, Fawad in-house readymade (stickers, not iron-on), Absolute/BTC on-demand.

Unmatched 14: blank ship-by 7; no catalog match 7 (`1636ALG-M263-P5-DTF-IronOn-A4`, `922ALG-M260-P2-17259`, `189364LG-N217-P3-1D77`, `110419LG-F4-M-T-NVY-M-Yes`, `802058LG-STICKERS-M(30cmx30cm)`, `47BLG-P5-ACPPLQ-A625-PB`, `50BLG-P5-ACPPLQ-A415-PB`).

## Dry-run 2026-09-11 (`Logs/dry-run_20260911_084147.txt`)

Read-only. **Input was not written.** Catalogs: CL unique Custom Label keys **128,688** (live file 131,892 rows; first row wins on duplicate labels), Plain **78,039**, Packs **38,452**.

ShipStation `awaiting_shipment` `total=98`–`100` this morning (pages=1; not a 100-row page cap). 1 skipped `post-order-designs`, 1 discount-only/empty.

| Bucket | Orders | Lines | Units |
|--------|-------:|------:|------:|
| resend | 0 | 0 | 0 |
| unmatched | 23 | 46 | 61 |
| held-after-caps | 0 | 0 | 0 |
| 1st Shift (cap 300) | 75 | 78 | 80 |
| 2nd / 3rd | 0 | 0 | 0 |

2nd/3rd empty is correct: 1st still had cap left, so leftover future filled **1st**, not 2nd.

Unmatched reasons:

| Reason | Orders |
|--------|-------:|
| blank ship-by | 11 |
| mixed size | 7 |
| no catalog match | 2 |
| mixed customised | 1 |
| mixed department | 1 |
| blank colour | 1 |

Mixed size / department / customised are flag-`1` whole-order unmatched (locked). Blank ship-by is locked unmatched.

Name samples (flag `x`/`0` slots present; 30-chain only when it peels):

- `today-1st-printed-fawad-x-non-prime-dtf-customised-x-x-x-warehouse_stock-x-x-kids-x-7-8_years`
- `today-1st-printed-own-x-prime-dtf-customised-x-x-x-warehouse_stock-x-x-t-shirts-t-shirt-mens-x-large`
- `2026-09-14-1st-plain-own-x-non-prime-x-x-x-x-x-supplier_on_demand-uneek_clothing-x`

## Dry-run 2026-09-11 08:51 (`Logs/dry-run_20260911_085101.txt`) — inside-file `-N`

v1 names already accepted. Pool had moved (62 fetched). Input not written. `-N`: colour 3+ first, then 50-unit parts.

Colour 3+ on a live process (same filename, two `-N`):

- `…-t-shirts-mens-x-small` — 5 units → `-1` (3) + `-2` (2)
- `…-prime-…-mens-x-medium` — 4 units → `-1` (3) + `-2` (1)

No 50-unit part split this run (1st Shift 44 lines). Unmatched is still one file, with `-1`/`-2`/`-3` inside it.

## Dry-run 2026-09-11 11:09 (`Logs/dry-run_20260911_110932.txt`)

Live `awaiting_shipment` fetch. **Input was not written.** Catalogs unchanged (CL 128,688 / Plain 78,039 / Packs 38,452).

| Bucket | Orders | Lines | Units |
|--------|-------:|------:|------:|
| fetched | 85 | — | — |
| skipped post-order-designs | 3 | — | — |
| empty/discount-only | 1 | — | — |
| resend | 1 | 1 | 2 |
| unmatched | 23 | 34 | 40 |
| held-after-caps | 0 | 0 | 0 |
| 1st Shift (cap 300) | 57 | 59 | 60 |
| 2nd / 3rd | 0 | 0 | 0 |

2nd/3rd empty is still correct: 1st used 59 of 300.

Unmatched reasons: blank ship-by 11, mixed size 5, no catalog match 4, mixed department 2, blank colour 1.

Colour 3+ this run: `today-1st-printed-own-x-prime-dtf-readymade-…-mens-x-medium` — 5 units → `-1` (3) + `-2` (2). No 50-unit part split (1st still 59 lines).

## Run 2026-09-11 11:23 (`Logs/run_20260911_112348.txt`) — Packing Input written

Supervisor **run**. Live `awaiting_shipment` fetch=91. **46 CSVs** written to `Order Packing List Generator/Input/11-09-2026/`. Catalogs read-only.

| Bucket | Orders | Lines | Units | Files |
|--------|-------:|------:|------:|------:|
| skipped post-order-designs | 2 | — | — | — |
| empty/discount-only | 1 | — | — | — |
| resend | 1 | 1 | 2 | `1st Shift/resend.csv` |
| unmatched | 23 | 34 | 40 | `1st Shift/unmatched.csv` |
| 1st Shift processes (cap 300, used 67) | 64 | 67 | 68 | 44 process CSVs |
| 2nd / 3rd | 0 | 0 | 0 | folders created, empty |
| held-after-caps | 0 | 0 | 0 | not written |

Unmatched reasons unchanged: blank ship-by 11, mixed size 5, no catalog match 4, mixed department 2, blank colour 1.

Colour 3+ still on `today-1st-printed-own-x-prime-dtf-readymade-…-mens-x-medium` (5 lines / 3 orders in one CSV).

## Run 2026-09-11 14:13 (`Logs/run_20260911_141351.txt`) — Graph 30-chain

Supervisor **run** after printed department/size/brand moved onto the sequential ≥30 chain. Old always-split CSVs in `Input/11-09-2026/` were replaced. **19 CSVs** (17 process + resend + unmatched). Names stop at left-side slots (no `mens` / `kids` / size) because no 30-chain pile reached 30.

| Bucket | Orders | Lines | Units |
|--------|-------:|------:|------:|
| fetched | 61 | — | — |
| skipped post-order-designs | 4 | — | — |
| empty/discount-only | 1 | — | — |
| resend | 2 | 2 | 2 |
| unmatched | 16 | 16 | 17 |
| 1st Shift (cap 300, used 38) | 38 | 38 | 40 |
| 2nd / 3rd | 0 | 0 | 0 |

Unmatched: blank ship-by 10, no catalog match 3, **blank brand 3** (printed brand is now on the 30-chain, so blank Brand unmatched). Mixed size / mixed department are gone (under 30 they stay in the parent file).

Example pile: `today-1st-printed-own-x-non-prime-dtf-readymade-…-warehouse_stock-x-x` — 6 units, colour 3+ inside-file `-1` / `-2`, no department/size in the filename.

## Run 2026-09-11 14:25 (`Logs/run_20260911_142545.txt`) — today/future binary

Supervisor **run**. Same pool (61 fetched). **14 CSVs** after merging all future dates into `future-…` (was 19 when each ISO date was its own file). Date-named CSVs (`2026-09-12-…` etc.) removed.

1st Shift used 38 of 300: **12 process files** (5 `today-` + 7 `future-`) + resend + unmatched. Unmatched unchanged (blank ship-by 10, no catalog match 3, blank brand 3).

## Dry-run 2026-09-11 14:45 (`Logs/dry-run_20260911_144516.txt`) — flag-30 blank stays in parent

**Input was not written.** Pool 64 fetched (was 61). Flag-30 blank Brand/Colour no longer unmatcheds.

| Bucket | Orders | Lines | Units |
|--------|-------:|------:|------:|
| unmatched | 13 | 13 | 13 |
| 1st Shift (cap 300, used 45) | 45 | 45 | 50 |

Unmatched: **blank ship-by 10**, **no catalog match 3**. Blank brand gone.

Recovered in-house into process files:

- `future-…-dtf-customised-…-in_house_manufacture-x-x` — IronOn-A4-YES
- `future-…-dtf-readymade-…-in_house_manufacture-x-x` — IronOn-A4 + STICKER-A4

Still unmatched (have ship-by, missing CL row):

- `11828ALG-M281-P5-C800T-30-6>12` — cousin `M281-P5-C800T-30-3>6` exists; this size is not in CL
- `10182ALG-M281-C800T-30-3>6` — listing omitted `-P5-` vs catalog `M281-P5-C800T-30-3>6`
- `32BLG-P5-ACPPLQ-A410-PB` — acrylic plaque; not in CL (closest `A515-PHOTO`)

Blank ship-by stays unmatched (locked). Several of those 10 would group if ShipStation had a date.

## Catalog fill 2026-09-11 14:53 — three missing CL rows

Supervisor **fill**. Appended the three no-catalog labels (131,892 → 131,895). Backup `Custom_Label_Database_preAdd_20260911_145305.csv`. Packing Input **not** rewritten — wait for **run**.

## Run 2026-09-11 16:03 (`Logs/run_20260911_160325.txt`) — after CL fill

Supervisor **run**. Pool had moved (36 fetched). **16 CSVs** written. Unmatched is **blank ship-by 10 only** (no catalog-match / blank-brand left). The three filled labels grouped (Absolute babysuits + acrylic). In-house iron-on/sticker still on `in_house_manufacture` files.

`unmatched.csv` was open/locked. Live unmatched is `1st Shift/unmatched_write_fallback.csv`. Stale `unmatched.csv` is the previous 16-order file — do not pack from it.

Supervisor closed the lock 2026-09-11 16:11. Fallback copied onto `unmatched.csv`; `unmatched_write_fallback.csv` removed.

## Run 2026-09-12 05:25 (`Logs/run_20260912_052530.txt`)

Live `awaiting_shipment` fetch=185. **24 CSVs** into `Input/12-09-2026/1st Shift/`. 1st used 180 of 300 (2nd/3rd empty). 30-chain peeled this run: warehouse-stock FOTL t-shirts hit ≥30 (`…-t-shirts-…-fruit_of_the_loom`, 48 orders).

| Bucket | Orders | Lines | Units |
|--------|-------:|------:|------:|
| skipped post-order-designs | 3 | — | — |
| empty/discount-only | 1 | — | — |
| resend | 1 | 1 | 1 |
| unmatched | 14 | 14 | 14 |
| 1st Shift | 166 | 180 | 190 |

Unmatched: blank ship-by 13, no catalog match 1 (`110419LG-F4-M-T-NVY-M-Yes` → after-first `F4-M-T-NVY-M-Yes`).
