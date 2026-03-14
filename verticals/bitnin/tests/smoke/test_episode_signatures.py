from verticals.bitnin.services.bitnin_episode_builder.signatures import build_market_signature, build_narrative_signature
from verticals.bitnin.tests.conftest import load_fixture


def test_build_market_signature():
    market = load_fixture("episode_market_sample.json")
    signature = build_market_signature(
        bars=market,
        trigger_index=4,
        pre_bars=market[1:4],
    )
    assert signature["interval"] == "1d"
    assert signature["breakout"] is True
    assert signature["volume_anomaly"] is True


def test_build_narrative_signature():
    narrative = load_fixture("episode_narrative_sample.json")
    signature = build_narrative_signature(narrative[:2])
    assert signature["event_count"] == 2
    assert signature["dominant_cause"] in {"etf_institucional", "regulacion"}
