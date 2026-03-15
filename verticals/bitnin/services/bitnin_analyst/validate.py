from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import json
from pathlib import Path
from typing import Any
from verticals.bitnin.services.validator_fallback import BasicValidatorFallback


BITNIN_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SCHEMA_PATH = BITNIN_ROOT / "SCHEMAS" / "analysis_output.schema.json"


def normalize_retrieved_episodes(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for item in results:
        payload = item.get("payload", {})
        normalized.append(
            {
                "episode_id": payload.get("episode_id", "unknown"),
                "score": round(float(item.get("score", 0.0)), 6),
                "summary_local": payload.get("summary_local", ""),
                "dominant_cause": payload.get("dominant_cause", ""),
            }
        )
    return normalized


def pre_llm_guardrail(context: dict[str, Any], retrieval: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    episode_results = retrieval["episode_results"]
    if context["data_coverage_score"] < 0.75:
        reasons.append("data_coverage_below_threshold")
    if len(episode_results) < 2:
        reasons.append("too_few_episode_analogues")
    elif float(episode_results[0]["score"]) < 0.5:
        reasons.append("top_episode_similarity_too_low")
    
    # Refinado v1: Reducir umbral de narrativa para advertencia
    if context["narrative_coverage_score"] < 0.15:
        reasons.append("narrative_coverage_critically_low")
    return reasons


def post_llm_guardrails(
    analysis: dict[str, Any],
    *,
    context: dict[str, Any],
    retrieval: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    notes = list(analysis.get("notes", []))
    if not isinstance(notes, list):
        notes = [str(notes)]

    if analysis["recommended_action"] in {"long", "short", "hedge", "reduce"}:
        # Refinado v1: Suelo de confianza direccional reducido a 0.55
        if analysis["confidence"] < 0.55:
            analysis["recommended_action"] = "no_trade"
            analysis["final_status"] = "no_trade"
            analysis["why_not"] = sorted(set(analysis["why_not"] + ["confidence_too_low_for_directional_action"]))
            notes.append("recommended_action downgraded to no_trade because confidence < 0.55")
        elif context["narrative_coverage_score"] < 0.15:
            analysis["recommended_action"] = "no_trade"
            analysis["final_status"] = "no_trade"
            analysis["why_not"] = sorted(set(analysis["why_not"] + ["narrative_coverage_too_low_for_directional_action"]))
            notes.append("recommended_action downgraded to no_trade because narrative coverage is critically low")
        # Refinado v1: Permitir accion con 2 analogos si la confianza es alta (>0.7)
        elif len(retrieval["episode_results"]) < 2 or (len(retrieval["episode_results"]) < 3 and analysis["confidence"] < 0.7):
            analysis["recommended_action"] = "no_trade"
            analysis["final_status"] = "no_trade"
            analysis["why_not"] = sorted(set(analysis["why_not"] + ["too_few_analogues_for_directional_action"]))
            notes.append(f"recommended_action downgraded because analogues={len(retrieval['episode_results'])} and confidence={analysis['confidence']}")

    if analysis["recommended_action"] == "no_trade" and analysis["final_status"] == "ok":
        analysis["final_status"] = "no_trade"

    analysis["notes"] = sorted(set(note for note in notes if note))
    return analysis, analysis["notes"]


class AnalysisOutputValidator:
    def __init__(self, schema_path: Path | None = None) -> None:
        self.validator = BasicValidatorFallback(None)

    def validate(self, instance: dict[str, Any]) -> list[str]:
        return [str(err) for err in self.validator.iter_errors(instance)]
