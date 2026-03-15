from __future__ import annotations

import json
import pytest
from pathlib import Path
from verticals.bitnin.services.bitnin_hitl.builder import BitNinHitlRunner

def test_approval_request_immutability(tmp_path: Path):
    requests_dir = tmp_path / "requests"
    decisions_dir = tmp_path / "decisions"
    snapshots_dir = tmp_path / "snapshots"
    
    # Needs a schema and an intent to work
    # Mocking BITNIN_ROOT for the test session if needed, or just using the runner with paths
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
    
    # 2. Request approval
    req_result = runner.request(intent_path=str(intent_path))
    request_path = Path(req_result["request_path"])
    original_content = request_path.read_text(encoding="utf-8")
    original_payload = json.loads(original_content)
    assert original_payload["status"] == "awaiting_human_approval"
    
    # 3. Decide (Approve)
    runner.decide(request_path=str(request_path), decision="approve", actor="test_human")
    
    # 4. Verify Immutability
    final_content = request_path.read_text(encoding="utf-8")
    final_payload = json.loads(final_content)
    
    assert final_payload["status"] == "awaiting_human_approval", "Request status should NOT change (Hardening)"
    assert final_payload == original_payload, "Request file should remain bit-identical (Hardening)"
    
    # 5. Verify Decision Artifact
    decision_files = list(decisions_dir.glob("*.json"))
    assert len(decision_files) == 1
    decision_payload = json.loads(decision_files[0].read_text(encoding="utf-8"))
    assert decision_payload["status"] == "approved"
    assert decision_payload["request_ref"] == str(request_path)
