from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_snapshot_checksum(episodes: list[dict[str, Any]]) -> str:
    ordered = sorted(episodes, key=lambda item: (item["window_start"], item["episode_id"]))
    return hashlib.sha256(_stable_json(ordered).encode("utf-8")).hexdigest()


def write_snapshot(
    *,
    snapshot_dir: Path,
    dataset_version: str,
    source_slug: str,
    episodes: list[dict[str, Any]],
    validation_report: dict[str, Any],
) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    checksum = compute_snapshot_checksum(episodes)
    snapshot_name = f"snapshot__episodes__{source_slug}__{dataset_version}__{checksum[:12]}.json"
    snapshot_path = snapshot_dir / snapshot_name
    ordered = sorted(episodes, key=lambda item: (item["window_start"], item["episode_id"]))
    payload = {
        "snapshot_id": snapshot_name.removesuffix(".json"),
        "dataset_version": dataset_version,
        "source_slug": source_slug,
        "record_count": len(ordered),
        "content_checksum": checksum,
        "validation_summary": validation_report,
        "episodes": ordered,
    }
    snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_path
