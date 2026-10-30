# SharedInbox / DTF Des

Packing → Queue handoff tray.

When **Make design queues** is on, Packing copies `DTF Des-P*.xlsx` here under `{DD-MM-YYYY}/{nth} Shift/` after that input’s packing PDFs, then Queue runs Design Queues on the copy (`--files` and/or the continuous watcher).

Runtime date/shift files are gitignored. Only this `README.md` is tracked. An empty tray on a new PC is fine — the next packing run creates the folders.
