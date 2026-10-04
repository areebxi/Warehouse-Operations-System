# Custom Label Database — current state

**Updated:** 4 October 2026  
**Handbook:** `AGENTS.md` · Parent: `../AGENTS.md` · **Facts:** `FINDINGS.md` · **Paths:** `WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/`  
**Dated fill log (archive):** [`archive/HANDOFF_FILL_LOG.md`](archive/HANDOFF_FILL_LOG.md)

## Live

| File | Role |
|------|------|
| `database/shared/custom_label/Custom_Label_Database.csv` | Live catalog |
| `database/custom-label-database/support/Size References.csv` | Size References (no SKU Value 2/3) |
| `database/custom-label-database/support/` | Shirts Print Sizes, Mocks, Workbook helpers |
| `Database Transfer/Workbook.xlsx` + `Configuration Workbook.xlsx` | Mirror after fill via `sync_database_transfer.py` (locked 2026-09-25) |

Last recorded after 4 Oct UNMATCHED fill (+5: `B-M-T-WHI-M-YES`, `P5-ACPPLQ-A515-PB`, `N01-P7-235932`, `W696-NAT-O/S-Yes`, `M407-P3-1D112`) + transfer sync: CL **132,610** rows; Size References **97,845**. `M407-P3-1D112` defaulted A5 15mm (buyer note said A4).

## How fills run

No live write without **yes / fill / run**. Propose + dry-run first. Typical path: `add_labels.py` / `fill_from_seeds.py` → `fill_size_references_from_cl.py` → **`sync_database_transfer.py`**. Fast add is append-only (`add_labels.py`). `add_labels` peers (locked with 2 Oct UNMATCHED fill): `N##` mocks; `-Yes` colour-family size peers; bag `ClaPk` → Classic Pink; alnum acrylic codes without PE peer → `A515-PHOTO`. Policy and column rules live in parent `.cursor/rules/custom-label-database/` — do not re-decide them here.

## Standing do-nots (reminders)

- Apparel Image: blanks only. Duplicates: leave unless asked. NocoDB: no column-name normalization.
- Do not put Packs/Plain SKUs into CL to “fix” unmatched.
- Chat is not memory; do not copy transcripts into `docs/chats/`.

## Current leftovers (ask before acting)

1. BTC dedicated cols — remaining blanks after 10 Sep Package Type leak cleanup; dry-run `--steps suppliers` then ask.
2. Non-shirt Width 1 blanks (~485 historically): stickers/mugs/caps/bags/aprons/beanies — mm until catalog/override has sizes.
3. `--all-mocks` image download (~189 `M##` files left) — does not change CSV.
4. `generate_from_mocks` — ~293 guide IDs not in DB.
5. `Tags` / `Size (Dimensions)` — blank unless asked.
6. No PE UID (~5,908) — PE Category/Department/Brand stay blank; Areeb still from Gender Apparel (`areeb-taxonomy.mdc`).
7. PE Department/Sub Department corrections — `--overwrite-pe-taxonomy` (dry-run first) when PE worksheet is fixed; Brand blank-only.
8. 24 Aug tail seed drift (29 rows) — known GA/colour/size quirks; see archive fill log.

## Useful commands

```text
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
python scripts/add_labels.py --skus …
python scripts/sync_database_transfer.py
```

If the live CSV is locked: filler writes `Custom_Label_Database_write_fallback.csv`. Close the live file, then swap.
