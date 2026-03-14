import json
from pathlib import Path

from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent
from verticals.bitnin.services.bitnin_shadow.review import build_shadow_review
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_shadow_review_marks_abstention_reasonable(tmp_path):
    market_path = tmp_path / "market.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    review = build_shadow_review(intent=intent, analysis=analysis, market_path=market_path)
    assert review["suggested_action"] == "no_trade"
    assert review["abstention_reasonable"] is True

