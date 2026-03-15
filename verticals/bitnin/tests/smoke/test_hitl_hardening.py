import json
from pathlib import Path
from unittest.mock import patch
from verticals.bitnin.services.bitnin_hitl.builder import BitNinHitlRunner

def test_approval_request_immutability(tmp_path: Path):
    requests_dir = tmp_path / "requests"
    decisions_dir = tmp_path / "decisions"
    snapshots_dir = tmp_path / "snapshots"

    runner = BitNinHitlRunner(
        requests_root=requests_dir,
        decisions_root=decisions_dir,
        snapshots_root=snapshots_dir
    )

    # 1. Create a mock intent
    intent = {
        "intent_id": "test_intent_1",
        "valid_until": "2026-12-31T23:59:59Z",
        "reasoning_ref": "some_ref",
        "action": "long",
        "entry_reference": {"interval": "1h", "symbol": "BTC/USDT"}
    }
    # Mocking reasoning file
    reasoning_file = tmp_path / "analysis.json"
    reasoning_file.write_text(json.dumps({
        "trend": "up",
        "retrieved_episodes": [],
        "confidence": 0.9,
        "risk_level": "low",
        "final_status": "ready",
        "indicator_status": "OK",
        "why_not": ["No blockers"]
    }), encoding="utf-8")
    intent["reasoning_ref"] = str(reasoning_file)

    intent_path = tmp_path / "intent.json"
    intent_path.write_text(json.dumps(intent), encoding="utf-8")

    with patch("verticals.bitnin.services.bitnin_hitl.builder.build_approval_request") as mock_build, \
         patch("verticals.bitnin.services.bitnin_hitl.builder.build_telegram_approval_message") as mock_msg:
        mock_build.return_value = {
            "approval_id": "test_app_1",
            "status": "awaiting_human_approval",
            "expires_at": "2026-12-31T23:59:59Z"
        }
        mock_msg.return_value = "Mock message"
        # 2. Request approval
        req_result = runner.request(intent_path=str(intent_path))
    
    request_path = Path(req_result["request_path"])
    original_content = request_path.read_text(encoding="utf-8")
    original_payload = json.loads(original_content)
    assert original_payload["status"] == "awaiting_human_approval"

    # 3. Decide (Approve)
    runner.decide(approval_id=req_result["approval_id"], decision="approved", actor="test_human")
    
    # 4. Verify original request file is NOT changed (Immutability Hardening)
    after_content = request_path.read_text(encoding="utf-8")
    after_payload = json.loads(after_content)
    assert after_payload["status"] == "awaiting_human_approval"
    assert "decision" not in after_payload
