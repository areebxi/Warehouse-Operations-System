# runtime/

Shared cross-app I/O only:

- `SharedInbox/DTF Des/{date}/{shift}/` — Packing dual-write (when Make design queues on) → Queue Design Queues (`--files` sync and/or continuous watcher). See `SharedInbox/DTF Des/README.md`.

Runtime files under this tree are gitignored; nested `README.md` files stay tracked.
Resolve via `shared/paths.py`.
