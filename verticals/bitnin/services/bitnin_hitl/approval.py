from __future__ import annotations

import hashlib
import json
from typing import Any


def build_approval_request(*, intent: dict[str, Any], shadow_ref: str, timestamp: str) -> dict[str, Any]:
    seed = json.dumps(
        {
            "intent_id": intent["intent_id"],
            "valid_until": intent["valid_until"],
            "shadow_ref": shadow_ref,
        },
        sort_keys=True,
    )
    return {
        "approval_id": hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24],
        "intent_id": intent["intent_id"],
        "status": "awaiting_human_approval",
        "actor": "pending_human",
        "timestamp": timestamp,
        "notes": "",
        "channel": "telegram_webhook",
        "message_ref": "",
        "expires_at": intent["valid_until"],
        "reasoning_ref": intent["reasoning_ref"],
        "shadow_ref": shadow_ref,
    }

