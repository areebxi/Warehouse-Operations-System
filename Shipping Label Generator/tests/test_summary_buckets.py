from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.app.flows.convert.canonicalize import canonicalize_orders
from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.flows.print_labels.summary_buckets import (
    SHARE_SUMMARY_EXACT_LABELS,
    SHARED_SUMMARIES_ENABLED,
    ProcessGroupResult,
    bucket_process_groups_for_shared_summaries,
)


def _r(pn: str, n: int, *, source_file: str = "", source_index: int = 0) -> ProcessGroupResult:
    return ProcessGroupResult(
        process_number=pn,
        order_count=n,
        label_paths=[Path(f"{source_index}_{pn}_{i}.pdf") for i in range(n)],
        failures=[],
        ship_from="A",
        source_file=source_file,
        source_index=source_index,
    )


def test_share_exact_is_one() -> None:
    assert SHARED_SUMMARIES_ENABLED is True
    assert SHARE_SUMMARY_EXACT_LABELS == 1


def test_single_label_consecutive_processes_share() -> None:
    buckets = bucket_process_groups_for_shared_summaries([_r("100", 1), _r("101", 1), _r("102", 1)])
    assert len(buckets) == 1
    assert buckets[0].summary_process_number == "100"
    assert buckets[0].process_numbers == ["100", "101", "102"]


def test_two_or_more_labels_get_own_summary() -> None:
    buckets = bucket_process_groups_for_shared_summaries([_r("100", 1), _r("101", 2), _r("102", 1)])
    assert [b.summary_process_number for b in buckets] == ["100", "101", "102"]


def test_each_dtf_file_starts_fresh_even_if_process_numbers_consecutive() -> None:
    """
    File A ends at 104, File B starts at 105 — must NOT share across the file boundary,
    even though 104 -> 105 is consecutive numerically.
    """
    buckets = bucket_process_groups_for_shared_summaries(
        [
            _r("100", 1, source_file="DTF-A.xlsx", source_index=0),
            _r("101", 1, source_file="DTF-A.xlsx", source_index=0),
            _r("102", 1, source_file="DTF-A.xlsx", source_index=0),
            _r("103", 1, source_file="DTF-A.xlsx", source_index=0),
            _r("104", 1, source_file="DTF-A.xlsx", source_index=0),
            _r("105", 1, source_file="DTF-B.xlsx", source_index=1),
            _r("106", 1, source_file="DTF-B.xlsx", source_index=1),
        ]
    )
    assert [b.summary_process_number for b in buckets] == ["100", "105"]
    assert buckets[0].process_numbers == ["100", "101", "102", "103", "104"]
    assert buckets[1].process_numbers == ["105", "106"]


def test_multi_dtf_gap_also_starts_fresh() -> None:
    buckets = bucket_process_groups_for_shared_summaries(
        [
            _r("100", 1, source_file="A.xlsx", source_index=0),
            _r("101", 1, source_file="A.xlsx", source_index=0),
            _r("200", 1, source_file="B.xlsx", source_index=1),
            _r("201", 1, source_file="B.xlsx", source_index=1),
        ]
    )
    assert [b.summary_process_number for b in buckets] == ["100", "200"]


def test_canonicalize_keeps_source_and_file_order() -> None:
    df1 = pd.DataFrame(
        {
            "Process Number": ["104", "100"],
            "orders Numbers": ["A1", "A2"],
            "Source File": ["DTF-A.xlsx", "DTF-A.xlsx"],
            "Source Index": [0, 0],
        }
    )
    df2 = pd.DataFrame(
        {
            "Process Number": ["105"],
            "orders Numbers": ["B1"],
            "Source File": ["DTF-B.xlsx"],
            "Source Index": [1],
        }
    )
    out = canonicalize_orders([df1, df2])
    assert list(out.columns) == [
        "Process Number",
        "orders Numbers",
        "Customer Name",
        "Source File",
        "Source Index",
    ]
    assert out["Process Number"].tolist() == ["100", "104", "105"]
    assert out["Source Index"].tolist() == [0, 0, 1]


def test_read_group_preserves_source_file_boundary(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "Process Number,orders Numbers,Customer Name,Source File,Source Index\n"
        "104,O1,Alice,DTF-A.xlsx,0\n"
        "105,O2,Bob,DTF-B.xlsx,1\n",
        encoding="utf-8",
    )
    groups = read_and_group_orders(csv_path)
    assert len(groups) == 2
    assert groups[0].process_number == "104"
    assert groups[0].source_file == "DTF-A.xlsx"
    assert groups[0].source_index == 0
    assert groups[1].process_number == "105"
    assert groups[1].source_file == "DTF-B.xlsx"
    assert groups[1].source_index == 1
