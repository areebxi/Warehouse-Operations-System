# Shipping Label Generator — snapshot

**Updated:** 14 October 2026  
**Handbook:** `AGENTS.md` · **Behavior:** `REQUIREMENTS.md`

## Continue here

```text
python -m scripts.app.main convert
python -m scripts.app.main print
python -m scripts.app.main sample-print
python -m scripts.app.main void
```

Supervisor restored the previous working copy on 8 Oct 2026. Print, convert, and label-report modules are the pre-split versions again.

Batch files (`RUN.bat`, `SETUP.bat`, `bat_files\*.bat`) call `bat_files\resolve_python.bat`. That uses the `py` launcher when it exists, otherwise `python` on PATH.

- Drop DTF Des files into `DTF Des Files/` (config `desfiles_dir`).
- Secrets in `.env`; tuneables in `shipping_config.yaml`.

## Watch

- CSV mode wins over Excel if both present in the input folder.
- Print/void need supervisor approval on live ShipStation.
- `sample-print` does not call ShipStation. It reads today's converted order list and writes SAMPLE PDFs under `output/Sample/{date}/`. Menu option 6, or `bat_files\run_sample_print.bat`. Live `print` is unchanged.
- Process order is numeric: 1, 2, 3 … not 1, 10, 2. Combined PDF and process-PDF folder use the batch+shift token (`DTF Des-PB1050-S3` → `B1050-S3`).
- The first page of each DTF file is always a Batch Summary. After that, a summary is printed only when the processes it covers add up to the Label Page Threshold or more. A later run left under the threshold has labels only. The number is cell A2 on sheet `Label Page Threshold` in `Configuration Workbook.xlsx` (10 today). A missing or bad cell falls back to 10.
