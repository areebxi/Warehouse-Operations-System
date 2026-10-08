# Shipping Label Generator — snapshot

**Updated:** 8 October 2026 (previous working copy restored)  
**Handbook:** `AGENTS.md` · **Behavior:** `REQUIREMENTS.md`

## Continue here

```text
python -m scripts.app.main convert
python -m scripts.app.main print
python -m scripts.app.main void
```

Supervisor restored the previous working copy on 8 Oct 2026. Print, convert, and label-report modules are the pre-split versions again.

Batch files (`RUN.bat`, `SETUP.bat`, `bat_files\*.bat`) call `bat_files\resolve_python.bat`. That uses the `py` launcher when it exists, otherwise `python` on PATH.

- Drop DTF Des files into `DTF Des Files/` (config `desfiles_dir`).
- Secrets in `.env`; tuneables in `shipping_config.yaml`.

## Watch

- CSV mode wins over Excel if both present in the input folder.
- Print/void need supervisor approval on live ShipStation.
