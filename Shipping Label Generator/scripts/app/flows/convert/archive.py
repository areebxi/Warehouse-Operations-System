from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.app.util.time import utc_compact_timestamp, utc_iso_seconds


MANIFEST_NAME = ".processed_manifest.json"


@dataclass
class Manifest:
    hashes: set[str]

    @classmethod
    def load(cls, processed_dir: Path) -> "Manifest":
        path = processed_dir / MANIFEST_NAME
        if not path.exists():
            return cls(hashes=set())
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        hashes = set(data.get("hashes") or [])
        return cls(hashes=hashes)

    def save(self, processed_dir: Path) -> None:
        processed_dir.mkdir(parents=True, exist_ok=True)
        path = processed_dir / MANIFEST_NAME
        payload = {"hashes": sorted(self.hashes), "updated_at": utc_iso_seconds()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def archive_file(*, src: Path, processed_dir: Path) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    dst = processed_dir / f"{utc_compact_timestamp()}_{src.name}"
    return src.replace(dst)

