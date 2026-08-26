# Order Packing List Generator — handbook



Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/order-packing-list-generator/`. Details: `docs/`, `USAGE.md`, `README.md`.



App folder = **code only**. Live paths via `shared/paths.py`.



## Live vs helpers



| Live | Helpers / other |

|------|-----------------|

| `packing_list_app.py` + `scripts/` pipeline | `preflight_issues_app.py`, `missing_run_app.py` |

| `data/Packing/Workbook.xlsx` (CL Database sheet archive-only) | `data/Packing/New SKU Database.csv` |

| `Custom Label Database/Custom_Label_Database.csv` | Step 2 enrich |

| `data/shipstation/ShipStation_Tags.xlsx` | Shared tags |

| `runtime/Packing/Input|Output|…` | `config/Packing/` |
| `config/ShipStation/.env` | ShipStation credentials |
| `runtime/SharedInbox/DTF Des/{date}/{shift}/` | Dual-write DTF Des |



## How work is done



Eight-step pipeline: fetch ShipStation CSV → enrich from CL CSV → prime/images → position codes → process number → split by process → Excel (Picking, Orders Details, **DTF Des**) → packing PDFs. GUI or `pipeline_runner`.



SKU match: `shared/cl_sku_match.py` — whole → after-first-dash → till-last-dash on **Custom Label**.



DTF Des also lands in SharedInbox for Queue Missing Logo auto-run.



## Hard do-nots



- Do not invent Gender Apparel / CL matches for unmatched rows without approval.

- Do not revive Workbook `CL Database` as the live enrich source.

- Do not put live Excel/CSV back under this app folder.

- No pipeline write to live Output without **yes / do it / fill / run**.



## Report changes



Say what ran (inputs, date, shift), what was written under runtime Output and SharedInbox, unmatched counts, and any config touched. Log resolved bugs to `.cursor/issue-log.md`.

