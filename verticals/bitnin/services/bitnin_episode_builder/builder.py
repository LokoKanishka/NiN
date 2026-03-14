from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_episode_builder.merge import merge_episode  # type: ignore
    from verticals.bitnin.services.bitnin_episode_builder.snapshot import write_snapshot  # type: ignore
    from verticals.bitnin.services.bitnin_episode_builder.triggers import detect_trigger_candidates  # type: ignore
    from verticals.bitnin.services.bitnin_episode_builder.windows import build_episode_window  # type: ignore
else:
    from .merge import merge_episode
    from .snapshot import write_snapshot
    from .triggers import detect_trigger_candidates
    from .windows import build_episode_window


BITNIN_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = BITNIN_ROOT / "runtime"
RAW_ROOT = RUNTIME_ROOT / "datasets" / "episodes" / "raw"
NORMALIZED_ROOT = RUNTIME_ROOT / "datasets" / "episodes" / "normalized"
SNAPSHOT_ROOT = RUNTIME_ROOT / "datasets" / "episodes" / "snapshots"
LOG_ROOT = RUNTIME_ROOT / "logs"
EPISODE_SCHEMA_PATH = BITNIN_ROOT / "SCHEMAS" / "episode.schema.json"


class EpisodeDatasetBuilder:
    def __init__(self) -> None:
        for path in (RAW_ROOT, NORMALIZED_ROOT, SNAPSHOT_ROOT, LOG_ROOT):
            path.mkdir(parents=True, exist_ok=True)
        self.validator = Draft202012Validator(json.loads(EPISODE_SCHEMA_PATH.read_text(encoding="utf-8")))

    def build(
        self,
        *,
        dataset_version: str,
        market_path: str,
        narrative_path: str | None = None,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        pre_bars: int = 3,
        post_bars: int = 7,
    ) -> dict[str, Any]:
        market_bars = self._read_jsonl(Path(market_path))
        narrative_events = self._read_jsonl(Path(narrative_path)) if narrative_path else []

        filtered_market = [
            bar for bar in market_bars if bar.get("symbol") == symbol and bar.get("interval") == interval
        ]
        candidates = detect_trigger_candidates(filtered_market, narrative_events)
        market_source_ref = Path(market_path).name
        narrative_source_ref = Path(narrative_path).name if narrative_path else "narrative:none"

        raw_candidates_path = RAW_ROOT / f"episode_candidates__{symbol}__{interval}__{dataset_version}.json"
        raw_candidates_path.write_text(
            json.dumps(
                [
                    {
                        "index": candidate.index,
                        "trigger_types": list(candidate.trigger_types),
                        "trigger_strength": candidate.trigger_strength,
                        "nearby_narrative_ids": list(candidate.nearby_narrative_ids),
                    }
                    for candidate in candidates
                ],
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        episodes: list[dict[str, Any]] = []
        for candidate in candidates:
            window = build_episode_window(
                total_bars=len(filtered_market),
                trigger_index=candidate.index,
                pre_bars=pre_bars,
                event_bars=1,
                post_bars=post_bars,
            )
            episode = merge_episode(
                market_bars=filtered_market,
                narrative_events=narrative_events,
                trigger_index=candidate.index,
                trigger_types=list(candidate.trigger_types),
                trigger_strength=candidate.trigger_strength,
                window=window,
                dataset_version=dataset_version,
                market_source_ref=market_source_ref,
                narrative_source_ref=narrative_source_ref,
            )
            if episode["status"] == "discarded":
                continue
            episodes.append(episode)

        episodes = self._dedupe_by_id(episodes)
        validation = self._validate_episodes(episodes)
        if not validation["valid"]:
            raise ValueError(json.dumps(validation, indent=2, ensure_ascii=False))

        normalized_path = NORMALIZED_ROOT / f"episodes__{symbol}__{interval}__{dataset_version}.jsonl"
        self._write_jsonl(normalized_path, episodes)
        snapshot_path = write_snapshot(
            snapshot_dir=SNAPSHOT_ROOT,
            dataset_version=dataset_version,
            source_slug=f"{symbol}__{interval}",
            episodes=episodes,
            validation_report={
                "valid": validation["valid"],
                "record_count": validation["record_count"],
                "schema_errors": len(validation["schema_errors"]),
                "duplicate_episode_ids": len(validation["duplicate_episode_ids"]),
            },
        )
        log_path = LOG_ROOT / f"bitnin_episode_builder__{symbol}__{interval}__{dataset_version}.json"
        log_path.write_text(
            json.dumps(
                {
                    "dataset_version": dataset_version,
                    "market_path": market_path,
                    "narrative_path": narrative_path,
                    "symbol": symbol,
                    "interval": interval,
                    "candidate_count": len(candidates),
                    "episode_count": len(episodes),
                    "raw_candidates_path": str(raw_candidates_path),
                    "normalized_path": str(normalized_path),
                    "snapshot_path": str(snapshot_path),
                    "validation": validation,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return {
            "dataset_version": dataset_version,
            "symbol": symbol,
            "interval": interval,
            "candidate_count": len(candidates),
            "episode_count": len(episodes),
            "raw_path": str(raw_candidates_path),
            "normalized_path": str(normalized_path),
            "snapshot_path": str(snapshot_path),
            "log_path": str(log_path),
            "validation": validation,
        }

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        if content.startswith("["):
            payload = json.loads(content)
            if not isinstance(payload, list):
                raise ValueError(f"Expected list payload in {path}")
            return payload
        return [json.loads(line) for line in content.splitlines() if line.strip()]

    def _write_jsonl(self, path: Path, rows: list[dict[str, Any]]) -> None:
        lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _dedupe_by_id(self, episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: dict[str, dict[str, Any]] = {}
        for episode in episodes:
            unique[episode["episode_id"]] = episode
        return sorted(unique.values(), key=lambda item: (item["window_start"], item["episode_id"]))

    def _validate_episodes(self, episodes: list[dict[str, Any]]) -> dict[str, Any]:
        schema_errors: list[dict[str, Any]] = []
        duplicate_ids: dict[str, int] = {}
        counter: dict[str, int] = {}

        for index, episode in enumerate(episodes):
            counter[episode["episode_id"]] = counter.get(episode["episode_id"], 0) + 1
            errors = [error.message for error in self.validator.iter_errors(episode)]
            if errors:
                schema_errors.append({"index": index, "errors": sorted(errors)})

        duplicate_ids = {key: value for key, value in counter.items() if value > 1}
        return {
            "valid": not schema_errors and not duplicate_ids,
            "record_count": len(episodes),
            "schema_errors": schema_errors,
            "duplicate_episode_ids": duplicate_ids,
        }


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin episode builder")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--market-path", required=True)
    parser.add_argument("--narrative-path")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--pre-bars", type=int, default=3)
    parser.add_argument("--post-bars", type=int, default=7)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    builder = EpisodeDatasetBuilder()
    result = builder.build(
        dataset_version=args.dataset_version,
        market_path=args.market_path,
        narrative_path=args.narrative_path,
        symbol=args.symbol,
        interval=args.interval,
        pre_bars=args.pre_bars,
        post_bars=args.post_bars,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
