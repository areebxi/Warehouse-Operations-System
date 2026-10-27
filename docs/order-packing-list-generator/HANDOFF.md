# Order Packing List Generator — snapshot

**Updated:** 27 October 2026 (CL enrich case-sensitive)  
**Handbook:** `AGENTS.md` · **Policy:** parent `.cursor/rules/order-packing-list-generator/`

## Continue here

- Live pipeline: `packing_list_app.py` or step scripts under `scripts/`.
- Missing logos are stripped **after Step 5, before Step 6 naming** so Process/Item numbers have no gaps. The missing-logo CSV is a holding file (no Item numbers). Logos ready → run it in the main packing app **from Step 1**.
- Enrich: Custom Label first (**case-sensitive** entire-cell via `shared/cl_sku_match`, locked 2026-10-27), then `database/shared/plain/Plain Database.csv` (till last dash or whole SKU), then Packs (whole `Channel Child SKU`). Blank Gender Apparel after those three is unmatched.
- **Make design queues** (GUI checkbox, default on): Step 7 writes DTF Des to Output. After Step 8 PDFs, Packing copies it to SharedInbox and waits on Queue `--files` for that file. With several inputs, the next packing run starts while the previous queue job runs (one queue job at a time). When off: Excel and PDFs only. Skip Batches (Queue Configuration Workbook) skip the SharedInbox copy; Queue still skips those PNGs.
- DTF Des: packing `Output/` always; SharedInbox only when Make design queues is on, after that file’s PDFs.
- Unmatched / preflight: helper apps at project root.
- Step 8 PDF: non-customise rows can take F/B/P/S(+S1/S2/SL/SR) side files from Normal Logo (sides-only grid). Customise can add a `{order}-LOCATION` image to the logo grid. Sleeve labels: S1/SL=Left, S2/SR=Right.
- Each input runs the full packing list (`phases="all"`), then the Design Queues handoff. `run_pdf_only_phase` must receive `lc=ctx["lc"]`.

## Pending / watch

- **Later (not built, 2026-09-17):** this app prints **every** packing list (including PO slips). Plain + Packs enrich is in place (2026-10-13). Do not put pack/plain SKUs in CL (`SET5722`).
- Operator config in `config/gui_config.json` may point at external Testing paths — not this folder’s Data/Output unless changed.
- Logo/Design Image is blank from CL CSV (no such column); personalised/order-number paths still apply downstream.
