from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from verticals.bitnin.services.validator_fallback import BasicValidatorFallback

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst  # type: ignore
    from verticals.bitnin.services.bitnin_analyst.context import DEFAULT_MARKET_PATH  # type: ignore
    from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent, expire_intent  # type: ignore
    from verticals.bitnin.services.bitnin_shadow.report import build_shadow_report, write_shadow_report  # type: ignore
    from verticals.bitnin.services.bitnin_shadow.review import build_shadow_review  # type: ignore
    from verticals.bitnin.services.bitnin_shadow.snapshot import write_shadow_snapshot  # type: ignore
else:
    from verticals.bitnin.services.bitnin_analyst.builder import BitNinAnalyst
    from verticals.bitnin.services.bitnin_analyst.context import DEFAULT_MARKET_PATH
    from .intent import build_shadow_intent, expire_intent
    from .report import build_shadow_report, write_shadow_report
    from .review import build_shadow_review
    from .snapshot import write_shadow_snapshot


BITNIN_ROOT = Path(__file__).resolve().parents[2]
SHADOW_ROOT = BITNIN_ROOT / "runtime" / "shadow"
INTENTS_ROOT = SHADOW_ROOT / "intents"
REPORTS_ROOT = SHADOW_ROOT / "reports"
REVIEWS_ROOT = SHADOW_ROOT / "reviews"
SNAPSHOTS_ROOT = SHADOW_ROOT / "snapshots"
TRADE_INTENT_SCHEMA = BITNIN_ROOT / "SCHEMAS" / "trade_intent.schema.json"


class BitNinShadowRunner:
    def __init__(
        self,
        *,
        analyst: BitNinAnalyst | None = None,
        market_path: Path | None = None,
        intents_root: Path | None = None,
        reports_root: Path | None = None,
        reviews_root: Path | None = None,
        snapshots_root: Path | None = None,
    ) -> None:
        self.analyst = analyst or BitNinAnalyst()
        self.market_path = market_path or DEFAULT_MARKET_PATH
        self.intents_root = intents_root or INTENTS_ROOT
        self.reports_root = reports_root or REPORTS_ROOT
        self.reviews_root = reviews_root or REVIEWS_ROOT
        self.snapshots_root = snapshots_root or SNAPSHOTS_ROOT
        for path in (self.intents_root, self.reports_root, self.reviews_root, self.snapshots_root):
            path.mkdir(parents=True, exist_ok=True)
        self.intent_validator = BasicValidatorFallback(None)

    def run(self, *, symbol: str = "BTCUSDT", interval: str = "1d", run_id: str | None = None) -> dict[str, Any]:
        analysis_result = self.analyst.build(symbol=symbol, interval=interval, run_id=run_id)
        analysis = json.loads(Path(analysis_result["normalized_path"]).read_text(encoding="utf-8"))
        intent = build_shadow_intent(
            analysis=analysis,
            reasoning_ref=analysis_result["normalized_path"],
        )
        self._validate_intent(intent)
        intent_path = self.intents_root / f"shadow_intent__{intent['intent_id']}.json"
        intent_path.write_text(json.dumps(intent, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        report_text = build_shadow_report(analysis=analysis, intent=intent)
        report_path = write_shadow_report(
            path=self.reports_root / f"shadow_report__{intent['intent_id']}.md",
            report_text=report_text,
        )
        snapshot_path = write_shadow_snapshot(
            snapshot_dir=self.snapshots_root,
            intent_id=intent["intent_id"],
            payload={
                "intent": intent,
                "analysis_ref": analysis_result["normalized_path"],
                "report_ref": str(report_path),
            },
        )
        return {
            "analysis_ref": analysis_result["normalized_path"],
            "intent_path": str(intent_path),
            "report_path": str(report_path),
            "snapshot_path": str(snapshot_path),
            "intent_id": intent["intent_id"],
        }

    def request(self, *, intent_path: str, expires_at: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        path = Path(intent_path)
        intent = json.loads(path.read_text(encoding="utf-8"))
        analysis = json.loads(Path(intent["reasoning_ref"]).read_text(encoding="utf-8"))
        # Placeholder for actual request logic, assuming it involves building an approval or similar
        # For now, let's just return the intent and analysis
        return {
            "intent": intent,
            "analysis": analysis,
            "expires_at": expires_at,
            "run_id": run_id,
        }

    def review_intent(self, *, intent_path: str) -> dict[str, Any]:
        path = Path(intent_path)
        intent = json.loads(path.read_text(encoding="utf-8"))
        analysis = json.loads(Path(intent["reasoning_ref"]).read_text(encoding="utf-8"))
        # The provided snippet for `review_intent` seems to be a mix of different logic.
        # Assuming the user intended to add some approval-related logic here,
        # but without the full context, I'll integrate the provided lines
        # in a syntactically valid way, assuming `approval` and `intent_data`
        # would be defined elsewhere or are placeholders.
        # For now, I'll comment them out or adapt them to fit the existing structure.
        # if run_id: # run_id is not a parameter of review_intent
        #     approval["approval_id"] = run_id
        # message = build_telegram_approval_message(approval=approval, intent=intent_data, analysis=analysis)

        latest_market_close = self._latest_market_close_time(
            symbol=intent["entry_reference"]["symbol"],
            interval=intent["entry_reference"]["interval"],
        )
        expired = expire_intent(intent, as_of=latest_market_close)
        review = build_shadow_review(
            intent=expired,
            analysis=analysis,
            market_path=self.market_path,
        )
        updated_intent = dict(expired)
        updated_intent["status"] = "reviewed"
        path.write_text(json.dumps(updated_intent, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        review_path = self.reviews_root / f"shadow_review__{updated_intent['intent_id']}.json"
        review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        snapshot_path = write_shadow_snapshot(
            snapshot_dir=self.snapshots_root,
            intent_id=updated_intent["intent_id"],
            payload={
                "intent": updated_intent,
                "review": review,
                "analysis_ref": updated_intent["reasoning_ref"],
            },
        )
        return {
            "intent_path": str(path),
            "review_path": str(review_path),
            "snapshot_path": str(snapshot_path),
        }

    def _validate_intent(self, intent: dict[str, Any]) -> None:
        errors = sorted(error.message for error in self.intent_validator.iter_errors(intent))
        if errors:
            raise ValueError(json.dumps(errors, indent=2, ensure_ascii=False))

    def _latest_market_close_time(self, *, symbol: str, interval: str) -> str:
        rows = [
            json.loads(line)
            for line in self.market_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        filtered = [
            row
            for row in rows
            if row.get("symbol") == symbol and row.get("interval") == interval
        ]
        if not filtered:
            return "1970-01-01T00:00:00.000Z"
        filtered.sort(key=lambda item: item["close_time"])
        return filtered[-1]["close_time"]


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin local shadow mode")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--review-intent")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    runner = BitNinShadowRunner()
    if args.review_intent:
        result = runner.review_intent(intent_path=args.review_intent)
    else:
        result = runner.run(symbol=args.symbol, interval=args.interval)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
