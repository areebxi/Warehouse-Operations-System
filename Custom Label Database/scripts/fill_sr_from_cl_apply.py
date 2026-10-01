"""Pick CL payloads and apply blank-only Size References fill."""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

from fill_from_seeds import clean
from fill_sr_from_cl_parse import desired_sr_rows, parse_cl_mock_uid, parse_sr_key, slot_payload
from fill_sr_from_cl_paths import BLANK_FILL_COLS, SR_COLS


def blank(val) -> bool:
    return clean(val) == ""


def fill_cell(existing: dict, col: str, incoming: str, counts: dict, prefixed: str) -> None:
    if not incoming:
        return
    if not blank(existing.get(col)):
        counts[f"skip_already_{prefixed}_{col}"] += 1
        return
    existing[col] = incoming
    counts[f"filled_{prefixed}_{col}"] += 1


def empty_sr_row() -> dict:
    return {c: "" for c in SR_COLS}


def pick_cl_payloads(cl: pd.DataFrame) -> tuple[dict[str, dict], dict]:
    stats: dict[str, int] = defaultdict(int)
    best: dict[str, dict] = {}
    records = cl.to_dict("records")
    stats["cl_label_rows"] = len(records)
    for rec in records:
        parsed = parse_cl_mock_uid(rec.get("Custom Label", ""))
        if parsed is None:
            stats["cl_skipped_not_mock_uid"] += 1
            continue
        stats["cl_mock_uid_rows"] += 1
        payload = slot_payload(rec)
        key = payload["key"]
        prev = best.get(key)
        if prev is None:
            best[key] = payload
        elif payload["wh_score"] > prev["wh_score"] or (
            payload["wh_score"] == prev["wh_score"]
            and payload["ga_len"] > prev["ga_len"]
        ):
            stats["cl_duplicate_keys_replaced"] += 1
            best[key] = payload
        else:
            stats["cl_duplicate_keys_kept_first"] += 1
    stats["cl_unique_mock_uid_keys"] = len(best)
    return best, stats


def apply_fill(
    sr_rows: list[dict],
    payloads: dict[str, dict],
    mock_meta: dict[str, dict[str, str]],
) -> tuple[list[dict], dict]:
    counts: dict[str, int] = defaultdict(int)
    by_key: dict[str, list[int]] = defaultdict(list)
    for i, rec in enumerate(sr_rows):
        key = parse_sr_key(rec.get("SKU Value", ""))
        if key:
            by_key[key].append(i)
            counts["sr_existing_mock_uid_rows"] += 1
        else:
            counts["sr_non_mock_or_other_rows"] += 1

    counts["sr_existing_mock_uid_keys"] = len(by_key)
    appends: list[dict] = []
    samples_new: list[str] = []
    samples_extra: list[str] = []
    samples_filled: list[str] = []

    for key, payload in payloads.items():
        desired = desired_sr_rows(payload, mock_meta)
        idxs = by_key.get(key, [])
        if not idxs:
            appends.extend(desired)
            counts["keys_appended"] += 1
            counts["rows_appended_new_key"] += len(desired)
            if payload["n_slots"] > 1:
                counts["new_keys_multi_design"] += 1
            if len(samples_new) < 8:
                samples_new.append(f"{key} n={payload['n_slots']}")
            continue

        counts["keys_already_present"] += 1
        extra = len(desired) - len(idxs)
        if extra > 0:
            counts["keys_extra_design_rows"] += 1
            counts["rows_appended_extra_design"] += extra
            nd = str(len(desired))
            for i in idxs:
                sr_rows[i]["Number of Designs"] = nd
            for rec in desired[len(idxs) :]:
                rec["Number of Designs"] = nd
                appends.append(rec)
            if len(samples_extra) < 6:
                samples_extra.append(f"{key} {len(idxs)}->{len(desired)}")

        n_overlap = min(len(idxs), len(desired))
        expand = extra > 0
        before_fills = sum(counts.get(f"filled_existing_{c}", 0) for c in BLANK_FILL_COLS)
        for j in range(n_overlap):
            existing = sr_rows[idxs[j]]
            incoming = desired[j]
            for col in BLANK_FILL_COLS:
                if (
                    col == "Suffix"
                    and not expand
                    and len(desired) == 1
                    and blank(existing.get("Suffix"))
                ):
                    counts["skip_single_blank_suffix"] += 1
                    continue
                fill_cell(existing, col, incoming.get(col, ""), counts, "existing")
        after_fills = sum(counts.get(f"filled_existing_{c}", 0) for c in BLANK_FILL_COLS)
        if after_fills > before_fills and len(samples_filled) < 6:
            samples_filled.append(key)

    sr_rows.extend(appends)
    counts["rows_appended_total"] = len(appends)
    counts["sample_new"] = samples_new  # type: ignore[assignment]
    counts["sample_extra"] = samples_extra  # type: ignore[assignment]
    counts["sample_filled"] = samples_filled  # type: ignore[assignment]
    return sr_rows, counts
