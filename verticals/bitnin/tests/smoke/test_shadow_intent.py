from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent, expire_intent
from verticals.bitnin.tests.conftest import load_fixture


def test_build_shadow_intent_from_analysis():
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    assert intent["action"] == "no_trade"
    assert intent["mode"] == "shadow"
    assert intent["status"] == "open"
    assert intent["approved"] is False


def test_expire_intent_marks_expired_after_valid_until():
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    expired = expire_intent(intent, as_of="2026-03-15T00:00:00.000Z")
    assert expired["status"] == "expired"

