# runtime/

Shared cross-app I/O only:

- `SharedInbox/DTF Des/{date}/{shift}/` — Packing dual-write (when Make design queues on) → Queue Design Queues (`--files` sync and/or continuous watcher)

Per-app Input/Output/Logs live inside each app folder.
Resolve via `shared/paths.py`.
