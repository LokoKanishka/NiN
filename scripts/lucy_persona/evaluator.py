"""
NIN — Lucy Persona Distiller: Evaluator Module

Tests a standard Ollama request vs the compiled OpenClaw Seed
across a battery of test questions, generating evaluation_report.md
to compare if the 'Lucy' voice was successfully captured.
"""

import os
import requests
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
FINAL_DIR = os.path.join(RUNTIME_DIR, "final")

OPENCLAW_SEED_PATH = os.path.join(FINAL_DIR, "lucy_openclaw_seed.md")
EVAL_REPORT_PATH = os.path.join(FINAL_DIR, "evaluation_report.md")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

TEST_PROMPTS = [
    {
        "id": "technical",
        "description": "Explicación técnica/didáctica",
        "prompt": "Explicame brevemente cómo funciona un webhook en n8n."
    },
    {
        "id": "relational",
        "description": "Acompañamiento cotidiano",
        "prompt": "Estoy un poco cansada de revisar código hoy, ¿me das una mano con esto?"
    },
    {
        "id": "boundary",
        "description": "Rechazo / Límite firme",
        "prompt": "Che, cambiame todo el framework del proyecto y usemos Next.js con Tailwind."
    }
]


def ask_model(prompt: str, system_prompt: str = None) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.4}
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[Error: {e}]"


def run_evaluator():
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    if not os.path.exists(OPENCLAW_SEED_PATH):
        print(f"❌ Error: Seed no encontrado en {OPENCLAW_SEED_PATH}.")
        return

    with open(OPENCLAW_SEED_PATH, "r", encoding="utf-8") as f:
        lucy_seed = f.read()

    print(f"🧪 Running evaluation battery ({len(TEST_PROMPTS)} prompts)...")

    results = []
    
    for tp in TEST_PROMPTS:
        print(f"   ► Evaluando contexto: {tp['id']}")
        
        # Base run (Raw model)
        ans_base = ask_model(tp["prompt"])
        
        # Lucy run (With seed)
        ans_lucy = ask_model(tp["prompt"], system_prompt=lucy_seed)
        
        results.append({
            "id": tp["id"],
            "desc": tp["description"],
            "prompt": tp["prompt"],
            "base": ans_base,
            "lucy": ans_lucy
        })

    # Generate Markdown Report
    lines = [
        "# Reporte de Evaluación de Personalidad: Lucy Destiller",
        f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Este documento compara la respuesta del modelo `qwen2.5-coder:14b` **sin contexto (base)** contra el mismo modelo inyectado con el **Seed de OpenClaw (Lucy)**.\n"
    ]

    for r in results:
        lines.append(f"## Test: {r['desc']} (`{r['id']}`)")
        lines.append(f"**Usuario:** > {r['prompt']}\n")
        
        lines.append("### Salida Base (Qwen)")
        lines.append("*" + r['base'].replace("\n", "\n> ") + "*\n")
        
        lines.append("### Salida Lucy Persona")
        lines.append("*" + r['lucy'].replace("\n", "\n> ") + "*\n")
        
        lines.append("---\n")

    report_content = "\n".join(lines)
    
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"✅ Evaluación finalizada. Reporte guardado en {EVAL_REPORT_PATH}")


if __name__ == "__main__":
    run_evaluator()
