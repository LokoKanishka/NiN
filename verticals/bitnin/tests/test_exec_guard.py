import pytest
import os
import shutil
import json
from datetime import datetime, timezone, timedelta
from verticals.bitnin.services.bitnin_exec_guard.executor import ExecGuardExecutor
from verticals.bitnin.services.bitnin_exec_guard.receipt import ReceiptManager
from verticals.bitnin.services.bitnin_exec_guard.snapshot import SnapshotManager

RUNTIME_DIR = "/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/execution"

@pytest.fixture(autouse=True)
def clean_runtime():
    for subdir in ["requests", "results", "snapshots", "logs"]:
        path = os.path.join(RUNTIME_DIR, subdir)
        os.makedirs(path, exist_ok=True)
        for f in os.listdir(path):
            if f != ".gitkeep":
                os.remove(os.path.join(path, f))
    yield

def _make_intent(action="buy", mode="simulation", approved=True, valid_until_offset=timedelta(hours=1)):
    valid_until = (datetime.now(timezone.utc) + valid_until_offset).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "intent_id": "int_123",
        "mode": mode,
        "action": action,
        "entry_reference": {"symbol": "BTC", "interval": "1m", "timestamp": "2024-01-01T00:00:00Z", "price": 50000},
        "valid_until": valid_until,
        "reasoning_ref": "some_ref",
        "approved": approved,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "open"
    }

def _make_approval(status="approved"):
    return {
        "approval_id": "app_456",
        "intent_id": "int_123",
        "status": status,
        "actor": "hitl",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": ""
    }

def _make_analysis():
    return {"analysis_ref": "something"}

def test_intent_without_approval():
    intent = _make_intent()
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=None, analysis=_make_analysis())
    assert record["status"] == "guardrail_blocked"
    assert "missing_approval" in record["rejection_reasons"]

def test_intent_expired():
    intent = _make_intent(valid_until_offset=timedelta(minutes=-10))
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=_make_approval(), analysis=_make_analysis())
    assert record["status"] == "expired"
    assert "intent_expired" in record["rejection_reasons"]

def test_intent_approved_but_blocked_by_guardrail():
    # E.g. forbidden action
    intent = _make_intent(action="gambling")
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=_make_approval(), analysis=_make_analysis())
    assert record["status"] == "invalid_intent"
    assert "invalid_action:gambling" in record["rejection_reasons"]

def test_acceptance_in_dry_run():
    intent = _make_intent(action="buy")
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=_make_approval(), analysis=_make_analysis())
    assert record["status"] == "accepted_dry_run"
    assert len(record["rejection_reasons"]) == 0
    assert "valid_action" in record["validated_guards"]
    assert record["dry_run"] is True

def test_snapshot_generation():
    intent = _make_intent()
    approval = _make_approval()
    analysis = _make_analysis()
    
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=approval, analysis=analysis)
    
    req_path = ReceiptManager.persist_request(record["execution_id"], {"intent": intent})
    res_path = ReceiptManager.persist_result(record)
    snap_path = SnapshotManager.create_snapshot(record["execution_id"], req_path, res_path)
    
    assert os.path.exists(req_path)
    assert os.path.exists(res_path)
    assert os.path.exists(snap_path)
    assert snap_path.endswith(".tar.gz")

def test_idempotence_basic():
    # Calling the executor doesn't mutate states globally without explicit caller intention
    # Same payload generates multiple distinct execution requests
    intent = _make_intent()
    approval = _make_approval()
    analysis = _make_analysis()
    executor = ExecGuardExecutor()
    record1 = executor.execute(intent=intent, approval=approval, analysis=analysis)
    record2 = executor.execute(intent=intent, approval=approval, analysis=analysis)
    
    # Assert records are distinct attempts but both accepted
    assert record1["execution_id"] != record2["execution_id"]
    assert record1["status"] == "accepted_dry_run"
    assert record2["status"] == "accepted_dry_run"

def test_pipeline_e2e():
    intent = _make_intent()
    approval = _make_approval()
    executor = ExecGuardExecutor()
    record = executor.execute(intent=intent, approval=approval, analysis={"ref": "foo"})
    
    ReceiptManager.persist_request(record["execution_id"], {"intent": intent})
    ReceiptManager.persist_result(record)
    ReceiptManager.log_event(record["execution_id"], "Test pass")
    
    # Verify log presence
    logs = os.listdir(os.path.join(RUNTIME_DIR, "logs"))
    assert len(logs) > 0
