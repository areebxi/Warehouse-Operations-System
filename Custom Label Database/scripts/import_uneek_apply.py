"""Upsert Uneek rows into CL + download images."""
from __future__ import annotations

import csv
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from import_uneek_map import (
    _IMAGE_COL,
    _ext_from_url,
    download_one,
    uneek_to_cl_fields,
)
from shared import paths as wh


def upsert_uneek_into_cl(
    uneek_rows: list[dict[str, str]],
    cl_path: Path,
    *,
    dry_run: bool,
    no_backup: bool,
) -> tuple[int, int, dict[str, str]]:
    with open(cl_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    by_label: dict[str, int] = {}
    for i, r in enumerate(rows):
        lab = (r.get("Custom Label") or "").strip().casefold()
        if lab and lab not in by_label:
            by_label[lab] = i

    added = updated = 0
    url_by_stem: dict[str, str] = {}

    for u in uneek_rows:
        fields = uneek_to_cl_fields(u)
        short = fields["Custom Label"]
        key = short.casefold()
        url = u.get(_IMAGE_COL) or ""
        stem = fields.get("Apparel Image") or ""
        if stem and url and stem not in url_by_stem:
            url_by_stem[stem] = url

        if key in by_label:
            row = rows[by_label[key]]
            changed = False
            for col, val in fields.items():
                if col not in fieldnames or col == "Custom Label":
                    continue
                if (row.get(col) or "") != val:
                    row[col] = val
                    changed = True
            if changed:
                updated += 1
        else:
            row = {c: "" for c in fieldnames}
            for col, val in fields.items():
                if col in row:
                    row[col] = val
            rows.append(row)
            by_label[key] = len(rows) - 1
            added += 1

    print(
        f"Would add={added:,} update={updated:,} unique {_IMAGE_COL} images={len(url_by_stem):,}",
        flush=True,
    )
    if dry_run:
        return added, updated, url_by_stem

    if not no_backup:
        backups = wh.cl_backups_dir()
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backups / f"{cl_path.stem}_preFill_{stamp}{cl_path.suffix}"
        shutil.copy2(cl_path, backup)
        print(f"Backup: {backup}", flush=True)

    with open(cl_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {cl_path} ({len(rows):,} rows)", flush=True)
    return added, updated, url_by_stem


def download_uneek_images(url_by_stem: dict[str, str]) -> int:
    apparel_dir = wh.images_apparel_dir()
    apparel_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[str, Path]] = []
    for stem, url in sorted(url_by_stem.items()):
        dest = apparel_dir / f"{stem}{_ext_from_url(url)}"
        jobs.append((url, dest))

    print(f"Downloading {len(jobs)} {_IMAGE_COL} file(s) -> {apparel_dir}", flush=True)
    ok = fail = skip = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(download_one, url, dest): dest.stem for url, dest in jobs}
        for fut in as_completed(futs):
            stem, success, detail = fut.result()
            if detail == "exists":
                skip += 1
            elif success:
                ok += 1
            else:
                fail += 1
                print(f"  FAIL {stem}: {detail}", flush=True)
    print(
        f"Images: saved={ok} existed={skip} failed={fail} in {time.time()-t0:.1f}s",
        flush=True,
    )
    return fail
