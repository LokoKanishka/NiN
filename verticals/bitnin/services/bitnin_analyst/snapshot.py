from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_snapshot_checksum(analysis: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(analysis).encode("utf-8")).hexdigest()


def write_snapshot(
    *,
    snapshot_dir: Path,
    analysis: dict[str, Any],
    raw_ref: str,
    normalized_ref: str,
) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    checksum = compute_snapshot_checksum(analysis)
    snapshot_name = f"snapshot__analysis__{analysis['analysis_id']}__{checksum[:12]}.json"
    snapshot_path = snapshot_dir / snapshot_name
    payload = {
        "snapshot_id": snapshot_name.removesuffix(".json"),
        "analysis_id": analysis["analysis_id"],
        "timestamp": analysis["timestamp"],
        "content_checksum": checksum,
        "raw_ref": raw_ref,
        "normalized_ref": normalized_ref,
        "analysis": analysis,
    }
    snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_path

