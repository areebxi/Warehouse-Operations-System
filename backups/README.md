# backups/

One folder for snapshots, old code copies, and doc archives. Live catalogs stay under `database/`. Scripts write here via `shared/paths.py`.

| Folder | Was | Role |
|--------|-----|------|
| `custom-label/` | `database/shared/custom_label/backups/` | CL CSV snapshots (`cl_backups_dir()`) |
| `plain/` | `database/shared/plain/archive/` | Plain Database snapshots |
| `packs/` | `database/shared/packs/archive/` | Packs Database snapshots |
| `shared/` | `database/shared/archive/` | Former local copies some scripts still read (`data_archive_dir()`) |
| `size-references/` | `database/custom-label-database/support/backups/` | Size References snapshots |
| `database-transfer/` | `Database Transfer/backups/` | Transfer workbook snapshots |
| `versions/order-packing-list-generator/` | `Order Packing List Generator/Versions/` | Old packing app copies |
| `versions/production-design-queue-manager/` | `Production Design Queue Manager/Versions/` | Old queue app copies |
| `working-copies/` | `Working Copies/` | Frozen working copies of packing, PO, and queue |
| `docs/` | each app’s `docs/archive/` | Historical notes (tracked in git) |

Bulk files in this folder are gitignored. This README and `docs/` stay tracked.

Dated fill notes that still name the old paths (for example `database/shared/custom_label/backups/…`) describe where the file was written. The file is in the matching folder above.
