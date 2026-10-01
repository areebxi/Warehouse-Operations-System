"""Pipeline runner for fill_from_seeds CLI."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from fill_seeds_pe import step_pe_enrich
from fill_seeds_print import step_print_sizes
from fill_seeds_size import load_pe_index, load_pe_sizes, load_print_sizes, pe_sizes_from_index
from fill_seeds_steps import (
    step_apparel_image,
    step_areeb,
    step_customise,
    step_dedicated_suppliers,
    step_printing_type,
    step_supplier_name,
    step_supplier_sku,
    step_supply,
)
from fill_seeds_util import ALL_STEPS, write_db

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from size_code_logic import load_overrides, load_size_ref_index  # noqa: E402


def _check_helper_paths(args, steps: tuple[str, ...]) -> int:
    for label, path in (
        ("BTC Product Data", args.pe),
        ("Size References", args.config),
        ("Shirts Print Sizes", args.print_sizes),
    ):
        need = (
            ("pe" in steps and label == "BTC Product Data")
            or ("print" in steps and label != "BTC Product Data")
            or ("print" in steps and label == "BTC Product Data" and args.shirts_only)
        )
        if need and not path.exists():
            print(f"Missing {label}: {path}", file=sys.stderr)
            return 1
    return 0


def run_fill(args) -> int:
    steps = tuple(s.strip().lower() for s in args.steps.split(",") if s.strip())
    unknown = [s for s in steps if s not in ALL_STEPS]
    if unknown:
        print(f"Unknown steps: {unknown}. Allowed: {ALL_STEPS}", file=sys.stderr)
        return 2

    db_path: Path = args.file.resolve()
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1
    if _check_helper_paths(args, steps):
        return 1

    print(f"Loading DB: {db_path}", flush=True)
    if db_path.suffix.lower() == ".csv":
        df = pd.read_csv(db_path, dtype=str, low_memory=False)
    else:
        df = pd.read_excel(db_path, sheet_name=args.sheet, dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()
    print(f"  rows={len(df):,} cols={len(df.columns)}", flush=True)

    work = df
    if args.iloc_from is not None:
        if args.iloc_from < 0 or args.iloc_from >= len(df):
            print(
                f"--iloc-from {args.iloc_from} out of range for {len(df)} rows",
                file=sys.stderr,
            )
            return 1
        work = df.iloc[args.iloc_from :].copy()
        print(f"  scoped to iloc[{args.iloc_from}:] -> {len(work)} rows", flush=True)

    counts: dict = defaultdict(int)

    if "sku" in steps:
        print("Step: supplier SKU from Custom Label UID...", flush=True)
        step_supplier_sku(work, counts)

    pe_index = None
    if "pe" in steps:
        print(f"Loading BTC Product Data: {args.pe}", flush=True)
        pe_index = load_pe_index(args.pe)
        print(f"  PE UIDs={len(pe_index):,}", flush=True)
        print("Step: BTC Product Data enrich...", flush=True)
        if args.overwrite_pe_taxonomy:
            print(
                "  overwrite Category / Sub-Category / Department / Sub-Department from PE",
                flush=True,
            )
        step_pe_enrich(
            work, pe_index, counts, overwrite_taxonomy=args.overwrite_pe_taxonomy
        )

    if "suppliers" in steps:
        print("Step: dedicated supplier columns...", flush=True)
        step_dedicated_suppliers(work, counts)

    if "image" in steps:
        print("Step: Apparel Image slug...", flush=True)
        step_apparel_image(work, counts)

    if "print" in steps:
        print("Step: print sizes (shirts -> Print Sizes, else Size References)...", flush=True)
        print(f"  loading Size References + Override: {args.config}", flush=True)
        size_index = load_size_ref_index(args.config)
        overrides = load_overrides(args.config)
        print(f"  loading Shirts Print Sizes: {args.print_sizes}", flush=True)
        ps_table = load_print_sizes(args.print_sizes)
        pe_sizes: dict = {}
        if pe_index is not None:
            pe_sizes = pe_sizes_from_index(pe_index)
            print(f"  PE size UIDs={len(pe_sizes):,} (from loaded PE)", flush=True)
        elif args.pe.exists():
            print(f"  loading PE sizes: {args.pe}", flush=True)
            pe_sizes = load_pe_sizes(args.pe)
            print(f"  PE size UIDs={len(pe_sizes):,}", flush=True)
        print(
            f"  SR bases={len(size_index.bases_longest_first)} "
            f"overrides={len(overrides)} shirt bands={len(ps_table)}",
            flush=True,
        )
        if args.shirts_only:
            print("  scoped to shirts only", flush=True)
        if args.w1_blank:
            print("  scoped to blank Width 1", flush=True)
        step_print_sizes(
            work,
            size_index,
            overrides,
            ps_table,
            counts,
            only_missing_wh=args.only_missing_wh,
            pe_sizes=pe_sizes,
            shirts_only=args.shirts_only,
            w1_blank=args.w1_blank,
        )

    if "customise" in steps:
        print("Step: Customise from Custom Label (-P{digit}- or Yes token => Yes)...", flush=True)
        step_customise(work, counts)

    if "areeb" in steps:
        print("Step: Areeb 30-chain from Gender Apparel warehouse standard...", flush=True)
        step_areeb(work, counts)

    if "supply" in steps:
        print("Step: Supply Method (FOTL t-shirts / iron-on+sticker / on-demand)...", flush=True)
        step_supply(work, counts)

    if "printing_type" in steps:
        print("Step: Printing Type (DTF / mug Sublimation)...", flush=True)
        step_printing_type(work, counts)

    if "supplier_name" in steps:
        print("Step: Supplier Name (Absolute babysuits / Uneek / BTC)...", flush=True)
        step_supplier_name(work, counts)

    if args.iloc_from is not None:
        for c in work.columns:
            df.loc[work.index, c] = work[c]

    print("\n=== Counts ===", flush=True)
    for k in sorted(counts):
        print(f"  {k}: {counts[k]:,}", flush=True)

    if args.dry_run:
        print("\nDry run — no files written.", flush=True)
        return 0

    write_db(df, db_path, args.sheet, no_backup=args.no_backup)
    return 0
