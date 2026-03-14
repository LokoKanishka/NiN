from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.context import DEFAULT_MARKET_PATH  # type: ignore
    from verticals.bitnin.services.bitnin_backtester.baselines import (  # type: ignore
        abstention_baseline,
        buy_and_hold_baseline,
        return_signal_baseline,
    )
    from verticals.bitnin.services.bitnin_backtester.metrics import compute_metrics  # type: ignore
    from verticals.bitnin.services.bitnin_backtester.replay import build_replay_points, read_market_bars  # type: ignore
    from verticals.bitnin.services.bitnin_backtester.review import review_decision  # type: ignore
    from verticals.bitnin.services.bitnin_backtester.simulator import simulate_decision  # type: ignore
    from verticals.bitnin.services.bitnin_backtester.snapshot import write_snapshot  # type: ignore
else:
    from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst
    from verticals.bitnin.services.bitnin_analyst.context import DEFAULT_MARKET_PATH
    from .baselines import abstention_baseline, buy_and_hold_baseline, return_signal_baseline
    from .metrics import compute_metrics
    from .replay import build_replay_points, read_market_bars
    from .review import review_decision
    from .simulator import simulate_decision
    from .snapshot import write_snapshot


BITNIN_ROOT = Path(__file__).resolve().parents[2]
BACKTEST_ROOT = BITNIN_ROOT / "runtime" / "backtests"
RUNS_ROOT = BACKTEST_ROOT / "runs"
REPORTS_ROOT = BACKTEST_ROOT / "reports"
REPLAYS_ROOT = BACKTEST_ROOT / "replays"
SNAPSHOT_ROOT = BACKTEST_ROOT / "snapshots"

BACKTEST_RUN_SCHEMA = BITNIN_ROOT / "SCHEMAS" / "backtest_run.schema.json"
BACKTEST_DECISION_SCHEMA = BITNIN_ROOT / "SCHEMAS" / "backtest_decision.schema.json"
BACKTEST_REPORT_SCHEMA = BITNIN_ROOT / "SCHEMAS" / "backtest_report.schema.json"


def _load_validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")), format_checker=Draft202012Validator.FORMAT_CHECKER)


