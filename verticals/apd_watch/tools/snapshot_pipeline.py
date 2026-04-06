#!/usr/bin/env python3
"""APD Watch read-only snapshot pipeline (Tramo 2).

Este módulo trabaja con fixtures/entrada manual para cerrar el contrato:
raw -> normalized -> snapshots + manifests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
RUNTIME_DIR = ROOT / "runtime"


@dataclass
class SnapshotArtifacts:
    raw_path: Path
    normalized_path: Path
    raw_manifest_path: Path
    normalized_manifest_path: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = " ".join(text.split())
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def _iso_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        return text
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compute_stable_id(source: str, code: Any, cargo_materia: Any, district: Any, level_modality: Any, school: Any) -> str:
    payload = "|".join(
        [
            _canonical_text(source),
            _canonical_text(code),
            _canonical_text(cargo_materia),
            _canonical_text(district),
            _canonical_text(level_modality),
            _canonical_text(school),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def compute_fingerprint(stable_id: str, status: Any, closing_at: Any) -> str:
    payload = "|".join([stable_id, _canonical_text(status), _canonical_text(closing_at)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_raw_offer(record: dict[str, Any], source: str, source_snapshot_date: str, captured_at_utc: str) -> dict[str, Any]:
    raw_payload = dict(record)
    source_url = raw_payload.get("source_url") or raw_payload.get("url")
    raw_hash = hashlib.sha256(json.dumps(raw_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "source": source,
        "source_snapshot_date": source_snapshot_date,
        "captured_at_utc": captured_at_utc,
        "source_url": source_url,
        "raw_payload": raw_payload,
        "raw_hash": raw_hash,
    }


def normalize_offer(raw_offer: dict[str, Any]) -> dict[str, Any]:
    payload = raw_offer["raw_payload"]
    source = raw_offer["source"]
    code = payload.get("code")
    cargo_materia = payload.get("cargo_materia") or payload.get("cargo") or payload.get("materia") or ""
    district = payload.get("district") or payload.get("distrito") or ""
    level_modality = payload.get("level_modality") or payload.get("nivel_modalidad")
    school = payload.get("school") or payload.get("escuela")
    status = payload.get("status") or payload.get("estado") or "desconocido"
    closing_at = _iso_or_none(payload.get("closing_at") or payload.get("cierre"))
    source_url = raw_offer.get("source_url")

    stable_id = compute_stable_id(source, code, cargo_materia, district, level_modality, school)
    fingerprint = compute_fingerprint(stable_id, status, closing_at)

    return {
        "stable_id": stable_id,
        "source": source,
        "source_snapshot_date": raw_offer["source_snapshot_date"],
        "captured_at_utc": raw_offer["captured_at_utc"],
        "normalized_at_utc": _utc_now_iso(),
        "code": code,
        "cargo_materia": cargo_materia,
        "district": district,
        "level_modality": level_modality,
        "school": school,
        "status": status,
        "closing_at": closing_at,
        "fingerprint": fingerprint,
        "source_url": source_url,
    }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _load_schema_required(schema_name: str) -> list[str]:
    schema = load_json(SCHEMAS_DIR / schema_name)
    return list(schema.get("required", []))


def _validate_required_fields(records: list[dict[str, Any]], required_fields: list[str], label: str) -> None:
    for idx, item in enumerate(records):
        missing = [key for key in required_fields if key not in item or item[key] in (None, "") and key not in {"closing_at", "code", "level_modality", "school", "source_url"}]
        if missing:
            raise ValueError(f"{label}[{idx}] missing required fields: {missing}")


def build_snapshot_manifests(records: list[dict[str, Any]], *, source: str, source_snapshot_date: str, created_at_utc: str) -> dict[str, Any]:
    aggregate_hash = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "source": source,
        "source_snapshot_date": source_snapshot_date,
        "created_at_utc": created_at_utc,
        "offers_count": len(records),
        "aggregate_hash": aggregate_hash,
    }


def run_pipeline(input_path: Path, source: str, source_snapshot_date: str) -> SnapshotArtifacts:
    captured_at_utc = _utc_now_iso()
    records: list[dict[str, Any]] = load_json(input_path)

    raw_offers = [build_raw_offer(record, source=source, source_snapshot_date=source_snapshot_date, captured_at_utc=captured_at_utc) for record in records]
    normalized_offers = [normalize_offer(item) for item in raw_offers]

    _validate_required_fields(raw_offers, _load_schema_required("offer_raw.schema.json"), "raw")
    _validate_required_fields(normalized_offers, _load_schema_required("offer_normalized.schema.json"), "normalized")

    stamp = source_snapshot_date.replace("-", "")
    raw_path = RUNTIME_DIR / "snapshots" / f"apd_raw_{stamp}.json"
    normalized_path = RUNTIME_DIR / "normalized" / f"apd_normalized_{stamp}.json"
    raw_manifest_path = RUNTIME_DIR / "snapshots" / f"apd_raw_manifest_{stamp}.json"
    normalized_manifest_path = RUNTIME_DIR / "normalized" / f"apd_normalized_manifest_{stamp}.json"

    write_json(raw_path, raw_offers)
    write_json(normalized_path, normalized_offers)
    write_json(
        raw_manifest_path,
        build_snapshot_manifests(raw_offers, source=source, source_snapshot_date=source_snapshot_date, created_at_utc=captured_at_utc),
    )
    write_json(
        normalized_manifest_path,
        build_snapshot_manifests(normalized_offers, source=source, source_snapshot_date=source_snapshot_date, created_at_utc=captured_at_utc),
    )

    return SnapshotArtifacts(
        raw_path=raw_path,
        normalized_path=normalized_path,
        raw_manifest_path=raw_manifest_path,
        normalized_manifest_path=normalized_manifest_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera snapshot raw/normalized read-only desde un fixture APD.")
    parser.add_argument("--input", type=Path, default=ROOT / "tests" / "fixtures" / "apd_offers_sample.json")
    parser.add_argument("--source", default="apd_fixture")
    parser.add_argument("--date", dest="source_snapshot_date", required=True, help="Fecha snapshot YYYY-MM-DD")
    args = parser.parse_args()

    artifacts = run_pipeline(args.input, source=args.source, source_snapshot_date=args.source_snapshot_date)
    print(json.dumps({
        "raw_path": str(artifacts.raw_path),
        "normalized_path": str(artifacts.normalized_path),
        "raw_manifest_path": str(artifacts.raw_manifest_path),
        "normalized_manifest_path": str(artifacts.normalized_manifest_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
