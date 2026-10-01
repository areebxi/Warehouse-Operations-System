"""ponytail: sorter grouping lock — fails if finish gate / caps / names drift."""
from __future__ import annotations

from test_grouping_customise import *
from test_grouping_finish import *
from test_grouping_fixed_a import *
from test_grouping_fixed_b import *
from test_grouping_fixed_c import *
from test_grouping_fixed_d import *
from test_grouping_intake import *
from test_grouping_names import *
from test_grouping_parts import *
from test_grouping_peel import *
from test_grouping_shift import *
from test_grouping_slots import *
from test_grouping_volume import *
from test_grouping_write import *


def main() -> None:
    test_finish_gate_and_attribute_source()
    test_resend_1014_only_and_blank_shipby()
    test_skip_dtfocean_wp_store()
    test_fawad_and_prime_and_readymade()
    test_warehouse_stock_supplier_slot_x()
    test_b50_on_demand_fotl_ready_made()
    test_plain_in_house_unmatched()
    test_printed_wins_and_mixed_flag1_unmatched()
    test_no_dash_sku_matches_cl_whole()
    test_mixed_supply_goes_on_demand()
    test_today_orders_never_held()
    test_future_fill_uses_future_slot_not_iso_date()
    test_flag30_peels_and_packs_skip_colour()
    test_slotify()
    test_inside_file_colour_groups_then_parts()
    test_printed_under_30_keeps_all_departments_in_one_process()
    test_flag30_blank_brand_stays_in_parent_not_unmatched()
    test_flag30_blank_leftover_when_named_value_peels()
    test_blank_customise_is_readymade_not_unmatched()
    test_mixed_customised_majority_units_tie_readymade()
    test_write_process_csvs()
    test_fixed_batch_codes_first_then_graph_leftover()
    test_named_floor_splits_today_future_when_over_mix()
    test_named_floor_fawad_prime_customised_ironon()
    test_named_floor_skips_30chain_and_keeps_inside_file()
    test_named_ironon_includes_prime_sticker_is_b1050()
    test_named_fawad_personalised_fotl_stays_on_run_shift()
    test_personalised_without_ready_tag_is_held()
    test_six_field_filename_tokens()
    test_small_pool_mixes_today_and_future()
    test_today_300_plus_future_splits_by_date()
    test_volume_300_mixes_today_and_later()
    test_volume_over_300_splits_even_if_today_is_small()
    test_named_floor_mixes_today_future_when_small()
    test_second_run_uses_s2_filename()
    test_next_open_shift_and_written_order_numbers()
    test_priority_today_then_prime_then_as_made()
    test_glow_and_sku_contain_fixed_batches()
    test_b40_gildan_b1050_sticker_b3700_sweatshirt()
    test_2026_09_28_batches_and_priority()
    test_plain_sequence_skips_reserved()
    print("ok")


if __name__ == "__main__":
    main()
