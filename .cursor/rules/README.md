# Project rules (`.cursor/rules/`)

Cursor auto-loads project rules **only** from this folder. That is the single home for warehouse agent policy.

## Two tiers

| Tier | Path | Use for |
|------|------|---------|
| Global | `global/` | Always-on or cross-app shared |
| App | `<app-slug>/` | That app’s policy only (`alwaysApply: false` + globs for the app folder) |

Do not nest rules under `AppName/.cursor/rules/`. Do not invent a parallel root `rules/`. How to write rules: [`global/rule-writing.mdc`](global/rule-writing.mdc).

## `global/` (always-on / shared)

| File | Purpose |
|------|---------|
| `rule-writing.mdc` | Where rules live; write so any LLM can follow |
| `warehouse-system-map.mdc` | Always-on router — one engineer; do not mix apps |
| `architecture.mdc` | 200-line limit, layers, shared vs app, boundaries |
| `session-independence.mdc` | Repo is memory; two-axis truth; verify; persist |
| `docs-first.mdc` | Prefer docs; same-turn sync when behaviour changes |
| `requirement-understanding.mdc` | Restate + supervisor go-ahead before implement |
| `ponytail.mdc` | YAGNI / reuse ladder; minimum code |
| `best-advice-first.mdc` | Advise best path; do not rubber-stamp |
| `supervisor-chat.mdc` | Chat protocol; commit-and-push; grouping lock hook |
| `cl-sku-match.mdc` | Shared SKU ↔ Custom Label match |
| `shared-inbox.mdc` | Packing → SharedInbox → Queue handoff |
| `shipstation.mdc` | Shared ShipStation client + secrets home |

## App-slug folders

| Folder | Handbook / state |
|--------|------------------|
| `custom-label-database/` | `Custom Label Database/AGENTS.md` · `docs/HANDOFF.md` |
| `order-grouping-sorter/` | `Order Grouping Sorter/AGENTS.md` · `docs/HANDOFF.md` |
| `order-packing-list-generator/` | `Order Packing List Generator/AGENTS.md` · `docs/HANDOFF.md` |
| `production-design-queue-manager/` | `Production Design Queue Manager/AGENTS.md` · `docs/HANDOFF.md` |
| `shipping-label-generator/` | `Shipping Label Generator/AGENTS.md` · `docs/HANDOFF.md` |
| `purchase-order-generator/` | `Purchase Order Generator/AGENTS.md` · `docs/HANDOFF.md` |

Decision owners (locks): [`docs/DECISIONS.md`](../../docs/DECISIONS.md). Parent map: [`AGENTS.md`](../../AGENTS.md).

## How to add a rule

1. **Place:** cross-app / always-on → `global/`; app-only → that app’s slug folder.
2. **Frontmatter:** `description` + either `alwaysApply: true` or `globs` for the app folder.
3. **Do not duplicate locks** — link the owner in `docs/DECISIONS.md` / the existing rule; update the index row above same turn.
