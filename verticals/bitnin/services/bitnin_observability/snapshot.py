from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class Snapshorter:
    """Captures and verifies state snapshots."""

    def __init__(self, snapshots_dir: Path):
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _stable_json(self, payload: Any) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def compute_checksum(self, payload: dict[str, Any]) -> str:
        return hashlib.sha256(self._stable_json(payload).encode("utf-8")).hexdigest()

    def write_snapshot(self, payload: dict[str, Any], context_id: str) -> Path:
        checksum = self.compute_checksum(payload)
        snapshot_path = self.snapshots_dir / f"snapshot_{context_id}_{checksum[:12]}.json"
        snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return snapshot_path
