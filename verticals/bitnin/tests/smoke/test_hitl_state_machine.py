import pytest

from verticals.bitnin.services.bitnin_hitl.state_machine import transition_approval


def test_hitl_state_machine_approves_from_waiting():
    approval = {
        "approval_id": "ap1",
        "intent_id": "in1",
        "status": "awaiting_human_approval",
        "actor": "pending_human",
        "timestamp": "2026-03-13T00:00:00.000Z",
        "notes": "",
    }
    updated = transition_approval(
        approval,
        event="approve",
        actor="lucy",
        timestamp="2026-03-13T01:00:00.000Z",
        notes="ok",
    )
    assert updated["status"] == "approved"
    assert updated["actor"] == "lucy"


def test_hitl_state_machine_rejects_early_expiration():
    approval = {
        "approval_id": "ap1",
        "intent_id": "in1",
        "status": "awaiting_human_approval",
        "actor": "pending_human",
        "timestamp": "2026-03-13T00:00:00.000Z",
        "notes": "",
        "expires_at": "2026-03-13T02:00:00.000Z",
    }
    with pytest.raises(ValueError, match="Cannot expire approval before expires_at"):
        transition_approval(
            approval,
            event="expire",
            actor="system_expirer",
            timestamp="2026-03-13T01:00:00.000Z",
            notes="too early",
        )


def test_hitl_state_machine_rejects_late_approval():
    approval = {
        "approval_id": "ap1",
        "intent_id": "in1",
        "status": "awaiting_human_approval",
        "actor": "pending_human",
        "timestamp": "2026-03-13T00:00:00.000Z",
        "notes": "",
        "expires_at": "2026-03-13T02:00:00.000Z",
    }
    with pytest.raises(ValueError, match="Cannot resolve approval after expires_at"):
        transition_approval(
            approval,
            event="approve",
            actor="lucy",
            timestamp="2026-03-13T03:00:00.000Z",
            notes="too late",
        )
