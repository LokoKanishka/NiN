from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_narrative_builder.dedupe import dedupe_narrative_events  # type: ignore
    from verticals.bitnin.services.bitnin_narrative_builder.normalize import (  # type: ignore
        normalize_gdelt_articles,
        validate_narrative_events,
    )
    from verticals.bitnin.services.bitnin_narrative_builder.snapshot import write_snapshot  # type: ignore
    from verticals.bitnin.services.bitnin_narrative_builder.sources import (  # type: ignore
        GDELTDocSource,
        RawNarrativeFetchResult,
    )
else:
    from .dedupe import dedupe_narrative_events
    from .normalize import normalize_gdelt_articles, validate_narrative_events
    from .snapshot import write_snapshot
    from .sources import GDELTDocSource, RawNarrativeFetchResult


BITNIN_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = BITNIN_ROOT / "runtime"
RAW_ROOT = RUNTIME_ROOT / "datasets" / "narrative" / "raw"
NORMALIZED_ROOT = RUNTIME_ROOT / "datasets" / "narrative" / "normalized"
SNAPSHOT_ROOT = RUNTIME_ROOT / "datasets" / "narrative" / "snapshots"
LOG_ROOT = RUNTIME_ROOT / "logs"


@dataclass
class NarrativeBuildResult:
    source: str
    dataset_version: str
    mode: str
    query: str
    event_count: int
    raw_path: str
    normalized_path: str
    snapshot_path: str
    log_path: str
    validation: dict[str, Any]


def slugify_query(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "query"


class NarrativeDatasetBuilder:
    def __init__(self) -> None:
        for path in (RAW_ROOT, NORMALIZED_ROOT, SNAPSHOT_ROOT, LOG_ROOT):
            path.mkdir(parents=True, exist_ok=True)

    def build_gdelt(
        self,
        *,
        dataset_version: str,
        mode: str = "full",
        query: str = "bitcoin",
        timespan: str = "1d",
        start: str | None = None,
        end: str | None = None,
        maxrecords: int = 50,
    ) -> NarrativeBuildResult:
        query_slug = slugify_query(query)
        normalized_path = self._normalized_path("gdelt_doc_artlist", query_slug, dataset_version)
        existing_events = self._read_jsonl(normalized_path) if mode == "incremental" else []

        ingestion_error = None
        try:
            raw_result = GDELTDocSource().fetch_articles(
                query=query,
                maxrecords=maxrecords,
                timespan=timespan,
                start=start,
                end=end,
            )
        except Exception as e:
            ingestion_error = str(e)
            self._write_run_log(
                {
                    "action": "build_gdelt",
                    "mode": mode,
                    "dataset_version": dataset_version,
                    "query": query,
                    "query_slug": query_slug,
                    "ingestion_error": ingestion_error,
                    "status": "FAILED"
                }
            )
            raise

        raw_path = self._write_raw(raw_result, query_slug=query_slug)

        fresh_events = normalize_gdelt_articles(raw_result, dataset_version=dataset_version)
        merged = dedupe_narrative_events(existing_events + fresh_events)
        validation = validate_narrative_events(merged)
        if not validation["valid"]:
            raise ValueError(json.dumps(validation, indent=2, ensure_ascii=False))

        self._write_jsonl(normalized_path, merged)
        snapshot_path = write_snapshot(
            snapshot_dir=SNAPSHOT_ROOT,
            dataset_version=dataset_version,
            source=raw_result.source,
            query_slug=query_slug,
            events=merged,
            validation_report=validation,
        )
        log_path = self._write_run_log(
            {
                "action": "build_gdelt",
                "mode": mode,
                "dataset_version": dataset_version,
                "query": query,
                "query_slug": query_slug,
                "raw_path": str(raw_path),
                "normalized_path": str(normalized_path),
                "snapshot_path": str(snapshot_path),
                "validation": validation,
                "request": raw_result.params,
            }
        )
        return NarrativeBuildResult(
            source=raw_result.source,
            dataset_version=dataset_version,
            mode=mode,
            query=query,
            event_count=len(merged),
            raw_path=str(raw_path),
            normalized_path=str(normalized_path),
            snapshot_path=str(snapshot_path),
            log_path=str(log_path),
            validation=validation,
        )

    def _write_raw(self, raw_result: RawNarrativeFetchResult, *, query_slug: str) -> Path:
        filename = f"{raw_result.source}__{query_slug}__{raw_result.requested_at.replace(':', '-')}.json"
        path = RAW_ROOT / filename
        payload = {
            "source": raw_result.source,
            "query": raw_result.query,
            "requested_at": raw_result.requested_at,
            "endpoint": raw_result.endpoint,
            "params": raw_result.params,
            "payload": raw_result.payload,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _write_jsonl(self, path: Path, rows: list[dict[str, Any]]) -> None:
        lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _normalized_path(self, source: str, query_slug: str, dataset_version: str) -> Path:
        return NORMALIZED_ROOT / f"{source}__{query_slug}__{dataset_version}.jsonl"

    def _write_run_log(self, payload: dict[str, Any]) -> Path:
        filename = f"bitnin_narrative_builder__{payload['action']}__{payload['dataset_version']}__{payload['query_slug']}.json"
        path = LOG_ROOT / filename
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin narrative dataset builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gdelt = subparsers.add_parser("gdelt", help="Fetch and build narrative candidates from GDELT DOC 2.0")
    gdelt.add_argument("--dataset-version", required=True)
    gdelt.add_argument("--mode", choices=["full", "incremental"], default="full")
    gdelt.add_argument("--query", default="bitcoin")
    gdelt.add_argument("--timespan", default="1d")
    gdelt.add_argument("--start")
    gdelt.add_argument("--end")
    gdelt.add_argument("--maxrecords", type=int, default=50)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    builder = NarrativeDatasetBuilder()

    if args.command == "gdelt":
        result = builder.build_gdelt(
            dataset_version=args.dataset_version,
            mode=args.mode,
            query=args.query,
            timespan=args.timespan,
            start=args.start,
            end=args.end,
            maxrecords=args.maxrecords,
        )
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
