# Warehouse docs

Living documentation lives here. App handbooks stay in each app’s `AGENTS.md`. Policy stays in `.cursor/rules/`. Archives stay in `backups/docs/`.

## Cross-app

| File | What it is |
|------|------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Pipeline, ownership, boundaries |
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | Built vs not-built snapshot |
| [`DECISIONS.md`](DECISIONS.md) | Decision owner map |

## Per app

| Slug folder | App folder | Key files |
|-------------|------------|-----------|
| [`custom-label-database/`](custom-label-database/) | `Custom Label Database/` | HANDOFF, FINDINGS, WORKSPACE |
| [`order-grouping-sorter/`](order-grouping-sorter/) | `Order Grouping Sorter/` | HANDOFF, FINDINGS |
| [`order-packing-list-generator/`](order-packing-list-generator/) | `Order Packing List Generator/` | HANDOFF, FINDINGS, `scripts/` |
| [`production-design-queue-manager/`](production-design-queue-manager/) | `Production Design Queue Manager/` | HANDOFF, FINDINGS, DOCUMENTATION |
| [`shipping-label-generator/`](shipping-label-generator/) | `Shipping Label Generator/` | HANDOFF, FINDINGS, REQUIREMENTS |
| [`purchase-order-generator/`](purchase-order-generator/) | `Purchase Order Generator/` | HANDOFF, FINDINGS |

Session start for an app: that app’s `AGENTS.md` + `docs/<slug>/HANDOFF.md` + matching `.cursor/rules/<slug>/`.
