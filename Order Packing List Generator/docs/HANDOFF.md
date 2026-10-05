# Order Packing List Generator — snapshot

**Updated:** 5 October 2026 (batch PDF phase: pass `lc` into `run_pdf_only_phase` so PDF copy after Step 8 does not NameError)  
**Handbook:** `AGENTS.md` · **Policy:** parent `.cursor/rules/order-packing-list-generator/`

## Continue here

- Live pipeline: `packing_list_app.py` or step scripts under `scripts/`.
- Missing logos are stripped **after Step 5, before Step 6 naming** so Process/Item numbers have no gaps. The missing-logo CSV is a holding file (no Item numbers). Logos ready → run it in the main packing app **from Step 1**.
- Enrich: `Custom Label Database/Custom_Label_Database.csv` (Workbook process sheets still used; CL Database sheet archive-only).
- DTF Des: packing `Output/` **and** `SharedInbox/DTF Des/{date}/{shift}/`.
- Unmatched / preflight: helper apps at project root.
- Step 8 PDF: non-customise rows can take F/B/P/S(+S1/S2/SL/SR) side files from Normal Logo (sides-only grid). Customise can add a `{order}-LOCATION` image to the logo grid. Sleeve labels: S1/SL=Left, S2/SR=Right.
- Batch Excel-then-PDF: `run_pdf_only_phase` must receive `lc=ctx["lc"]` (detail logger) when copying PDFs to the optional PDF copy directory after Step 8.

## Pending / watch

- **Later (not built, 2026-09-17):** this app prints **every** packing list (including PO slips). Enrich/preflight also Plain + Packs. Do not put pack/plain SKUs in CL (`SET5722`).
- Operator config in `config/gui_config.json` may point at external Testing paths — not this folder’s Data/Output unless changed.
- Logo/Design Image is blank from CL CSV (no such column); personalised/order-number paths still apply downstream.
