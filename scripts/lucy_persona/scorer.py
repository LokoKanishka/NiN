"""
NIN — Lucy Persona Distiller: Scorer Module

Uses local Ollama 14B to evaluate cleaned conversation turns.
Rates turns on multiple persona metrics and partitions them into
accepted/scored examples or rejected bundles.
"""

import os
import json
import requests
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
CLEAN_DIR = os.path.join(RUNTIME_DIR, "clean")
SCORED_DIR = os.path.join(RUNTIME_DIR, "scored")
FINAL_DIR = os.path.join(RUNTIME_DIR, "final")

CLEAN_TURNS_PATH = os.path.join(CLEAN_DIR, "clean_turns.jsonl")
SCORED_EXAMPLES_PATH = os.path.join(SCORED_DIR, "scored_examples.jsonl")
REJECTED_EXAMPLES_PATH = os.path.join(FINAL_DIR, "lucy_rejected_examples.jsonl")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

SCORING_PROMPT = """Eres el evaluador de personalidad del sistema NIN.
Tu tarea es analizar un fragmento de conversación donde habla la asistente "Lucy" y evaluar qué tan útil es ese fragmento para destilar o replicar su personalidad (tono, calidez, didáctica, estilo de ordenar ideas) en el futuro.

Debes extraer métricas de 1 a 10 para los siguientes aspectos:
- persona_value: representatividad general de la identidad de Lucy.
- style_quality: calidad literaria/estilística de la respuesta (sin alucinaciones ni muletillas de IA).
- coherence: coherencia de la respuesta respecto a la interacción.
- warmth: grado de calidez, empatía o cercanía humana.
- clarity: claridad explicativa o resolutiva.
- didactic_structure: capacidad para ordenar ideas, enumerar, hacer esquemas o guiar al usuario.
- privacy_risk: riesgo de privacidad (1 = muy seguro general, 10 = contiene contraseñas, IPs, datos muy íntimos o PII real de los operadores).
- lora_utility: qué tan útil sería este extracto textualmente para entrenar un modelo LoRA en el futuro (1 a 10).
- openclaw_utility: qué tan útil sería este extracto como "ejemplo canónico de conducta" (few-shot) para el prompt de OpenClaw hoy (1 a 10).

Reglas de Estado Final:
- Si "privacy_risk" >= 7, marca status como "rejected".
- Si "persona_value" <= 4 o "style_quality" <= 4, marca status como "rejected".
- Si es una respuesta estándar aburrida ("Hola, ¿en qué te ayudo?"), marca como "rejected".
- Si todo es de muy buena calidad y muestra rasgos distinguibles de Lucy, marca como "accepted".
- En caso de duda o calidades medias, marca "doubtful".

Formato de Respuesta (DEBE SER JSON ESTRICTO, NINGÚN OTRO TEXTO):
{
  "metrics": {
    "persona_value": int,
    "style_quality": int,
    "coherence": int,
    "warmth": int,
    "clarity": int,
    "didactic_structure": int,
    "privacy_risk": int,
    "lora_utility": int,
    "openclaw_utility": int
  },
  "rationale": "Breve justificación de por qué sirve o se rechaza...",
  "status": "accepted|rejected|doubtful"
}
"""


def score_turn_batch(context_prompt: str, assistant_turn: str) -> dict:
    """Invokes Ollama to score a single exchange."""
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SCORING_PROMPT},
            {
                "role": "user",
                "content": (
                     f"Contexto previo (Usuario u otros):\n{context_prompt}\n\n"
                     f"Respuesta a evaluar (Lucy/Asistente):\n{assistant_turn}\n\n---\n"
                     "Retorna la evaluación exclusivamente en JSON de acuerdo al formato."
                )
            }
        ],
        "stream": False,
        "options": {"temperature": 0.0}
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "")
        
        # Clean markdown code blocks if Ollama output them
        if "```json" in content:
            content = content.split("```json", 1)[1]
        if "```" in content:
            content = content.split("```", 1)[0]
            
        return json.loads(content.strip())
        
    except Exception as e:
        print(f"⚠️ Scoring error: {e}")
        return None


