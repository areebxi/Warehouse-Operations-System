# Shipping Label Generator — handbook



Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/shipping-label-generator/`. Behavior source: `../docs/shipping-label-generator/REQUIREMENTS.md`. Snapshot: `../docs/shipping-label-generator/HANDOFF.md`.
Current state: `../docs/shipping-label-generator/HANDOFF.md`, kept as present-tense state, not a log.

Live paths via `shared/paths.py` / `load_config` (desfiles + yaml in this app; Output/Logs under warehouse-root; ShipStation secrets shared).



## Live vs helpers



| Live | Other |

|------|--------|

| `python -m scripts.app.main` (convert / print / sample-print / void) | `bat_files/`, `tests/` |

| `DTF Des Files/` | `DTF Des Files - Processed/` |

| `config/shipping_config.yaml` | Tuneables |

| `database/shipping-label-generator/Configuration Workbook.xlsx` | Label Page Threshold (A2) |

| `config/ShipStation/.env` | Only ShipStation secrets file (warehouse-wide) |

| `Output/Shipping Label Generator/` | Labels, batch PDFs, Reports |

| `Logs/Shipping Label Generator/` | Run logs + Error and Failures |



## How work is done



1. **Convert** — DTF Des in app desfiles → canonical orders list. A file already in the processed manifest is converted again.

2. **Print** — ShipStation create/reuse labels; per-process + combined PDFs. A shipped order reprints the PDF already under `Output/Shipping Label Generator/Labels` and does not buy a second label. The first page of each DTF file is a Batch Summary.

3. **Void** — from void list CSV.

Reprint lock (2026-10-20): `.cursor/rules/shipping-label-generator/reprint.mdc`.



## Hard do-nots



- Never hardcode or paste API secrets.

- Do not read Orders Details as the primary input.

- No print/void against live ShipStation without **yes / do it / fill / run**.



## Report changes



Report convert counts, process groups, label successes/failures, void results, and artifact paths. Redact secrets.



## Structure & boundaries

- **Orchestration:** `scripts/app/main` and `scripts/app/flows/` (convert / print / void / report). Previous working copy restored 8 Oct 2026; print, convert, and label-report modules are the pre-split versions.
- **Integrations:** `scripts/app/providers/` (`RealProvider` creates and voids labels).
- **Generation:** `scripts/app/pdf/`.
- **I/O:** `DTF Des Files/`, `config/shipping_config.yaml`; Label Page Threshold via `database/shipping-label-generator/Configuration Workbook.xlsx`; secrets via `config/ShipStation/.env` only.
- **200-line:** several restored flow modules are over 200 lines. New edits still follow `../docs/ARCHITECTURE.md`.
- **Must not:** import Packing/Queue/Sorter internals; hardcode secrets; auto-read SharedInbox until built.
- Architecture: `.cursor/rules/global/architecture.mdc`.

