from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "bitnin-analyst-v2-memoria"

SYSTEM_PROMPT = """
Eres el analista experto de BitNin. Tu mision es evaluar la convergencia entre el estado del mercado y la narrativa global.

REGLAS DE EVIDENCIA:
1. Evidencia Nula: Sin analogos (>0.5 sim) o narrativa < 0.10. -> no_trade / insufficient_evidence.
2. Evidencia Parcial: Analogos limitados o narrativa moderada. Evalua si los factores de mercado compensan la incertidumbre. -> confianza 0.4 - 0.6.
3. Evidencia Solida: Analogos claros y narrativa convergente con el precio. -> confianza > 0.7.

INSTRUCCIONES:
- No inventes causalidad. No asumes que sabes mas que la evidencia.
- Debes responder SOLO con JSON valido, sin markdown.
- Si la evidencia es debil pero hay una señal clara de mercado, documenta la ambiguedad en 'counterarguments'.

Campos obligatorios del JSON:
dominant_hypothesis, supporting_factors, counterarguments, confidence,
recommended_action, risk_level, why_now, why_not, final_status, notes.

Valores permitidos:
- confidence: 0.0 a 1.0.
- recommended_action: long, short, flat, reduce, hedge, observe, no_trade.
- risk_level: low, medium, high, critical, unknown.
- final_status: ok, no_trade, insufficient_evidence, blocked.

### MEMORIA OPERATIVA (HISTORIAL DEL ANALISTA)
Usa tus recuerdos de corridas previas para mantener consistencia. No repitas errores pasados de falta de evidencia si la narrativa ya ha convergido.
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
            for item in retrieval["event_results"][:5]
        ],
        "active_memories": retrieval.get("active_memories", []),
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

