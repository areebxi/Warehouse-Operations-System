# Shipping Label Generator — handbook



Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/shipping-label-generator/`. Behavior source: `docs/REQUIREMENTS.md`. Snapshot: `docs/HANDOFF.md`.



App folder = **code only**. Live paths via `shared/paths.py` / `load_config`.



## Live vs helpers



| Live | Other |

|------|--------|

| `python -m scripts.app.main` (convert / print / void) | `bat_files/`, `tests/` |

| `runtime/Shipping/DTF Des Files/` | `…/DTF Des Files - Processed/` |

| `config/Shipping/shipping_config.yaml` | Tuneables |
| `config/ShipStation/.env` | ShipStation secrets |
| `runtime/Shipping/Output/` | |



## How work is done



1. **Convert** — DTF Des in runtime Shipping desfiles → canonical orders list.  

2. **Print** — ShipStation create/reuse labels; per-process + combined PDFs.  

3. **Void** — from void list CSV.



## Hard do-nots



- Never hardcode or paste API secrets.

- Do not read Orders Details as the primary input.

- No print/void against live ShipStation without **yes / do it / fill / run**.



## Report changes



Report convert counts, process groups, label successes/failures, void results, and artifact paths. Redact secrets.

