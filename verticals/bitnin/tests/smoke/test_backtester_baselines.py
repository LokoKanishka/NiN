from verticals.bitnin.services.bitnin_backtester.baselines import abstention_baseline, buy_and_hold_baseline


def test_buy_and_hold_baseline_uses_period_prices():
    decisions = [
        {
            "entry_reference": {"close": 100.0},
            "outcome": {"evaluation_end_close": 105.0},
        },
        {
            "entry_reference": {"close": 103.0},
            "outcome": {"evaluation_end_close": 110.0},
        },
    ]
    baseline = buy_and_hold_baseline(decisions)
    assert baseline["return"] == 0.1


def test_abstention_baseline_is_zero():
    baseline = abstention_baseline([{"x": 1}, {"x": 2}])
    assert baseline["return"] == 0.0
    assert baseline["decision_count"] == 2

