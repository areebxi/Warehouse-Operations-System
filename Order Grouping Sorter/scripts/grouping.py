"""Grouping façade — public API for run_sorter and tests."""
from __future__ import annotations

from grouping_bins import group_orders, sort_raw_orders
from grouping_finish import attrs_for_sku, finish_for_sku
from grouping_fixed import fixed_batch_matches, named_process_code
from grouping_intake import orders_from_ss
from grouping_io import (
    input_date_folder,
    next_open_shift,
    order_numbers_in_date_folder,
    write_csv,
    write_process_csvs,
)
from grouping_models import (
    CHAIN_30,
    CSV_FIELDNAMES,
    EXCLUDE_STORES,
    EXCLUDE_TAG,
    IN_HOUSE,
    ON_DEMAND,
    PART_CAP,
    PERSONALISED_READY_TAG,
    PLAIN_MARKERS,
    PRIME_TAG,
    RESEND_FILE,
    RESEND_TAG,
    SHIFT1_SPLIT_ORDERS,
    SHIFT_PER_RUN,
    UNMATCHED_FILE,
    WAREHOUSE_STOCK,
    LineAttrs,
    Order,
    ProcessBin,
    ProcessPart,
    SortResult,
    date_slot,
    parse_qty,
    parse_ship_by,
    sku_is_plain_override,
    slotify,
)
from grouping_parts import assign_inside_file
from grouping_peel import peel_chain
from grouping_report import format_report
from grouping_shift import (
    FIXED_BATCH_CODES,
    NAMED_CODES,
    RESERVED_BATCH_NUMS,
    next_leftover_batch_codes,
    next_plain_batch_codes,
    shift_file_token,
    shift_number,
    shift_pair,
    six_field_core,
)
from grouping_slots import (
    left_slots,
    mixed_customised_slot,
    order_skips_colour,
    order_source_slot,
    prime_slot,
)
