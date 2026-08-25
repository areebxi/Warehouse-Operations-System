# Workspace layout

**App root** is this folder (`Custom Label Database/`), the parent of `scripts/`. That is true whether Cursor opened this folder alone or opened `Warehouse Operations System` (this path nested underneath).

Two copies of this tree have existed (`D:\Custom Label Database` and `D:\Warehouse Operations System\Custom Label Database`). Treat them as the same project until the supervisor says otherwise.

**Policy rules** for this app live only at the warehouse parent: `../.cursor/rules/custom-label-database/` (when the parent folder is the Cursor window).

```
Custom Label Database/
├── AGENTS.md                     ← domain handbook
├── Custom_Label_Database.csv     ← LIVE working DB (edit this)
├── Custom Label Database.xlsx    ← archive / Excel copy (not live)
├── backups/                      ← timestamped copies before fills / restores
├── docs/                         ← living docs (this folder)
│   └── archive/                  ← old dated execution logs
├── scripts/                      ← Python tools (run from app root)
├── Custom Label Database Maker/  ← expander + image download
│   └── Apparel Images/           ← PE colour image 01 saved as exact Apparel Image names
└── support/                      ← helpers only (do not treat as live DB)
    ├── Shirts Print Sizes.csv    ← garment size-band W/H (Standard A4 / A3 / Neck)
    ├── Size References.csv       ← bags / paper / iron-on / exact mock+UID / templates
    ├── BTC Product Export.csv    ← product catalog (join on UID)
    ├── Mocks Databse.csv         ← mocks guide (filename spelling is real)
    ├── Old Custom Label Database.csv
    ├── M01 Print Config.xlsx
    └── Workbook.xlsx             ← Picture Name used for Apparel Image restore
```

## Roles

| Path | Role |
|------|------|
| `Custom_Label_Database.csv` | Live database. Prefer CSV; supervisor converts to xlsx when needed. |
| `Custom Label Database.xlsx` | Older Excel archive — never the edit target. |
| `support/` | Reference tables. Read-only during fills. Prefer the `.csv` names above. |
| `backups/` | Pre-change snapshots. Not under `support/`. |
| `scripts/` | Fillers, generators, NocoDB round-trip. One-off historical cleanups still named `phase*.py`. |
| `Custom Label Database Maker/` | Original expander (`fill_cl_database.py`) and `download_apparel_images.py`. |

## Main commands (app root)

```text
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps print --shirts-only --w1-blank
python scripts/fill_from_seeds.py --iloc-from 124109
python scripts/generate_from_mocks.py --dry-run
python scripts/db_export.py
python scripts/db_update.py
```

`db_export.py` / `db_update.py` read/write `Custom_Label_Database.csv` in the current working directory.

## Path rules

- App root = parent of `scripts/`
- Helpers = `support/…`
- Backups = `backups/…`
- If the live CSV is open in Excel/Cursor, writes hit `PermissionError`. The filler then writes `Custom_Label_Database_write_fallback.csv`. Swap onto live after the file is closed; do not leave a second “live” CSV.
