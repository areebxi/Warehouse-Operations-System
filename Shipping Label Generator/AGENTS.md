# Shipping Label Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/shipping-label-generator/`. Behavior source: `docs/REQUIREMENTS.md`. Snapshot: `docs/HANDOFF.md`.

## Live vs helpers

| Live | Other |
|------|--------|
| `python -m scripts.app.main` (convert / print / void) | `bat_files/`, `tests/` |
| `DTF Des Files/` | `DTF Des Files - Processed/` |
| `shipping_config.yaml`, `.env` | `docs/archive/` (old PLAN / build logs) |
| `output/` labels + process/combined PDFs | |

## How work is done

1. **Convert** — DTF Des Excel/CSV in `DTF Des Files/` → canonical orders list (needs `Order - Number`, `Process Num`).  
2. **Print** — ShipStation create/reuse labels; per-process + combined PDFs.  
3. **Void** — from void list CSV.

Inputs match packing DTF Des shape; drop files here manually.

## Hard do-nots

- Never hardcode or paste API secrets.
- Do not read Orders Details as the primary input.
- No print/void against live ShipStation without **yes / do it / fill / run**.

## Report changes

Report convert counts, process groups, label successes/failures, void results, and artifact paths. Redact secrets.
