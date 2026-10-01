"""Deeper print-size fill simulation."""
from __future__ import annotations

from print_sizes_sim_load import (
    enrich_apparel_keys,
    load_db,
    load_print_sizes,
    load_size_ref,
    print_sr_profiles,
)
from print_sizes_sim_match import (
    build_sr_indexes,
    override_match_count,
    print_multi_design,
    print_spc_detail,
    print_spc_fill_rates,
    run_match_strategies,
    sim_fill_counts,
)


def run() -> None:
    ps = load_print_sizes()
    print("=== Print Sizes lookup table ===")
    print(ps.to_string())

    sr, overrides = load_size_ref()
    print_sr_profiles(sr)

    df = load_db()
    print(f"\n=== Database: {len(df):,} rows ===")
    has_pp = df["Print Positions"] != ""
    print("\nPrint position count distribution (non-empty):")
    print(df.loc[has_pp, "Pos_Count"].value_counts().sort_index().head(10))
    print("\nTop Print Positions values:")
    print(df.loc[has_pp, "Print Positions"].value_counts().head(15))

    sku_suffix, gss_lookup, gs_lookup, sr_by_sku = build_sr_indexes(sr)
    print(
        f"\nLookup indexes: sku_suffix={len(sku_suffix)}, "
        f"gss={len(gss_lookup)}, gs={len(gs_lookup)}"
    )

    df = enrich_apparel_keys(df, ps)
    mapped = (df["Apparel_Size_Key"] != "").sum()
    print(
        f"\nDB rows mapped to Print Sizes apparel key: "
        f"{mapped:,} ({100 * mapped / len(df):.1f}%)"
    )
    print(
        "Unmapped size samples:",
        df.loc[df["Apparel_Size_Key"] == "", "Size"].value_counts().head(15).to_dict(),
    )

    stats = run_match_strategies(df, sr, ps, gs_lookup, sr_by_sku)
    has_gender_size = (sr["Gender"] != "") & (sr["Size"] != "")
    print("\nSize Ref Gender+Size combos:")
    print(
        sr[has_gender_size][
            [
                "Gender",
                "Size",
                "Printing Position",
                "Size Width",
                "Size Height",
                "Printing Size",
            ]
        ]
        .drop_duplicates()
        .to_string()
    )
    print("\n=== Match strategy counts (rows) ===")
    for k, v in stats.items():
        print(f"  {k}: {v:,} ({100 * v / len(df):.1f}%)")

    print("\n=== Supplier Product Code match detail ===")
    print_spc_detail(df, sr_by_sku)
    print_multi_design(sr)

    print("\n=== M01 Print Position Code pattern ===")
    print("F4 = Front A4, B4 = Back A4, F14/F15 = small corners")
    print("Suffix F/B/S in Size Ref likely maps to Front/Back/Sleeve")
    sim_front, sim_multi = sim_fill_counts(df)
    print(f"\nSimulation: Front Center only + apparel key: {sim_front:,}")
    print(f"Simulation: 2+ positions + apparel key: {sim_multi:,}")

    print("\n=== Override Print Size ===")
    print(overrides.to_string())
    print(f"Rows matching override contains: {override_match_count(df, overrides):,}")
    print_spc_fill_rates(df, sr_by_sku)
    print("\nDONE")


if __name__ == "__main__":
    run()
