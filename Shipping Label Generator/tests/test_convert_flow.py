from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.app.flows.convert.canonicalize import canonicalize_orders
from scripts.app.flows.convert.discover import discover_input_files
from scripts.app.flows.convert.parse_csv import parse_csv_file
from scripts.app.flows.convert.run import _dtf_key_for_manifest


def test_discover_prefers_csv_over_excel(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("Order Number,Process\nA1,1\n", encoding="utf-8")
    # not a real excel, but discovery only checks extensions
    (tmp_path / "b.xlsx").write_text("x", encoding="utf-8")
    d = discover_input_files(tmp_path)
    assert d.mode == "csv"
    assert [p.name for p in d.files] == ["a.csv"]


def test_parse_csv_keeps_process_as_string_without_dot_zero(tmp_path: Path) -> None:
    p = tmp_path / "in.csv"
    p.write_text("Order Number,Process\nA100,2\nA200,10\n", encoding="utf-8")
    r = parse_csv_file(p)
    assert r.ok is True
    assert r.df is not None
    assert "Process Number" in r.df.columns
    assert "orders Numbers" in r.df.columns
    assert r.df["Process Number"].tolist() == ["2", "10"]


def test_canonicalize_dedupes_by_order_and_sorts_by_numeric_then_string() -> None:
    df1 = pd.DataFrame({"Process Number": ["2", "10"], "orders Numbers": ["A100", "A200"]})
    df2 = pd.DataFrame({"Process Number": ["1"], "orders Numbers": ["A100"]})  # duplicate A100, should be ignored
    out = canonicalize_orders([df1, df2])
    assert out["orders Numbers"].tolist() == ["A100", "A200"]
    assert out["Process Number"].tolist() == ["2", "10"]
    assert "Source File" in out.columns
    assert "Source Index" in out.columns

def test_dtf_key_lists_every_file_number(tmp_path: Path) -> None:
    files_2 = [tmp_path / "DTF 200.xlsx", tmp_path / "DTF 400.xlsx"]
    files_3 = [tmp_path / "DTF 200.xlsx", tmp_path / "DTF 300.xlsx", tmp_path / "DTF 400.xlsx"]
    files_5 = [tmp_path / f"DTF {n}.xlsx" for n in (3000, 3100, 3200, 3300, 3400)]

    assert _dtf_key_for_manifest(files_2) == "200-400"
    assert _dtf_key_for_manifest(files_3) == "200-300-400"
    assert _dtf_key_for_manifest(files_5) == "3000-3100-3200-3300-3400"
    assert _dtf_key_for_manifest([tmp_path / "only_500.xlsx"]) == "500"