def run_scorer(max_items: int = 50):
    """
    Reads cleaned turns, pairs User/Assistant naturally,
    scores them with Ollama, and partitions into accepted/rejected.
    Because scoring is slow, we limit to max_items per run by default.
    """
    os.makedirs(SCORED_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)

    if not os.path.exists(CLEAN_TURNS_PATH):
        print(f"❌ Error: {CLEAN_TURNS_PATH} not found.")
        return

    # Load all clean turns to find exchanges
    clean_turns = []
    with open(CLEAN_TURNS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                clean_turns.append(json.loads(line))

    # Identify pairs: previous turn (context) + assistant turn
    exchanges_to_score = []
    for i, turn in enumerate(clean_turns):
        if turn.get("role") == "assistant":
            context = ""
            # If the previous turn is a user, use it as context
            if i > 0 and clean_turns[i-1].get("role") == "user":
                 context = clean_turns[i-1].get("content", "")
            
            exchanges_to_score.append({
                "doc_id": turn.get("doc_id"),
                "turn_index": turn.get("turn_index"),
                "context_prompt": context,
                "content": turn.get("content")
            })

    if not exchanges_to_score:
        print("⚠️ No assistant turns found for scoring.")
        return

    # To avoid re-scoring, check what we already have
    already_scored_keys = set()
    if os.path.exists(SCORED_EXAMPLES_PATH):
        with open(SCORED_EXAMPLES_PATH, "r") as f:
             for line in f:
                 if line.strip():
                     t = json.loads(line)
                     already_scored_keys.add(f"{t['doc_id']}:{t['turn_index']}")
    if os.path.exists(REJECTED_EXAMPLES_PATH):
        with open(REJECTED_EXAMPLES_PATH, "r") as f:
             for line in f:
                 if line.strip():
                     t = json.loads(line)
                     already_scored_keys.add(f"{t['doc_id']}:{t['turn_index']}")

    scored = []
    rejected = []
    items_scored_this_run = 0

    print(f"🔍 Found {len(exchanges_to_score)} exchanges. (Checking skipped)")

    import sys
    
    with open(SCORED_EXAMPLES_PATH, "a", encoding="utf-8") as f_scored, \
         open(REJECTED_EXAMPLES_PATH, "a", encoding="utf-8") as f_rejected:
         
        for exchange in exchanges_to_score:
            if items_scored_this_run >= max_items:
                print("\n⏹ Max bounds reached. Stopping scoring early to save time.")
                break
                
            key = f"{exchange['doc_id']}:{exchange['turn_index']}"
            if key in already_scored_keys:
                continue

            print(f"   ► Scoring {key}...", end=" ")
            sys.stdout.flush()

            start_t = time.time()
            score_data = score_turn_batch(exchange["context_prompt"], exchange["content"])
            dt = time.time() - start_t
            
            if not score_data:
                print("[FAILED]")
                continue

            # Merge
            exchange.update(score_data)

            if score_data.get("status") in ["accepted", "doubtful"]:
                f_scored.write(json.dumps(exchange, ensure_ascii=False) + "\n")
                f_scored.flush()
                scored.append(exchange)
                print(f"[✅ {score_data.get('status').upper()}] ({dt:.1f}s)")
            else:
                f_rejected.write(json.dumps(exchange, ensure_ascii=False) + "\n")
                f_rejected.flush()
                rejected.append(exchange)
                print(f"[❌ REJECTED - {score_data.get('rationale', 'No rationale')[:40]}...] ({dt:.1f}s)")
            
            items_scored_this_run += 1

    print(f"\n✅ Scoring run complete. {items_scored_this_run} items evaluated.")
    print(f"📁 Accepted/Doubtful appended to {SCORED_EXAMPLES_PATH}")
    print(f"📁 Rejected appended to {REJECTED_EXAMPLES_PATH}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM Profiler/Scorer")
    parser.add_argument("--max", type=int, default=10, help="Max turns to score in this run (chunked execution)")
    args = parser.parse_args()
    
    run_scorer(max_items=args.max)
