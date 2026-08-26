# Custom Label Database — handbook



Domain handbook for the **Warehouse Automation System Engineer**. Supervisor = user. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/custom-label-database/`. Facts: `docs/FINDINGS.md`, `docs/HANDOFF.md`, `docs/WORKSPACE.md`.



**Save as you go** into this app’s docs (and parent CL rules when policy changes). Chat is not memory.



App folder owns the live `Custom_Label_Database.csv` (+ `backups/`), `support/` helpers, and `Apparel Images/`. PE under warehouse `data/product_export/`.



## Live work



- Edit **`Custom Label Database/Custom_Label_Database.csv`** only (via `shared.paths.cl_csv_path()`).

- Helpers under `support/`. PE: `data/product_export/ProductExport.csv`. Backups: `Custom Label Database/backups/`.

- Run Python from this app folder. Prefer scripts over opening the full CSV in the editor.



## Approval



No production writes unless the supervisor already said **yes / do it / fill / run**. Propose, dry-run, then wait. Scope fills (`--iloc-from`, `--shirts-only`, `--w1-blank`) when only a slice changed.



Tackle **one problem at a time**.



## Hard do-nots



- Do not add or maintain **NocoDB column-name normalization**. Supervisor uploads and maps columns manually.

- **Apparel Image:** fill **blanks only**. Never rewrite an existing name.

- Do not auto-merge or delete **duplicate Custom Labels** unless asked.

- Do not fill **Tags / Size (Dimensions)** unless asked.

- Do not use a **generic mock prefix** in Size References (`M96` without this UID) for print millimetres.



PE taxonomy: `Category` and `Department` ← PE `Department`; `Sub-Category` and `Sub-Department` ← PE `Sub Department`; `Brand` ← PE `Brand` (blank-only). When the supervisor corrects PE Department / Sub Department, **overwrite** the four taxonomy columns on matching UIDs (`--overwrite-pe-taxonomy`).



## After any CSV change



Tell the supervisor exactly what changed: file, rows/labels, columns, before→after, count, backup path.

