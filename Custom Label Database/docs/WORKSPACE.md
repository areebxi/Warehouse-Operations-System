# Workspace layout

**App root** is this folder (`Custom Label Database/`), the parent of `scripts/`. Code and docs live here; **live database files** live under warehouse `database/`.

Resolve all paths via `shared/paths.py`.

```
Custom Label Database/          ← scripts + docs (this app)
database/
├── shared/
│   ├── custom_label/
│   │   ├── Custom_Label_Database.csv   ← LIVE catalog
│   │   └── backups/
│   └── product_export/ProductExport.csv
└── custom-label-database/
    ├── support/                  ← Size References, Shirts Print Sizes, Mocks, Workbook
    └── Apparel Images/
```

## Roles

| Path | Role |
|------|------|
| `database/shared/custom_label/Custom_Label_Database.csv` | Live database. Prefer CSV. |
| `database/custom-label-database/support/` | Helpers (Size References, Shirts Print Sizes, Mocks, Workbook). |
| `database/shared/custom_label/backups/` | Catalog snapshots. |
| `database/custom-label-database/Apparel Images/` | Apparel image library. |
| `scripts/` | Fillers, generators, NocoDB round-trip, image download. |

## Main commands (app root)

```text
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps print --shirts-only --w1-blank
python scripts/fill_from_seeds.py --iloc-from 124138
python scripts/generate_from_mocks.py --dry-run
python scripts/download_apparel_images.py --dry-run
python scripts/db_export.py
python scripts/db_update.py
```

`db_export.py` / `db_update.py` read/write the live CSV via `shared.paths.cl_csv_path()`.

## Path rules

- App root = parent of `scripts/`
- Helpers = `database/custom-label-database/support/` (`custom_label_support_dir()`)
- Catalog backups = `database/shared/custom_label/backups/` (`cl_backups_dir()`)
- Apparel images = `database/custom-label-database/Apparel Images/` (`images_apparel_dir()`)
- If the live CSV is open in Excel/Cursor, writes hit `PermissionError`. The filler then writes `Custom_Label_Database_write_fallback.csv`. Swap onto live after the file is closed; do not leave a second “live” CSV.
