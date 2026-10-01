import sys
from pathlib import Path
_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
from validate_orders_stock_helpers import *  # noqa: F403

class TestIssueRowExports(unittest.TestCase):
    def test_not_found_blank_item_sku_and_not_in_oos(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        orders = [_order("4102711607", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "30890",
            "013",
            {},
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(len(not_found), 1)
        row = not_found[0]
        self.assertEqual(row[3], "")  # Item SKU blank — prefix is not a real stock id
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "")
        self.assertEqual(row[7], -1)
        self.assertEqual(row[9], STATUS_NOT_IN_CUSTOM_LABEL_DB)
        self.assertEqual(out_of_stock, [])

    def test_not_found_custom_label_missing_stock_id(self):
        complete = "176505LG-C800T-BLK-3-6M"
        orders = [_order("4117710140", [{"sku": complete, "quantity": 1, "name": "Item"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "30886",
            "3100",
            {},
            {},
            {},
            {},
            log=lambda _msg: None,
            labels_missing_stock_id={"c800t-blk-3-6m"},
        )
        self.assertEqual(out_of_stock, [])
        self.assertEqual(len(not_found), 1)
        self.assertEqual(not_found[0][9], STATUS_CUSTOM_LABEL_MISSING_STOCK_ID)

    def test_not_found_stock_id_not_in_stock_levels(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        custom_label_map = {"tpc001-nat-o/s-yes": "7299"}
        orders = [_order("1005", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            {},
            {},
            {},
            custom_label_map,
            log=lambda _msg: None,
        )
        self.assertEqual(out_of_stock, [])
        self.assertEqual(len(not_found), 1)
        row = not_found[0]
        self.assertEqual(row[5], "7299")
        self.assertEqual(row[9], STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS)

    def test_out_of_stock_blank_item_sku_when_fallback(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        custom_label_map = {"tpc001-nat-o/s-yes": "7299"}
        stock_levels = {"7299": 0}
        orders = [_order("1003", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            stock_levels,
            {},
            {},
            custom_label_map,
            log=lambda _msg: None,
        )
        self.assertEqual(not_found, [])
        self.assertEqual(len(out_of_stock), 1)
        row = out_of_stock[0]
        self.assertEqual(row[3], "")  # fallback — do not show fake prefix as Item SKU
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "7299")
        self.assertEqual(row[7], 0)

    def test_out_of_stock_primary_keeps_item_sku(self):
        complete = "KNOWN-SUFFIX"
        stock_levels = {"KNOWN": 0}
        orders = [_order("1004", [{"sku": complete, "quantity": 2, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            stock_levels,
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(not_found, [])
        self.assertEqual(len(out_of_stock), 1)
        row = out_of_stock[0]
        self.assertEqual(row[3], "KNOWN")
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "KNOWN")

    def test_write_stock_issues_csv_headers_and_status(self):
        not_found_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "",
            "30890",
            -1,
            "013",
            STATUS_NOT_IN_CUSTOM_LABEL_DB,
        ]
        oos_row = [
            "1002",
            "Bob",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "7299",
            "30890",
            0,
            "013",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            issues_path = Path(tmp) / "stock_issues.csv"
            write_stock_issues_csv(str(issues_path), [oos_row], [not_found_row])

            with open(issues_path, encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

        self.assertEqual(
            rows[0],
            [
                "Order",
                "Recipient",
                "Quantity",
                "Item SKU",
                "Complete SKU",
                "Stock ID",
                "Tag",
                "Stock Level",
                "Process No",
                "Status",
            ],
        )
        self.assertEqual(rows[1][9], STATUS_NOT_IN_CUSTOM_LABEL_DB)
        self.assertEqual(rows[1][3], "")
        self.assertEqual(rows[1][4], "46139LG-TPC001-NAT-O/S-Yes")
        self.assertEqual(rows[1][7], "N/A")
        self.assertEqual(rows[2][9], STATUS_OUT_OF_STOCK)
        self.assertEqual(rows[2][5], "7299")

    def test_format_run_summary_lists_marketplace_skus(self):
        not_found = [
            ["1", "A", 1, "", "SKU-A-FULL", "", "t", -1, "01"],
            ["2", "B", 1, "", "SKU-A-FULL", "", "t", -1, "01"],
        ]
        oos = [["3", "C", 1, "", "SKU-B-FULL", "99", "t", 0, "01"]]
        text = format_run_summary(
            tag_label="013-P-04-Odd Items-7000",
            orders_processed=48,
            in_stock_items=[[] for _ in range(45)],
            out_of_stock_items=oos,
            not_found_items=not_found,
            issues_filename="stock_issues_tag_x_20260716_130000.csv",
        )
        self.assertIn("Not found: 1 SKU(s)", text)
        self.assertIn("  - SKU-A-FULL", text)
        self.assertIn("Out of stock: 1 SKU(s)", text)
        self.assertIn("  - SKU-B-FULL", text)
        self.assertIn("stock_issues_tag_x_20260716_130000.csv", text)

    def test_format_run_summary_all_clear(self):
        text = format_run_summary(
            tag_label="007",
            orders_processed=10,
            in_stock_items=[[1]] * 10,
            out_of_stock_items=[],
            not_found_items=[],
        )
        self.assertIn("All orders found and in stock.", text)

