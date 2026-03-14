from verticals.bitnin.services.bitnin_episode_builder.outcomes import build_outcome
from verticals.bitnin.tests.conftest import load_fixture


def test_build_outcome():
    market = load_fixture("episode_market_sample.json")
    outcome = build_outcome(market, 4)
    assert isinstance(outcome["forward_return_1d"], float)
    assert isinstance(outcome["forward_return_7d"], float)
    assert outcome["forward_return_30d"] == "insufficient_horizon"
