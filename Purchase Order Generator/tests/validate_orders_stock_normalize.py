import sys
from pathlib import Path
_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
from validate_orders_stock_helpers import *  # noqa: F403

class TestNormalizePackingRows(unittest.TestCase):
    def test_len_9_issue_row_maps_to_packing_format(self):
        issue_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "7299",
            "30890",
            0,
            "013",
        ]
        normalized = normalize_packing_rows([issue_row])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0][3], "7299")
        self.assertEqual(normalized[0][10], "46139LG-TPC001-NAT-O/S-Yes")

    def test_len_9_without_stock_id_blank_item_sku(self):
        issue_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "",
            "30890",
            -1,
            "013",
        ]
        normalized = normalize_packing_rows([issue_row])
        self.assertEqual(normalized[0][3], "")
        self.assertEqual(normalized[0][10], "46139LG-TPC001-NAT-O/S-Yes")

