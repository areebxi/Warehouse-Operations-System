# Docs

Living (no phases):

| File | What it is |
|------|------------|
| [`../AGENTS.md`](../AGENTS.md) | Domain handbook |
| [`../../AGENTS.md`](../../AGENTS.md) | Parent system map (Warehouse Automation System Engineer) |
| [`HANDOFF.md`](HANDOFF.md) | Current snapshot, pending work, how to continue |
| [`FINDINGS.md`](FINDINGS.md) | Every key finding and locked lesson |
| [`WORKSPACE.md`](WORKSPACE.md) | Paths and file roles |
| [`chats/`](chats/) | Copies of Cursor chat transcripts |

Historical execution logs sit in [`archive/`](archive/).

**Policy** lives in the warehouse parent: `.cursor/rules/custom-label-database/*.mdc` (globs for this app). Nested `.cursor/rules` under this app were removed to avoid drift. **Save everything as we go** — this folder’s docs plus those parent rules are the memory, not the chat.
