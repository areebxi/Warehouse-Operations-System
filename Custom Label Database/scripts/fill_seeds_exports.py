"""Public re-exports so `from fill_from_seeds import …` keeps working."""
from __future__ import annotations

from fill_seeds_apparel import (
    classify,
    g1_format,
    has_exact_mock_uid,
    infer_printing_position,
    is_age_size,
    is_shirt_row,
    kinds_in,
    map_print_sizes_key,
    map_sr_size,
    normalize_gender_apparel_for_sr_sku,
    paper_from_printing_size,
    sr_gender,
    suffix_name,
)
from fill_seeds_lookup import lookup_sr
from fill_seeds_maps import (
    AGE_TO_PRINT,
    AGE_TO_SR,
    KNOWN_HUMAN,
    LETTER_TO_MEN_PRINT,
    LETTER_TO_SR,
    PE_AGE,
    RE_NOT_SHIRT_GA,
    RE_SHIRT_GA,
    RE_SHIRT_SKU,
    SUFFIX_TO_NAME,
)
from fill_seeds_pe import step_pe_enrich
from fill_seeds_print import step_print_sizes
from fill_seeds_size import (
    load_pe_index,
    load_pe_sizes,
    load_print_sizes,
    pe_sizes_from_index,
)
from fill_seeds_size_ref import load_size_ref, pick_pc_block, score_block
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
from fill_seeds_util import (
    ALL_STEPS,
    BACKUPS,
    BASE,
    BTC_SUPPLIER,
    DEFAULT_CONFIG,
    DEFAULT_DB,
    DEFAULT_PE,
    DEFAULT_PRINT_SIZES,
    DEDICATED_SUPPLIERS,
    MAX_SLOTS,
    POCKET_WH,
    SHEET,
    SUPPORT,
    apparel_image_slug,
    clean,
    customise_for_label,
    extract_mock,
    hyphen_tshirt_in_slug,
    mm_str,
    split_positions,
    to_num,
    uid_from_custom_label,
)

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from size_code_logic import load_overrides, load_size_ref_index  # noqa: E402
