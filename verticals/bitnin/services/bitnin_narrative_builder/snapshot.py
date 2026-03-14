from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_snapshot_checksum(events: list[dict[str, Any]]) -> str:
    ordered = sorted(events, key=lambda item: (item["timestamp_start"], item["event_id"]))
    return hashlib.sha256(_stable_json(ordered).encode("utf-8")).hexdigest()


def write_snapshot(
    *,
    snapshot_dir: Path,
    dataset_version: str,
    source: str,
    query_slug: str,
    events: list[dict[str, Any]],
    validation_report: dict[str, Any],
) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    checksum = compute_snapshot_checksum(events)
    snapshot_name = f"snapshot__{source}__{query_slug}__{dataset_version}__{checksum[:12]}.json"
    snapshot_path = snapshot_dir / snapshot_name

    ordered = sorted(events, key=lambda item: (item["timestamp_start"], item["event_id"]))
    payload = {
        "snapshot_id": snapshot_name.removesuffix(".json"),
        "dataset_version": dataset_version,
        "source": source,
        "query_slug": query_slug,
        "record_count": len(ordered),
        "content_checksum": checksum,
        "validation_summary": {
            "valid": validation_report["valid"],
            "schema_errors": len(validation_report["schema_errors"]),
            "timestamp_errors": len(validation_report["timestamp_errors"]),
            "duplicate_event_ids": len(validation_report["duplicate_event_ids"]),
        },
        "events": ordered,
    }
    snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_path
