from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader

from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.run_sample import run_sample_print
from scripts.app.logging.jsonl import JsonlLogger


def _cfg(tmp_path: Path) -> AppConfig:
    return AppConfig(
        raw={
            "paths": {
                "output_dir": str(tmp_path / "output"),
                "logs_dir": str(tmp_path / "logs"),
                "orders_csv": "Order Numbers.csv",
            },
            "batch": {"notes": "n", "processed_by": "t", "ship_from": "Dudley"},
            "logging": {"level": "INFO", "redact_keys": []},
        },
        provider_name="real",
    )


def test_sample_print_writes_combined_pdf_without_shipstation(tmp_path: Path, monkeypatch) -> None:
    called: list[str] = []
    monkeypatch.setattr(
        "scripts.app.providers.select_provider.get_provider",
        lambda *_a, **_k: called.append("provider"),
    )
    day = "2099-01-02"
    orders = tmp_path / "output" / "Order_Numbers" / day
    orders.mkdir(parents=True)
    (orders / "Order Numbers.csv").write_text(
        "Process Number,orders Numbers,Customer Name,Source File,Source Index\n"
        "50,SAMPLE-1,Ada,DTF Des-P50.xlsx,0\n"
        "50,SAMPLE-2,Bea,DTF Des-P50.xlsx,0\n",
        encoding="utf-8",
    )
    (orders / "source_manifest.json").write_text('{"dtf_id": "50"}', encoding="utf-8")
    monkeypatch.setattr("scripts.app.flows.print_labels.run.local_date_ymd", lambda: day)
    monkeypatch.setattr("scripts.app.flows.print_labels.run_sample.local_date_ymd", lambda: day)

    cfg = _cfg(tmp_path)
    rc = run_sample_print(cfg, JsonlLogger.from_config(cfg))

    assert rc == 0
    assert called == []
    combined = tmp_path / "output" / "Sample" / day / "Combined_PDFs" / "50.pdf"
    assert combined.is_file()
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(combined)).pages)
    assert "SAMPLE" in text
    assert "SAMPLE-1" in text
    assert "SAMPLE-2" in text
    assert not (tmp_path / "output" / "Labels").exists()
    assert not (tmp_path / "output" / "Combined_PDFs").exists()
    assert [p.name for p in combined.parent.glob("*.pdf")] == ["50.pdf"]


def test_sample_print_writes_combined_and_one_pdf_per_batch(tmp_path: Path, monkeypatch) -> None:
    day = "2099-01-03"
    orders = tmp_path / "output" / "Order_Numbers" / day
    orders.mkdir(parents=True)
    (orders / "Order Numbers.csv").write_text(
        "Process Number,orders Numbers,Customer Name,Source File,Source Index\n"
        "B100-S1-1,A1,Ada,DTF Des-PB100-S1.xlsx,0\n"
        "B1000-S1-1,A2,Bea,DTF Des-PB1000-S1.xlsx,1\n"
        "B4000-S1-1,A3,Cara,DTF Des-PB4000-S1.xlsx,2\n",
        encoding="utf-8",
    )
    (orders / "source_manifest.json").write_text(
        '{"dtf_id": "B100-S1, B1000-S1, B4000-S1"}',
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.app.flows.print_labels.run.local_date_ymd", lambda: day)
    monkeypatch.setattr("scripts.app.flows.print_labels.run_sample.local_date_ymd", lambda: day)

    rc = run_sample_print(_cfg(tmp_path), JsonlLogger.from_config(_cfg(tmp_path)))
    assert rc == 0
    folder = tmp_path / "output" / "Sample" / day / "Combined_PDFs"
    names = sorted(p.name for p in folder.glob("*.pdf"))
    assert names == [
        "B100-S1, B1000-S1, B4000-S1.pdf",
        "B100-S1.pdf",
        "B1000-S1.pdf",
        "B4000-S1.pdf",
    ]
    combined_text = "\n".join((p.extract_text() or "") for p in PdfReader(str(folder / names[0])).pages)
    assert "A1" in combined_text and "A2" in combined_text and "A3" in combined_text
    only_b100 = "\n".join((p.extract_text() or "") for p in PdfReader(str(folder / "B100-S1.pdf")).pages)
    assert "A1" in only_b100
    assert "A2" not in only_b100
