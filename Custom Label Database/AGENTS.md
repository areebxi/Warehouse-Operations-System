# Custom Label Database — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Supervisor = user. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/custom-label-database/`. Facts: `docs/FINDINGS.md`, `docs/HANDOFF.md`, `docs/WORKSPACE.md`.

**Save as you go** into this app’s docs (and parent CL rules when policy changes). Chat is not memory.

This app folder holds **scripts and docs**. Live catalog + helpers live under warehouse `database/` (see `docs/WORKSPACE.md`).

## Live work

- Edit **`database/shared/custom_label/Custom_Label_Database.csv`** only (via `shared.paths.cl_csv_path()`).
- Areeb 30-chain (`Category (Areeb)` / `Product Type (Areeb)` / `Product Style (Areeb)` / `Department (Areeb)`): warehouse `cl_standard` from Gender Apparel (`python scripts/fill_areeb_taxonomy.py --target cl` from warehouse root, or `fill_from_seeds.py --steps areeb`). Never BTC/Uneek. Department = gender only. Snap all four Areeb cells to Hashim #038 pick-list (Title Case; type has no gender; style is a product name, never a code). **Do not refill Plain / Packs Areeb** (supplier product data). Rule: parent `.cursor/rules/custom-label-database/areeb-taxonomy.mdc`.
- **Supply Method**: CL `Warehouse Stock` = FOTL men/women/kids t-shirts in the locked colour lists, plus Kids `C800T` / `C8030T` body colours (not `C8020T`). `In House Manufacture` = SKU or Gender Apparel contains iron on / ironon / iron-on / sticker. `Supplier On Demand` = everything else. `python scripts/fill_supply_method.py --target cl` from warehouse root, or `fill_from_seeds.py --steps supply`. Do not reuse `Warehouse Stock`. Rule: `supply-method.mdc`. Colour lists live in `shared/supply_method.py`.
- **Printing Type**: `DTF` default; `Sublimation` = mugs. `python scripts/fill_printing_type.py` from warehouse root, or `fill_from_seeds.py --steps printing_type`. Do not fill Design Type. Rule: `printing-type.mdc`.
- **Supplier Name**: `BTC Activewear` / `Uneek Clothing` / `Absolute Apparels`. Absolute = babysuits only (`C800T` / `C8020T` / `C8030T`). In-house iron-on/sticker stay blank. Filled 2026-09-09. `python scripts/fill_supplier_name.py` from warehouse root, or `fill_from_seeds.py --steps supplier_name`. Rule: `supplier-name.mdc`.
- **Customisation Type**: column exists; values empty; grouping split off in v1. Do not fill until a rule is locked.
- **BTC SKU / Product Code / Supplier Stock**: must be UID / SPC / stock — never Package Type, Weight, or Service. Leak cleared 2026-09-10 (`scripts/fix_cl_btc_leaked_shipping.py`).
- Helpers: `database/custom-label-database/support/`. **BTC Product Data**: `database/shared/btc_product_data/BTC_Product_Data.csv`. **Uneek Product Data**: `database/shared/uneek_product_data/Uneek_Product_Data.xlsx`. **Absolute Product Data**: `database/shared/absolute_product_data/Absolute_Product_Data.xlsx`.
- Run Python from this app folder. Prefer scripts over opening the full CSV in the editor.

## Approval

No production writes unless the supervisor already said **yes / do it / fill / run**. Propose, dry-run, then wait. Scope fills (`--iloc-from`, `--shirts-only`, `--w1-blank`) when only a slice changed.

Tackle **one problem at a time**.

**Unmatched packing SKUs (fast path):** `python scripts/add_labels.py --skus …` — named labels only, same fill rules, **append-only** (does not rewrite existing rows). Use `--all-spc` when you want every PE UID for that BTC SPC as `{mock}-{UID}` (catalog completeness; slower). Clone GA/Colour/Size/Image/Print Positions from a same-UID peer when possible; **Customise** = `Yes` when Custom Label has `-P{digit}-` **or** leading `P{digit}-` **or** a `Yes` token (e.g. `W101-SkyBe-O/S-Yes`). Then optional `fill_size_references_from_cl.py` for plain `M##-{UID}` keys.

**Database Transfer (locked 2026-09-25):** after every supervisor **fill** of CL and/or Size References, also run `python scripts/sync_database_transfer.py` so `Database Transfer/Workbook.xlsx` (CL Database sheet) and `Database Transfer/Configuration Workbook.xlsx` (Size References sheet) perfectly mirror the live CSVs. Rule: parent `.cursor/rules/custom-label-database/database-transfer-sync.mdc`.

## Hard do-nots

- Do not add or maintain **NocoDB column-name normalization**. Supervisor uploads and maps columns manually.
- **Apparel Image:** fill **blanks only**. Never rewrite an existing name.
- Do not auto-merge or delete **duplicate Custom Labels** unless asked.
- Do not fill **Tags / Size (Dimensions)** unless asked.
- Do not use a **generic mock prefix** in Size References (`M96` without this UID) for print millimetres.

PE taxonomy: `Category` and `Department` ← PE `Department`; `Sub-Category` and `Sub-Department` ← PE `Sub Department`; `Brand` ← PE `Brand` (blank-only). When the supervisor corrects PE Department / Sub Department, **overwrite** the four taxonomy columns on matching UIDs (`--overwrite-pe-taxonomy`).

## After any CSV change

Tell the supervisor exactly what changed: file, rows/labels, columns, before→after, count, backup path. On **fill**, also report the Database Transfer sync (row counts + backup paths).

## Structure & boundaries

- **Orchestration:** `scripts/` entry CLIs (`fill_from_seeds.py`, `add_labels.py`, `sync_database_transfer.py`, `db_update.py`).
- **Domain / shared fills:** `shared/areeb_taxonomy.py`, `supply_method.py`, `printing_type.py`, `supplier_name.py` (multi-app — do not fork in this folder). Seed fill helpers: `fill_seeds_*.py` beside `fill_from_seeds.py`.
- **I/O:** live paths only via `shared.paths`; helpers under `database/custom-label-database/`.
- **Split modules:** `size_code_logic.py` façade (`size_code_*.py`); `phase5_print_sizes.py` (`phase5_*.py`); `fill_size_references_from_cl.py` (`fill_sr_from_cl_*.py`); `fill_from_seeds.py` / `add_labels.py` (`fill_seeds_*` / `add_labels_*`).
- **Must not:** import other apps’ internals; resolve paths outside `shared.paths`; re-implement SKU match / finish gate / supply method / printing type.
- Policy detail: parent `.cursor/rules/custom-label-database/`. Architecture: `.cursor/rules/architecture.mdc`.
