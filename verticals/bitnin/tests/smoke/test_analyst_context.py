import json
from pathlib import Path

from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_current_context_builder_builds_compact_context(tmp_path):
    market_path = tmp_path / "market.jsonl"
    narrative_path = tmp_path / "narrative.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    _write_jsonl(narrative_path, load_fixture("analyst_narrative_sample.json"))
    _write_jsonl(episodes_path, load_fixture("analyst_episodes_sample.json"))

    builder = CurrentContextBuilder(
        market_path=market_path,
        narrative_path=narrative_path,
        episodes_path=episodes_path,
    )
    context = builder.build(symbol="BTCUSDT", interval="1d")

    assert context["market_state"]["symbol"] == "BTCUSDT"
    assert context["market_state"]["return_7d"] != "insufficient_history"
    assert context["data_coverage_score"] == 1.0
    assert context["narrative_coverage_score"] > 0
    assert context["recent_narrative"]["event_count"] == 2

