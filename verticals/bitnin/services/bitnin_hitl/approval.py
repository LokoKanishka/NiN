from __future__ import annotations

import hashlib
import json
from typing import Any


def build_approval_request(
    *,
    intent: dict[str, Any],
    shadow_ref: str,
    timestamp: str,
    expires_at: str,
) -> dict[str, Any]:
    approval_id = f"{intent['intent_id']}_{timestamp.replace(':', '-')}"
    return {
        "approval_id": approval_id,
        "status": "pending",
        "intent_ref": shadow_ref,
        "created_at": timestamp,
        "expires_at": expires_at,
        "decision": None,
    }
