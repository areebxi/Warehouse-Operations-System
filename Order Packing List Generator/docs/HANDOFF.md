# Order Packing List Generator — snapshot

**Updated:** 25 August 2026 (CL CSV + SharedInbox)  
**Handbook:** `AGENTS.md` · **Policy:** parent `.cursor/rules/order-packing-list-generator/`

## Continue here

- Live pipeline: `packing_list_app.py` or step scripts under `scripts/`.
- Enrich: `Custom Label Database/Custom_Label_Database.csv` (Workbook process sheets still used; CL Database sheet archive-only).
- DTF Des: packing `Output/` **and** `SharedInbox/DTF Des/{date}/{shift}/`.
- Unmatched / preflight: helper apps at project root.

## Pending / watch

- Operator config in `config/gui_config.json` may point at external Testing paths — not this folder’s Data/Output unless changed.
- Logo/Design Image is blank from CL CSV (no such column); personalised/order-number paths still apply downstream.
