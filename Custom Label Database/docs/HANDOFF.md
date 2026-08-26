# Custom Label Database — Agent snapshot

**Updated:** 25 August 2026 (Size References reverse fill)  
**Standing brief:** `AGENTS.md` (handbook) · Parent map: `../AGENTS.md`  
**Facts:** `docs/FINDINGS.md` · **Paths:** `docs/WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/` · **Chat copies:** `docs/chats/`

Prior long chats: [Custom Label DB cleanup](4455a0cd-185b-4d3e-86d5-b1c620841dd4), [shirt print sizes](59e96d0f-08d7-4ced-bb91-67d9556b29ca).

---

## Role

Warehouse Automation System Engineer on this catalog domain; user is supervisor. No production writes without **yes / do it / fill / run**. One problem at a time. Prefer CSV. **Save everything as we go** (parent CL rules + docs + `AGENTS.md`) — chat is not memory.

---

## Live now

Live catalog: `../Custom Label Database/Custom_Label_Database.csv` — **124,138** rows × **60** cols.  
Helpers: `../support/` (`Size References.csv`, `Shirts Print Sizes.csv`, `Mocks Databse.csv`).

Main filler: `python scripts/fill_from_seeds.py`. Size References reverse fill: `python scripts/fill_size_references_from_cl.py --dry-run`.

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

1. **BTC dedicated cols** — `fill_from_seeds.py --steps suppliers --dry-run`, then blanks only. Largest remaining fill (~83k BTC SKU / BTC Product Code on 24 Aug).
2. **Non-shirt Width 1 blanks** (~485 on 24 Aug): stickers, mugs, caps, bags, aprons, beanies, M251 / M290 / M307. Mock+UID keys are now in Size References; mm stay blank until the catalog (or an override) has Width/Height.
3. **`--all-mocks` image download** — ~189 unique remaining `M##` Apparel Image files. Does not change the CSV.
4. **`generate_from_mocks`** — ~293 guide IDs not in the DB. Pass current support CSV paths if script defaults still name old xlsx/guide files.
5. **`Tags` / `Size (Dimensions)`** — still blank; not filled from PE unless asked.
6. **24 Aug tail seed drift** (29 appended rows; duplicates kept): apostrophes in a few FOTL Gender Apparel values; `M281-P5-C800T-30-0>3` Size 3-6 Months vs 0-3; `K-H-DHR-YXS` Colour `Dark Heather` vs sibling `Dark Heather Grey`; 12/29 Print Positions blank.
7. **No PE UID** — 5,908 rows stay blank on Category / Department / Brand (iron-ons, bags without trailing UID, etc.).
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

Old dated approval/changelog files are in `docs/archive/`. They refer to `Custom Label Database_Updated.xlsx` and numbered work packets. The living way of working is this file + `FINDINGS.md` + parent `.cursor/rules/custom-label-database/`.