def _stable_run_id(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


class BitNinBacktester:
    def __init__(
        self,
        *,
        analyst: BitNinAnalyst | None = None,
        market_path: Path | None = None,
        runs_root: Path | None = None,
        reports_root: Path | None = None,
        replays_root: Path | None = None,
        snapshot_root: Path | None = None,
    ) -> None:
        self.market_path = market_path or DEFAULT_MARKET_PATH
        self.runs_root = runs_root or RUNS_ROOT
        self.reports_root = reports_root or REPORTS_ROOT
        self.replays_root = replays_root or REPLAYS_ROOT
        self.snapshot_root = snapshot_root or SNAPSHOT_ROOT
        for path in (self.runs_root, self.reports_root, self.replays_root, self.snapshot_root):
            path.mkdir(parents=True, exist_ok=True)
        self.analyst = analyst
        self.run_validator = _load_validator(BACKTEST_RUN_SCHEMA)
        self.decision_validator = _load_validator(BACKTEST_DECISION_SCHEMA)
        self.report_validator = _load_validator(BACKTEST_REPORT_SCHEMA)

    def run(
        self,
        *,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        warmup_bars: int = 8,
        max_steps: int = 10,
        evaluation_bars: int = 1,
        cost_bps: float = 5.0,
        slippage_bps: float = 5.0,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        replay_points = build_replay_points(
            market_path=self.market_path,
            symbol=symbol,
            interval=interval,
            warmup_bars=warmup_bars,
            start=start,
            end=end,
            max_steps=max_steps,
        )
        if not replay_points:
            raise ValueError("Replay produced no points")
        market_bars = read_market_bars(market_path=self.market_path, symbol=symbol, interval=interval)
        run_id = _stable_run_id(
            {
                "symbol": symbol,
                "interval": interval,
                "replay_start": replay_points[0]["timestamp"],
                "replay_end": replay_points[-1]["timestamp"],
                "step_count": len(replay_points),
                "evaluation_bars": evaluation_bars,
                "cost_bps": cost_bps,
                "slippage_bps": slippage_bps,
            }
        )
        analyst = self.analyst or BitNinAnalyst(
            raw_root=self.replays_root / run_id / "analyst" / "raw",
            normalized_root=self.replays_root / run_id / "analyst" / "normalized",
            snapshot_root=self.replays_root / run_id / "analyst" / "snapshots",
        )
        replay_entries = []
        for point in replay_points:
            analyst_result = analyst.build(
                symbol=symbol,
                interval=interval,
                as_of=point["timestamp"],
            )
            analysis = json.loads(Path(analyst_result["normalized_path"]).read_text(encoding="utf-8"))
            future_bars = market_bars[point["index"] + 1 : point["index"] + 1 + evaluation_bars]
            decision = simulate_decision(
                run_id=run_id,
                analysis=analysis,
                analysis_ref=analyst_result["normalized_path"],
                current_bar=point["bar"],
                future_bars=future_bars,
                evaluation_bars=evaluation_bars,
                cost_bps=cost_bps,
                slippage_bps=slippage_bps,
            )
            review = review_decision(decision)
            replay_entries.append({"decision": decision, "review": review})

        decisions = [item["decision"] for item in replay_entries]
        self._validate_documents(decisions, self.decision_validator, "backtest_decision")
        run_payload = {
            "run_id": run_id,
            "symbol": symbol,
            "interval": interval,
            "replay_start": replay_points[0]["timestamp"],
            "replay_end": replay_points[-1]["timestamp"],
            "step_count": len(replay_points),
            "dataset_versions": decisions[-1]["dataset_versions"],
        }
        self._validate_documents([run_payload], self.run_validator, "backtest_run")

        metrics = compute_metrics(decisions)
        baselines = {
            "buy_and_hold": buy_and_hold_baseline(decisions),
            "abstention": abstention_baseline(decisions),
            "return_signal": return_signal_baseline(decisions),
        }
        report_payload = {
            "run_id": run_id,
            "metrics": metrics,
            "baselines": baselines,
            "success_definition": [
                "No usar informacion futura en el analisis del mismo tick.",
                "Medir prudencia, cobertura y consistencia entre runs comparables.",
                "Mantener point-in-time replay reproducible.",
            ],
            "non_claims": [
                "No demuestra capacidad de trading real.",
                "No autoriza ejecucion financiera.",
                "No implica calibracion optima de thresholds ni de prompts.",
            ],
        }
        self._validate_documents([report_payload], self.report_validator, "backtest_report")

        replay_path = self.replays_root / f"replay__{run_id}.jsonl"
        replay_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in replay_entries) + "\n",
            encoding="utf-8",
        )
        run_path = self.runs_root / f"backtest_run__{run_id}.json"
        run_path.write_text(json.dumps(run_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report_path = self.reports_root / f"backtest_report__{run_id}.json"
        report_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        snapshot_payload = {
            "run": run_payload,
            "report": report_payload,
            "replay_ref": str(replay_path),
            "decision_count": len(decisions),
        }
        snapshot_path = write_snapshot(snapshot_dir=self.snapshot_root, payload=snapshot_payload, run_id=run_id)

        return {
            "run_id": run_id,
            "run_path": str(run_path),
            "report_path": str(report_path),
            "replay_path": str(replay_path),
            "snapshot_path": str(snapshot_path),
            "metrics": metrics,
            "baselines": baselines,
        }

    def _validate_documents(self, docs: list[dict[str, Any]], validator: Draft202012Validator, label: str) -> None:
        errors = []
        for index, doc in enumerate(docs):
            doc_errors = [error.message for error in validator.iter_errors(doc)]
            if doc_errors:
                errors.append({"index": index, "label": label, "errors": sorted(doc_errors)})
        if errors:
            raise ValueError(json.dumps(errors, indent=2, ensure_ascii=False))


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin point-in-time backtester")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--warmup-bars", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--evaluation-bars", type=int, default=1)
    parser.add_argument("--cost-bps", type=float, default=5.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    result = BitNinBacktester().run(
        symbol=args.symbol,
        interval=args.interval,
        warmup_bars=args.warmup_bars,
        max_steps=args.max_steps,
        evaluation_bars=args.evaluation_bars,
        cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
        start=args.start,
        end=args.end,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

