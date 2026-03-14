from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def compute_content_checksum(records: list[dict[str, Any]]) -> str:
    ordered_records = sorted(records, key=lambda item: (item["symbol"], item["interval"], item["open_time"]))
    return hashlib.sha256(_stable_json_dumps(ordered_records).encode("utf-8")).hexdigest()


def write_snapshot(
    *,
    snapshot_dir: Path,
    dataset_version: str,
    source: str,
    symbol: str,
    interval: str,
    records: list[dict[str, Any]],
    validation_report: dict[str, Any],
) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    checksum = compute_content_checksum(records)
    snapshot_name = f"snapshot__{source}__{symbol}__{interval}__{dataset_version}__{checksum[:12]}.json"
    snapshot_path = snapshot_dir / snapshot_name

    ordered_records = sorted(records, key=lambda item: (item["symbol"], item["interval"], item["open_time"]))
    payload = {
        "snapshot_id": snapshot_name.removesuffix(".json"),
        "dataset_version": dataset_version,
        "source": source,
        "symbol": symbol,
        "interval": interval,
        "record_count": len(ordered_records),
        "content_checksum": checksum,
        "validation_summary": {
            "valid": validation_report["valid"],
            "schema_errors": len(validation_report["schema_errors"]),
            "duplicates": len(validation_report["duplicates"]),
            "gaps": len(validation_report["gaps"]),
            "price_errors": len(validation_report["price_errors"]),
            "timestamp_errors": len(validation_report["timestamp_errors"]),
        },
        "records": ordered_records,
    }

    snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot_path
