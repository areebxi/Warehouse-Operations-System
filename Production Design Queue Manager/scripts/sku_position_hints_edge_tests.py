from sku_position_hints_fixtures import *  # noqa: F403

def test_double_folder_sku_png_unchanged() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        double_png = _png(double, f"{ORDER}-1-{SKU}.png", (150, 90), "yellow")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == double_png
        assert results[0]["design_type"] == "double"
        assert _near(results[0]["width_mm"], 150)
        assert _near(results[0]["height_mm"], 90)

def test_normal_mode_ignores_jpeg_hints() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        designs = os.path.join(tmp, "normal")
        os.makedirs(designs)
        png = _png(designs, f"{SKU}.png", (200, 300))
        _jpg(designs, f"P-{SKU}.jpg")
        _jpg(designs, f"{ORDER}-P-{SKU}.jpg")
        with patch(
            "src.core.design_processing_single.get_cl_position_size_entries",
            return_value=_entries(200, 300),
        ):
            results = process_single_designs(
                SKU,
                designs,
                FACTOR,
                canvas_width_mm=None,
                canvas_height_mm=None,
                design_padding=0,
                cl_csv_path=Path("missing-cl-for-tests.csv"),
            )
        for item in results:
            image = item.get("image")
            if image is not None:
                image.close()
        assert len(results) == 1
        assert results[0]["path"] == png
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)
        assert all(not str(r["path"]).lower().endswith((".jpg", ".jpeg")) for r in results)

def test_kids_sku_filename_p_hint_is_80x100_not_65x80() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{KIDS_SKU}.png", (80, 100))
        _jpg(single, f"{ORDER}-1-P-{KIDS_SKU}.jpg")
        results = _personalised(
            single,
            double,
            item_sku=KIDS_SKU,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"
        assert _near(results[0]["width_mm"], 80)
        assert _near(results[0]["height_mm"], 100)
        assert not _near(results[0]["width_mm"], 65)

def test_p_wins_over_later_tokens_and_index_zero_stem() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-{SKU}.png", (80, 100))
        _jpg(single, f"{ORDER}-S-{SKU}.jpg")
        _jpg(single, f"{ORDER}-P-{SKU}.jpg")
        _jpg(single, f"{ORDER}-S1-{SKU}.jpeg")
        token, is_pocket, is_sleeve = resolve_sku_position_hint(ORDER, 0, SKU, single)
        assert token == "P"
        assert is_pocket is True
        assert is_sleeve is False
        results = _personalised(single, double, duplicate_index=0)
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"

def test_slash_in_sku_becomes_hyphen() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        os.makedirs(single)
        sku = "BG/BG140S"
        png = _png(single, f"{ORDER}-1-BG-BG140S.png", (80, 100))
        _jpg(single, f"{ORDER}-1-P-BG-BG140S.jpg")
        path, _, is_pocket, is_sleeve = find_design_file_vba_logic(
            ORDER,
            1,
            single_designs_folder=single,
            item_sku=sku,
            is_duplicate_order=True,
        )
        assert path == png
        assert is_pocket is False
        token, hinted_p, _ = resolve_sku_position_hint(ORDER, 1, sku, single)
        assert token == "P"
        assert hinted_p is True

def test_unique_order_ignores_sku_jpeg_hint() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, "12345.png", (200, 300))
        _jpg(single, f"12345-P-{SKU}.jpg")
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku=SKU,
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == "12345 (Single)"
        assert _near(results[0]["width_mm"], 200)
