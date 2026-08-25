# Shipping Label Generator — snapshot

**Updated:** 25 August 2026 (warehouse AGENTS wiring)  
**Handbook:** `AGENTS.md` · **Behavior:** `REQUIREMENTS.md`

## Continue here

```text
python -m scripts.app.main convert
python -m scripts.app.main print
python -m scripts.app.main void
```

- Drop DTF Des files into `DTF Des Files/` (config `desfiles_dir`).
- Secrets in `.env`; tuneables in `shipping_config.yaml`.

## Watch

- CSV mode wins over Excel if both present in the input folder.
- Print/void need supervisor approval on live ShipStation.
