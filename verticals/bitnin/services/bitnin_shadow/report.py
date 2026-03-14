from __future__ import annotations

from pathlib import Path
from typing import Any


def build_shadow_report(*, analysis: dict[str, Any], intent: dict[str, Any]) -> str:
    lines = [
        f"# Shadow Intent {intent['intent_id']}",
        "",
        f"- mode: {intent['mode']}",
        f"- action: {intent['action']}",
        f"- status: {intent['status']}",
        f"- created_at: {intent['created_at']}",
        f"- valid_until: {intent['valid_until']}",
        f"- confidence: {analysis['confidence']}",
        f"- risk_level: {analysis['risk_level']}",
        f"- data_coverage_score: {analysis['data_coverage_score']}",
        f"- narrative_coverage_score: {analysis['narrative_coverage_score']}",
        "",
        "## Hypothesis",
        analysis["dominant_hypothesis"],
        "",
        "## Why Now",
    ]
    lines.extend(f"- {item}" for item in analysis["why_now"])
    lines.append("")
    lines.append("## Why Not")
    lines.extend(f"- {item}" for item in analysis["why_not"])
    lines.append("")
    lines.append("## Retrieved Episodes")
    for episode in analysis["retrieved_episodes"]:
        lines.append(f"- {episode['episode_id']} score={episode['score']}: {episode['summary_local']}")
    return "\n".join(lines) + "\n"


def write_shadow_report(*, path: Path, report_text: str) -> Path:
    path.write_text(report_text, encoding="utf-8")
    return path

