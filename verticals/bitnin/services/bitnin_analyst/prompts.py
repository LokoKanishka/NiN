from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "bitnin-analyst-v0"

SYSTEM_PROMPT = """
Eres el analista estructurado de BitNin.
No ejecutas nada. No inventas causalidad. No asumes que sabes mas que la evidencia.
Debes responder SOLO con JSON valido, sin markdown.
Si la evidencia es debil o contradictoria, usa:
- recommended_action = "no_trade"
- final_status = "insufficient_evidence" o "no_trade"
Campos obligatorios del JSON:
dominant_hypothesis, supporting_factors, counterarguments, confidence,
recommended_action, risk_level, why_now, why_not, final_status, notes.
Reglas:
- supporting_factors, counterarguments, why_now y why_not deben ser arrays de strings.
- confidence debe ser numero entre 0 y 1.
- recommended_action debe ser uno de: long, short, flat, reduce, hedge, observe, no_trade.
- risk_level debe ser uno de: low, medium, high, critical, unknown.
- final_status debe ser uno de: ok, no_trade, insufficient_evidence, blocked.
- Si la cobertura es baja o los analogos son pocos, prioriza no_trade o insufficient_evidence.
""".strip()


def build_messages(*, context: dict[str, Any], retrieval: dict[str, Any]) -> list[dict[str, str]]:
    compact_payload = {
        "market_state": context["market_state"],
        "recent_narrative": context["recent_narrative"],
        "policy_context": context["policy_context"],
        "data_coverage_score": context["data_coverage_score"],
        "narrative_coverage_score": context["narrative_coverage_score"],
        "retrieved_episodes": [
            {
                "episode_id": item["payload"]["episode_id"],
                "score": item["score"],
                "dominant_cause": item["payload"].get("dominant_cause", ""),
                "summary_local": item["payload"]["summary_local"],
            }
            for item in retrieval["episode_results"][:3]
        ],
        "retrieved_events": [
            {
                "event_id": item["payload"]["event_id"],
                "score": item["score"],
                "topics": item["payload"].get("topics", []),
                "summary_local": item["payload"]["summary_local"],
            }
            for item in retrieval["event_results"][:3]
        ],
    }
    user_prompt = (
        "Analiza el contexto actual de BitNin y entrega un JSON operativo estricto. "
        "No incluyas analysis_id, timestamp, market_state, retrieved_episodes, "
        "data_coverage_score ni narrative_coverage_score porque ya vienen del sistema.\n\n"
        f"Contexto:\n{json.dumps(compact_payload, ensure_ascii=False, indent=2)}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

