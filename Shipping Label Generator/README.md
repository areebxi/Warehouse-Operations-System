# Shipping Label App (Parity-First Rebuild)

Built from `PLAN.md` + `REQUIREMENTS.md`.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```powershell
python -m scripts.app.main --help
python -m scripts.app.main convert
python -m scripts.app.main print
python -m scripts.app.main void
```

## Test combined-PDF logic using existing process PDFs

If you already have per-process PDFs (files named `process_*.pdf`), you can rebuild a combined PDF without reprocessing labels:

```powershell
python -m scripts.app.tools.recombine_from_process_pdfs `
  --process-pdfs-dir "output\Process_PDFs\2026-04-29\200" `
  --out-pdf "output\Combined_PDFs\2026-04-29\combined_TEST.pdf"
```

Or via batch entrypoints:

- `bat_files\run_convert.bat`
- `bat_files\run_print.bat`
- `bat_files\ALL_VOID_LABELS.bat` (void all active shipments per order)
- `bat_files\VOID.bat` (void one active shipment per order)