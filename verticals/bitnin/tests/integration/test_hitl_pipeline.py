import json
from pathlib import Path

from verticals.bitnin.services.bitnin_hitl.builder import BitNinHitlRunner
from verticals.bitnin.services.bitnin_shadow.intent import build_shadow_intent
from verticals.bitnin.tests.conftest import load_fixture


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_hitl_pipeline_request_approve_reject_and_expire(tmp_path):
    analysis = load_fixture("shadow_analysis_sample.json")
    analysis_path = tmp_path / "analysis.json"
    _write_json(analysis_path, analysis)
    intent = build_shadow_intent(analysis=analysis, reasoning_ref=str(analysis_path))
    intent_path = tmp_path / "intent.json"
    _write_json(intent_path, intent)

    runner = BitNinHitlRunner(
        requests_root=tmp_path / "requests",
        decisions_root=tmp_path / "decisions",
        snapshots_root=tmp_path / "snapshots",
    )
    request_result = runner.request(intent_path=str(intent_path))
    request_payload = json.loads(Path(request_result["request_path"]).read_text(encoding="utf-8"))
    assert request_payload["status"] == "awaiting_human_approval"

    approved_result = runner.decide(
        request_path=request_result["request_path"],
        decision="approve",
        actor="operator_1",
        notes="looks good",
    )
    approved = json.loads(Path(approved_result["decision_path"]).read_text(encoding="utf-8"))
    assert approved["status"] == "approved"

    second_intent = build_shadow_intent(analysis=analysis, reasoning_ref=str(analysis_path))
    second_intent["intent_id"] = "second-intent"
    second_intent_path = tmp_path / "intent_2.json"
    _write_json(second_intent_path, second_intent)
    second_request = runner.request(intent_path=str(second_intent_path))
    rejected_result = runner.decide(
        request_path=second_request["request_path"],
        decision="reject",
        actor="operator_2",
        notes="not enough evidence",
    )
    rejected = json.loads(Path(rejected_result["decision_path"]).read_text(encoding="utf-8"))
    assert rejected["status"] == "rejected"

    third_intent = build_shadow_intent(analysis=analysis, reasoning_ref=str(analysis_path))
    third_intent["intent_id"] = "third-intent"
    third_intent["valid_until"] = "2026-03-13T00:00:00.000Z"
    third_intent_path = tmp_path / "intent_3.json"
    _write_json(third_intent_path, third_intent)
    third_request = runner.request(intent_path=str(third_intent_path))
    expired_result = runner.expire(request_path=third_request["request_path"])
    expired = json.loads(Path(expired_result["decision_path"]).read_text(encoding="utf-8"))
    assert expired["status"] == "expired"
