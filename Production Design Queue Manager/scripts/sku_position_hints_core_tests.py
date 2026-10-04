from sku_position_hints_fixtures import *  # noqa: F403

def test_token_tables() -> None:
    assert POSITION_HINT_TOKENS == ("S1", "S2", "SL", "SR", "P", "S")
    assert POSITION_HINT_EXTENSIONS == (".jpg", ".jpeg")
    assert POSITION_HINT_MM["P"] == (80.0, 100.0)
    assert POSITION_HINT_MM["S"] == (100.0, 100.0)
    assert normalize_position_token("p") == "P"
    assert normalize_position_token("LOCATION") is None
    assert flags_for_position_token("P") == ("P", True, False)
    assert flags_for_position_token("S1") == ("S1", False, True)
    assert target_mm_for_position_token("P") == (80.0, 100.0)
    assert target_mm_for_position_token(None) is None
    assert IMAGE_EXTENSIONS == [".png"]

def test_unique_order_png_size_reference() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, "12345.png", (200, 300))
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-M-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == "12345 (Single)"
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)

def test_legacy_pocket_sleeve_png_kids_65x80() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        pocket = _png(single, "12345-P.png", (65, 80))
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-K-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == pocket
        assert results[0]["sku"] == "12345 (Single-Pocket)"
        assert _near(results[0]["width_mm"], 65)
        assert _near(results[0]["height_mm"], 80)

        os.remove(pocket)
        sleeve = _png(single, "12345-S.png", (100, 100), "green")
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-K-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == sleeve
        assert results[0]["sku"] == "12345 (Single-Sleeve)"
        assert _near(results[0]["width_mm"], 100)
        assert _near(results[0]["height_mm"], 100)

def test_duplicate_png_plus_p_jpeg_queues_png_only() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{SKU}.png", (80, 100))
        jpg = _jpg(single, f"{ORDER}-1-P-{SKU}.jpg")
        path, design_type, is_pocket, is_sleeve = find_design_file_vba_logic(
            ORDER,
            1,
            single_designs_folder=single,
            double_designs_folder=double,
            folder_type="single",
            item_sku=SKU,
            is_duplicate_order=True,
        )
        assert path == png
        assert design_type == "single"
        assert is_pocket is False
        assert is_sleeve is False

        token, hinted_p, hinted_s = resolve_sku_position_hint(ORDER, 1, SKU, single)
        assert token == "P"
        assert hinted_p is True
        assert hinted_s is False
        companions = find_sku_position_variant_files(ORDER, 1, SKU, single)
        assert [c["token"] for c in companions] == ["P"]
        assert companions[0]["path"] == jpg

        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"
        assert _near(results[0]["width_mm"], 80)
        assert _near(results[0]["height_mm"], 100)
        assert all(r["path"] != jpg for r in results)
        assert all(not str(r["path"]).lower().endswith((".jpg", ".jpeg")) for r in results)

def test_duplicate_png_plus_s1_jpeg() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{SKU}.png", (100, 100))
        jpg = _jpg(single, f"{ORDER}-1-S1-{SKU}.jpeg")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Sleeve-S1)"
        assert _near(results[0]["width_mm"], 100)
        assert _near(results[0]["height_mm"], 100)
        assert results[0]["path"] != jpg

def test_apparel_size_s_in_sku_is_not_sleeve() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{APPAREL_S_SKU}.png", (200, 300))
        results = _personalised(
            single,
            double,
            item_sku=APPAREL_S_SKU,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single)"
        assert "Sleeve" not in results[0]["sku"]
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)
        assert resolve_sku_position_hint(ORDER, 1, APPAREL_S_SKU, single) == (None, False, False)

def test_jpeg_only_falls_through_to_double() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        jpg = _jpg(single, f"{ORDER}-1-P-{SKU}.jpg")
        double_png = _png(double, f"{ORDER}-1-{SKU}.png", (120, 90), "yellow")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == double_png
        assert results[0]["design_type"] == "double"
        assert results[0]["sku"] == f"{ORDER} (Double)"
        assert results[0]["path"] != jpg
