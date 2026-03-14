from verticals.bitnin.services.bitnin_hitl.approval import build_approval_request
from verticals.bitnin.services.bitnin_hitl.telegram_message import build_telegram_approval_message
from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent
from verticals.bitnin.tests.conftest import load_fixture


def test_hitl_approval_request_builds_expected_payload():
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    approval = build_approval_request(intent=intent, shadow_ref="/tmp/intent.json", timestamp="2026-03-13T23:00:00.000Z")
    message = build_telegram_approval_message(approval=approval, intent=intent, analysis=analysis)
    assert approval["status"] == "awaiting_human_approval"
    assert approval["channel"] == "telegram_webhook"
    assert "/bitnin_aprobar" in message

