from verticals.bitnin.services.bitnin_episode_builder.triggers import detect_trigger_candidates
from verticals.bitnin.tests.conftest import load_fixture


def test_detect_trigger_candidates_hits_return_and_narrative_reinforced():
    market = load_fixture("episode_market_sample.json")
    narrative = load_fixture("episode_narrative_sample.json")

    candidates = detect_trigger_candidates(market, narrative)
    assert candidates
    primary = candidates[0]
    assert "return" in primary.trigger_types
    assert "narrative_reinforced" in primary.trigger_types
