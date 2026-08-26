# Workspace layout

**App root** is this folder (`Custom Label Database/`), the parent of `scripts/`. That is true whether Cursor opened this folder alone or opened `Warehouse Operations System` (this path nested underneath).

Live catalog, `support/` helpers, and `Apparel Images/` live in this app. Product Export stays under warehouse `data/product_export/`. Resolve via `shared/paths.py`.

Two copies of this tree have existed (`D:\Custom Label Database` and `D:\Warehouse Operations System\Custom Label Database`). Treat them as the same project until the supervisor says otherwise.

**Policy rules** for this app live only at the warehouse parent: `../.cursor/rules/custom-label-database/` (when the parent folder is the Cursor window).

```
Custom Label Database/
├── Custom_Label_Database.csv     ← LIVE catalog
├── backups/                      ← catalog snapshots
├── Apparel Images/               ← apparel image library
├── support/
│   ├── Size References.csv
│   ├── Shirts Print Sizes.csv
│   ├── Mocks Databse.csv         ← filename spelling is real
│   ├── Workbook.xlsx             ← apparel restore source
│   └── backups/                  ← Size References snapshots
└── scripts/
    ├── fill_from_seeds.py
    ├── generate_from_mocks.py
    ├── download_apparel_images.py
    └── fill_cl_database.py       ← legacy PE→template expand
data/product_export/ProductExport.csv
```

## Roles

| Path | Role |
|------|------|
| `Custom_Label_Database.csv` | Live database. Prefer CSV. |
| `support/` | Helpers (Size References, Shirts Print Sizes, Mocks, Workbook). |
| `support/backups/` | Size References snapshots. |
| `backups/` | Catalog snapshots. |
| `Apparel Images/` | Apparel image library. |
| `scripts/` | Fillers, generators, NocoDB round-trip, image download. |

## Main commands (app root)

```text
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps print --shirts-only --w1-blank
python scripts/fill_from_seeds.py --iloc-from 124109
python scripts/generate_from_mocks.py --dry-run
python scripts/download_apparel_images.py --dry-run
python scripts/db_export.py
python scripts/db_update.py
```

`db_export.py` / `db_update.py` read/write `Custom_Label_Database.csv` via `shared.paths.cl_csv_path()`.

## Path rules

- App root = parent of `scripts/`
- Helpers = `support/`
- Catalog backups = `backups/`
- Size References backups = `support/backups/`
- Apparel images = `Apparel Images/`
- If the live CSV is open in Excel/Cursor, writes hit `PermissionError`. The filler then writes `Custom_Label_Database_write_fallback.csv`. Swap onto live after the file is closed; do not leave a second “live” CSV.
