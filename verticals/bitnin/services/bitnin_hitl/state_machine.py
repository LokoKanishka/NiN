from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


TRANSITIONS = {
    "awaiting_human_approval": {
        "approve": "approved",
        "reject": "rejected",
        "expire": "expired",
    },
    "approved": {},
    "rejected": {},
    "expired": {},
}


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def transition_approval(
    approval: dict[str, Any],
    *,
    event: str,
    actor: str,
    timestamp: str,
    notes: str = "",
) -> dict[str, Any]:
    current_status = approval["status"]
    next_status = TRANSITIONS.get(current_status, {}).get(event)
    if next_status is None:
        raise ValueError(f"Invalid HITL transition: {current_status} -> {event}")
    expires_at = approval.get("expires_at")
    if expires_at:
        transition_time = _parse_utc(timestamp)
        expiry_time = _parse_utc(expires_at)
        if event in {"approve", "reject"} and transition_time > expiry_time:
            raise ValueError("Cannot resolve approval after expires_at.")
        if event == "expire" and transition_time < expiry_time:
            raise ValueError("Cannot expire approval before expires_at.")
    updated = dict(approval)
    updated["status"] = next_status
    updated["actor"] = actor
    updated["timestamp"] = timestamp
    updated["notes"] = notes
    return updated
