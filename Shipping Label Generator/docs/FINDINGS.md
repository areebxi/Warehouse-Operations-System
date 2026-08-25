# Shipping Label Generator — key findings

- Provider: ShipStation API (`SHIPPING_PROVIDER=real`). Secrets via env/`.env` only.
- Convert inputs from `DTF Des Files/`: Excel needs exact headers `Order - Number` and `Process Num` (matches packing DTF Des). Optional `Ship To - Name`.
- Does not use packing **Orders Details** as input.
- Flows: convert → canonical orders; print → labels + process/combined PDFs; void → void list.
- Processed inputs archive under `DTF Des Files - Processed/` with manifest hashing.
- Old PLAN/IMPLEMENTATION docs are in `docs/archive/` (build history, not daily process).
