from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.app.flows.convert.canonicalize import canonicalize_orders
from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.flows.print_labels.summary_buckets import (
    SUMMARY_EVERY_LABELS,
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


def test_summary_every_is_ten() -> None:
    assert SHARED_SUMMARIES_ENABLED is True
    assert SUMMARY_EVERY_LABELS == 10


def test_batch_process_numbers_sort_1_then_2_not_10() -> None:
    buckets = bucket_process_groups_for_shared_summaries(
        [_r(f"B100-S1-{n}", 1) for n in (1, 10, 11, 12, 13, 2, 3, 4, 5, 6, 7, 8, 9)]
    )
    assert [n for b in buckets for n in b.process_numbers] == [f"B100-S1-{n}" for n in range(1, 14)]
    # 1 label each: first 10 share one summary, the last 3 are labels only.
    assert [(b.process_numbers[0], b.include_summary, b.label_count) for b in buckets] == [
        ("B100-S1-1", True, 10),
        ("B100-S1-11", False, 3),
    ]


def test_summary_covers_a_run_once_labels_add_up() -> None:
    # 9+6 reaches 10, so the first summary sits in front of processes 1 and 2.
    counts = [9, 6, 4, 2, 11, 1, 1, 2, 4, 5, 7, 3, 2, 2]
    buckets = bucket_process_groups_for_shared_summaries([_r(str(i + 1), n) for i, n in enumerate(counts)])
    assert [(b.process_numbers, b.include_summary, b.label_count) for b in buckets] == [
        (["1", "2"], True, 15),
        (["3", "4", "5"], True, 17),
        (["6", "7", "8", "9", "10"], True, 13),
        (["11", "12"], True, 10),
        (["13", "14"], False, 4),
    ]


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
    assert [tuple(b.process_numbers) for b in buckets] == [("100", "101", "102", "103", "104"), ("105", "106")]
    assert [b.include_summary for b in buckets] == [False, False]


def test_multi_dtf_gap_also_starts_fresh() -> None:
    buckets = bucket_process_groups_for_shared_summaries(
        [
            _r("100", 1, source_file="A.xlsx", source_index=0),
            _r("101", 1, source_file="A.xlsx", source_index=0),
            _r("200", 1, source_file="B.xlsx", source_index=1),
            _r("201", 1, source_file="B.xlsx", source_index=1),
        ]
    )
    assert [tuple(b.process_numbers) for b in buckets] == [("100", "101"), ("200", "201")]
    assert [b.include_summary for b in buckets] == [False, False]


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
    batch = pd.DataFrame(
        {
            "Process Number": ["B100-S1-10", "B100-S1-2"],
            "orders Numbers": ["C1", "C2"],
            "Source File": ["DTF.xlsx", "DTF.xlsx"],
            "Source Index": [0, 0],
        }
    )
    ordered = canonicalize_orders([batch])
    assert ordered["Process Number"].tolist() == ["B100-S1-2", "B100-S1-10"]
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
