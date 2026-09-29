# Purchase Order Generator — snapshot

**Updated:** 17 September 2026 (later: packing lists move to Packing)  
**Handbook:** `AGENTS.md` · **Layout:** `FOLDER_LAYOUT.md`

## Continue here

- Launch: `Run_GUI.bat` (creates `.venv`, runs GUI).
- Data under `data/`; outputs under `output/`.
- Stock CL map: `Custom Label Database/Custom_Label_Database.csv` (`BTC SKU`).
- Sync DB from BTC Product Data / download images with scripts when asked (`--dry-run` first).

## Watch

- **Later (not built, 2026-09-17):** packing list PDFs (including slips this app prints) move to Order Packing List Generator. This app stays tag → stock / EDI.
- Former local `data/Custom Label Database.csv` is under `data/archive/`.
- FTP stock filename is configured in `config.py` only.
