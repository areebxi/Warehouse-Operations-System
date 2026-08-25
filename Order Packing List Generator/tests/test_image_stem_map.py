"""Tests for image stem-map scan and memory/disk caches."""

from __future__ import annotations

import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.pipeline_generate_packing_list_pdf.image_lookup import (
    _scan_image_stem_map,
    build_image_stem_map_impl,
    clear_stem_map_caches,
)
from scripts.pipeline_generate_packing_list_pdf import stem_map_cache as smc


class TestImageStemMap(unittest.TestCase):
    def setUp(self) -> None:
        clear_stem_map_caches()
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.cache_dir = self.root / "cache_home"
        self.cache_dir.mkdir()
        self._cache_patch = patch.object(smc, "stem_map_cache_dir", return_value=self.cache_dir)
        self._cache_patch.start()
        self.addCleanup(self._cache_patch.stop)

    def _touch(self, rel: str, content: bytes = b"x") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_scan_top_level_extensions_and_first_wins(self) -> None:
        self._touch("Alpha.png")
        self._touch("beta.JPG")
        self._touch("gamma.jpeg")
        self._touch("notes.txt")
        self._touch("Alpha.jpg")  # duplicate stem; first wins by scandir order
        self._touch("sub/nested.png")

        result = _scan_image_stem_map(self.root, recursive=False)
        self.assertIn("Alpha", result)
        self.assertIn("beta", result)
        self.assertIn("gamma", result)
        self.assertNotIn("notes", result)
        self.assertNotIn("nested", result)
        self.assertTrue(str(result["Alpha"]).lower().endswith((".png", ".jpg")))

    def test_scan_recursive(self) -> None:
        self._touch("top.png")
        self._touch("deep/a/b/nested.png")
        result = _scan_image_stem_map(self.root, recursive=True)
        self.assertEqual(set(result), {"top", "nested"})
        self.assertTrue(result["nested"].as_posix().endswith("deep/a/b/nested.png"))

    def test_memory_cache_reuses_without_rescan(self) -> None:
        self._touch("one.png")
        calls = {"n": 0}
        real_scan = _scan_image_stem_map

        def counting_scan(root, *, recursive=False):
            calls["n"] += 1
            return real_scan(root, recursive=recursive)

        with patch(
            "scripts.pipeline_generate_packing_list_pdf.image_lookup._scan_image_stem_map",
            side_effect=counting_scan,
        ):
            m1 = build_image_stem_map_impl(self.root, recursive=False)
            m2 = build_image_stem_map_impl(self.root, recursive=False)
            m3 = build_image_stem_map_impl(self.root, recursive=False)
        self.assertEqual(calls["n"], 1)
        self.assertIs(m1, m2)
        self.assertIs(m2, m3)
        self.assertEqual(m1, {"one": self.root.resolve() / "one.png"})

    def test_disk_cache_loads_after_memory_clear(self) -> None:
        self._touch("disk.png")
        first = build_image_stem_map_impl(self.root, recursive=False)
        self.assertEqual(len(first or {}), 1)
        clear_stem_map_caches()
        calls = {"n": 0}
        real_scan = _scan_image_stem_map

        def counting_scan(root, *, recursive=False):
            calls["n"] += 1
            return real_scan(root, recursive=recursive)

        with patch(
            "scripts.pipeline_generate_packing_list_pdf.image_lookup._scan_image_stem_map",
            side_effect=counting_scan,
        ):
            second = build_image_stem_map_impl(self.root, recursive=False)
        self.assertEqual(calls["n"], 0)
        self.assertEqual(set(second or {}), {"disk"})
        self.assertEqual(second["disk"].name, "disk.png")

    def test_mtime_mismatch_forces_rescan(self) -> None:
        self._touch("a.png")
        build_image_stem_map_impl(self.root, recursive=False)
        clear_stem_map_caches()
        # Change folder mtime so disk cache fingerprint fails.
        new_mtime = time.time() + 120
        os.utime(self.root, (new_mtime, new_mtime))
        self._touch("b.png")
        calls = {"n": 0}
        real_scan = _scan_image_stem_map

        def counting_scan(root, *, recursive=False):
            calls["n"] += 1
            return real_scan(root, recursive=recursive)

        with patch(
            "scripts.pipeline_generate_packing_list_pdf.image_lookup._scan_image_stem_map",
            side_effect=counting_scan,
        ):
            rebuilt = build_image_stem_map_impl(self.root, recursive=False)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(set(rebuilt or {}), {"a", "b"})

    def test_entry_count_mismatch_forces_rescan(self) -> None:
        """Google Drive often keeps dir mtime stable while files change — count must invalidate."""
        self._touch("a.png")
        build_image_stem_map_impl(self.root, recursive=False)
        clear_stem_map_caches()
        # Add a file without changing directory mtime (simulate Drive sync).
        self._touch("b.png")
        dir_stat = self.root.stat()
        os.utime(self.root, ns=(dir_stat.st_atime_ns, dir_stat.st_mtime_ns))
        calls = {"n": 0}
        real_scan = _scan_image_stem_map

        def counting_scan(root, *, recursive=False):
            calls["n"] += 1
            return real_scan(root, recursive=recursive)

        with patch(
            "scripts.pipeline_generate_packing_list_pdf.image_lookup._scan_image_stem_map",
            side_effect=counting_scan,
        ):
            rebuilt = build_image_stem_map_impl(self.root, recursive=False)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(set(rebuilt or {}), {"a", "b"})

    def test_none_and_missing_dir(self) -> None:
        self.assertIsNone(build_image_stem_map_impl(None, recursive=False))
        self.assertIsNone(build_image_stem_map_impl(self.root / "nope", recursive=False))


if __name__ == "__main__":
    unittest.main()
