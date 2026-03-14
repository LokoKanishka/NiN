from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_snapshot_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def write_shadow_snapshot(*, snapshot_dir: Path, payload: dict[str, Any], intent_id: str) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    checksum = compute_snapshot_checksum(payload)
    path = snapshot_dir / f"snapshot__shadow__{intent_id}__{checksum[:12]}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

