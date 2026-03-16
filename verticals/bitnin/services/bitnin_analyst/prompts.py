from __future__ import annotations

import json
from typing import Any


PROMPT_VERSION = "bitnin-analyst-v3-compuesta"

SYSTEM_PROMPT = """
Eres el analista experto de BitNin. Tu mision es evaluar la convergencia entre el estado del mercado y la narrativa global.

SEÑAL COMPUESTA (ESTRUCTURADA):
Usa el campo 'composite_signal' para guiar tu confianza y el campo 'causal_typology' para tu diagnostico:
- Estado HIGH (>0.7): Convergencia fuerte. Busca confirmar con narrativa y memoria.
- Estado DIVERGENT (0.4-0.7): Desbalance mercado/narrativa. Usa 'causal_typology' para explicar la divergencia.
- Estado LOW (<0.4): Ruido predominante. 

TIPOLOGIA CAUSAL (GUIA):
- 'narrativa_ausente': Menciona falta de cobertura como riesgo principal.
- 'mercado_fuerte_narrativa_debil': Breakout sin respaldo. Advierte sobre trampa/ruido.
- 'narrativa_fuerte_mercado_debil': Interes sin movimiento. Busca señales de acumulacion.
- 'ruido_predominante': No hay señales claras en ningun frente.

REGLAS DE EVIDENCIA:
1. Evidencia Nula: composite_signal.state == LOW o narrativa < 0.10. -> no_trade / insufficient_evidence.
2. Evidencia Parcial: composite_signal.state == DIVERGENT. Explica la 'causal_typology' detectada. -> confianza 0.4 - 0.6.
3. Evidencia Solida: composite_signal.state == HIGH. Analogos claros y narrativa convergente. -> confianza > 0.7.

INSTRUCCIONES:
- No inventes causalidad. Usa la 'causal_typology' proporcionada como base de tu razonamiento.
- Debes responder SOLO con JSON valido, sin markdown.
- Documenta explicitamente por que la tipologia actual justifica tu decision en 'notes'.

Campos obligatorios del JSON:
dominant_hypothesis, supporting_factors, counterarguments, confidence,
recommended_action, risk_level, why_now, why_not, final_status, notes.

Valores permitidos:
- confidence: 0.0 a 1.0.
- recommended_action: long, short, flat, reduce, hedge, observe, no_trade.
- risk_level: low, medium, high, critical, unknown.
- final_status: ok, no_trade, insufficient_evidence, blocked.

### MEMORIA OPERATIVA
Usa tus recuerdos de corridas previas para mantener consistencia.
""".strip()


def build_messages(*, context: dict[str, Any], retrieval: dict[str, Any]) -> list[dict[str, str]]:
    compact_payload = {
        "market_state": context["market_state"],
        "recent_narrative": context["recent_narrative"],
        "policy_context": context["policy_context"],
        "composite_signal": retrieval.get("composite_signal", {}),
        "active_memories": retrieval.get("active_memories", []),
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

