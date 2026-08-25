# Shared Inbox

Handoff folder between warehouse apps.

## DTF Des

- **Live inbox:** `DTF Des/{date}/{shift}/` — packing writes `DTF Des-P*.xlsx` here when Excel outputs are generated (also keeps a copy under packing `Output/`).
- **Processed:** `DTF Des/Processed/{date}/{shift}/` — Queue Missing Logo auto-watcher moves files here after a successful PNG save.
- **Failed:** `DTF Des/Failed/{date}/{shift}/` — auto-watcher moves files here on hard failure.

Date = `DD-MM-YYYY`, shift = `1st Shift` style (same as packing).

Shipping Label Generator does **not** auto-consume this inbox yet.
