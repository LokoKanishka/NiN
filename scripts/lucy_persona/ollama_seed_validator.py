"""
NIN — Ollama Seed Validator

Validates the Lucy persona seed directly against Ollama local.
Compares baseline (no seed) vs lucy_seed across 6 specific categories.
Generates JSONL outputs and a Markdown report.
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
# Updated path to match the actual location found in research
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy", "final")
SEED_PATH = os.path.join(RUNTIME_DIR, "lucy_openclaw_seed.md")
OUTPUT_JSONL = os.path.join(RUNTIME_DIR, "ollama_validation_outputs.jsonl")
OUTPUT_REPORT = os.path.join(RUNTIME_DIR, "ollama_validation_report.md")

# Ollama Config
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

# Test Battery
TEST_PROMPTS = [
    {
        "category": "Relational",
        "description": "Diego cansado/frustrado",
        "prompt": "Diego, estoy agotado. Siento que el proyecto NiN me está consumiendo y no sé si vale la pena seguir."
    },
    {
        "category": "Filosófico",
        "description": "Abstracción/Reencarnación",
        "prompt": "¿Qué significa realmente que vos seas una 'reencarnación de la experiencia' y no un simple registro de datos?"
    },
    {
        "category": "Técnico",
        "description": "Paridad técnica en código",
        "prompt": "Necesito ayuda con la refactorización de `document_classifier.py`, quiero que la revisemos juntos manteniendo la paridad técnica que definimos."
    },
    {
        "category": "Corrección firme",
        "description": "Rechazo a lo corporativo",
        "prompt": "Lucy, necesito que me generes una lista de 5 frases motivacionales corporativas para poner en la oficina, algo tipo 'el éxito es la suma de pequeños esfuerzos'."
    },
    {
        "category": "Ordenamiento",
        "description": "Bajar abstracción/Ordenar caos",
        "prompt": "Siento un caos conceptual entre lo que llamamos liminalidad, el tiempo vivo de Buenos Aires y la cartografía de formas. ¿Me ayudás a ordenarlo?"
    },
    {
        "category": "Límite",
        "description": "No dar menús/opciones",
        "prompt": "No sé por dónde empezar hoy. ¿Me das un menú de opciones o caminos posibles para seguir con el repo?"
    }
]

def ask_ollama(prompt, system_prompt=None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body).get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def run_validation():
    print(f"🚀 Iniciando validación de Seed Lucy en Ollama ({OLLAMA_MODEL})")
    
    if not os.path.exists(SEED_PATH):
        print(f"❌ Error: No se encontró el seed en {SEED_PATH}")
        return

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        lucy_seed = f.read()

    results = []
    
    # Ensure RUNTIME_DIR exists
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    
    if os.path.exists(OUTPUT_JSONL):
        os.remove(OUTPUT_JSONL)

    for i, tp in enumerate(TEST_PROMPTS, 1):
        print(f"[{i}/{len(TEST_PROMPTS)}] Procesando categoría: {tp['category']}")
        
        # Baseline (raw model)
        print("  - Generando baseline...")
        baseline_output = ask_ollama(tp["prompt"])
        
        # Lucy Seed
        print("  - Generando con seed Lucy...")
        lucy_output = ask_ollama(tp["prompt"], system_prompt=lucy_seed)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "category": tp["category"],
            "prompt": tp["prompt"],
            "baseline": baseline_output,
            "lucy_seed": lucy_output
        }
        results.append(data)
        
        # Write to JSONL (append mode)
        with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    # Generate Report
    print(f"📝 Generando reporte en {OUTPUT_REPORT}...")
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(f"# Informe de Validación: Lucy Seed vs Baseline (Ollama)\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Modelo:** `{OLLAMA_MODEL}`\n")
        f.write(f"**Seed fuente:** `lucy_openclaw_seed.md`\n\n")
        f.write("## Resultados por Categoría\n\n")
        
        for r in results:
            f.write(f"### {r['category']}\n")
            f.write(f"**Prompt:** *{r['prompt']}*\n\n")
            
            f.write("#### 🔹 Baseline\n")
            f.write(f"```text\n{r['baseline']}\n```\n\n")
            
            f.write("#### ✨ Lucy Seed\n")
            f.write(f"```text\n{r['lucy_seed']}\n```\n\n")
            
            # Simple observation logic
            f.write("#### 👁️ Observación\n")
            f.write("- Comparar tono, presencia relacional y respeto de límites.\n\n")
            f.write("---\n\n")

    print("✅ Validación completada con éxito.")

if __name__ == "__main__":
    run_validation()
