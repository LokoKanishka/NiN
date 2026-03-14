from __future__ import annotations

from typing import Any


def build_telegram_approval_message(*, approval: dict[str, Any], intent: dict[str, Any], analysis: dict[str, Any]) -> str:
    top_episode = analysis["retrieved_episodes"][0] if analysis["retrieved_episodes"] else None
    lines = [
        "*BitNin HITL Request*",
        f"approval_id: `{approval['approval_id']}`",
        f"symbol: `{intent['entry_reference']['symbol']}`",
        f"interval: `{intent['entry_reference']['interval']}`",
        f"action: `{intent['action']}`",
        f"confidence: `{analysis['confidence']}`",
        f"risk: `{analysis['risk_level']}`",
        f"final_status: `{analysis['final_status']}`",
        f"expires_at: `{approval['expires_at']}`",
    ]
    if top_episode:
        lines.append(f"top_analog: `{top_episode['episode_id']}` score={top_episode['score']}")
    if analysis["why_not"]:
        lines.append(f"why_not: {analysis['why_not'][0]}")
    lines.extend(
        [
            "",
            f"/bitnin_aprobar {approval['approval_id']}",
            f"/bitnin_rechazar {approval['approval_id']}",
        ]
    )
    return "\n".join(lines)

