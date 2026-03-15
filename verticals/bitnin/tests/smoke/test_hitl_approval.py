import json
from pathlib import Path
from unittest.mock import patch
from verticals.bitnin.services.bitnin_hitl.approval import build_approval_request
from verticals.bitnin.services.bitnin_hitl.telegram_message import build_telegram_approval_message
from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent
from verticals.bitnin.tests.conftest import load_fixture

def test_hitl_approval_request_builds_expected_payload():
    # Use shadow_analysis_sample.json
    analysis = load_fixture("shadow_analysis_sample.json")
    intent = build_shadow_intent(analysis=analysis, reasoning_ref="/tmp/analysis.json")
    
    with patch("verticals.bitnin.services.bitnin_hitl.approval.build_approval_request") as mock_build:
        mock_build.return_value = {
            "approval_id": "app_123",
            "status": "pending",
            "channel": "telegram_webhook",
            "expires_at": "3000-01-01T00:00:00Z"
        }
        approval = build_approval_request(intent=intent, shadow_ref="/tmp/intent.json", timestamp="2026-03-13T23:00:00.000Z", expires_at="3000-01-01T00:00:00Z")
        
    message = build_telegram_approval_message(approval=approval, intent=intent, analysis=analysis)
    
    assert approval["status"] == "pending"
    assert approval["expires_at"] == "3000-01-01T00:00:00Z"
    assert "Request" in message
