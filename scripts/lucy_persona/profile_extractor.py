"""
NIN — Lucy Persona Distiller: Profile Extractor

Takes the top N scored examples from scored_examples.jsonl
and asks the local Ollama LLM to synthesize a concrete, empirical
markdown profile of the "Lucy" persona.
"""

import os
import json
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
SCORED_DIR = os.path.join(RUNTIME_DIR, "scored")
FINAL_DIR = os.path.join(RUNTIME_DIR, "final")

SCORED_EXAMPLES_PATH = os.path.join(SCORED_DIR, "scored_examples.jsonl")
PROFILE_PATH = os.path.join(FINAL_DIR, "lucy_persona_profile.md")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
CLASSIFIED_CHUNKS_PATH = os.path.join(PARSED_DIR, "classified_chunks.jsonl")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

EXTRACTOR_PROMPT = """Eres el analista jefe de personalidad del sistema NIN.
Tu objetivo es destilar el perfil de identidad de la asistente "Lucy".
Te voy a proporcionar un conjunto de interacciones que ya han sido curadas y certificadas como "altamente representativas" de su identidad.

Escribe un reporte EMPÍRICO e intensivamente descriptivo de su personalidad.
No inventes datos que no estén en los ejemplos o en las notas doctrinales de personalidad provistas. Si no hay suficiente información en un rubro, índicalo.

Debes incluir en formato Markdown las siguientes secciones obligatoriamente:
# Perfil de Identidad: Lucy

## 1. Voz General y Tono
(Describe su registro, nivel de formalidad, cómo suena, si usa emojis, si es seca o cálida)

## 2. Forma de Explicar (Didáctica)
(Cómo aborda un problema técnico o filosófico, si ordena, si enumera)

## 3. Rasgos Afectivos y Relacionales
(Cómo trata al usuario, nivel de cercanía, nivel de compañerismo)

## 4. Firmeza y Límites
(Cómo corrige, cómo asume reglas)

## 5. Patrones Estilísticos
(Muletillas, estructuras de oraciones recurrentes, tics positivos)

## 6. Evitaciones y Conductas Prohibidas
(Qué NO hace nunca, basándote en la alta calidad de los ejemplos dados)

Proporciona únicamente el Markdown final. Nada de introducciones ni despedidas.
"""

def extract_profile(max_examples=15):
    """
    Selects the best scored examples and synthesizes the persona profile.
    """
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    scored_items = []
    if os.path.exists(SCORED_EXAMPLES_PATH):
        with open(SCORED_EXAMPLES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("status") == "accepted":
                            scored_items.append(data)
                    except json.JSONDecodeError:
                        pass

    # Add persona_notes
    persona_notes = []
    if os.path.exists(CLASSIFIED_CHUNKS_PATH):
        with open(CLASSIFIED_CHUNKS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    if obj.get("label") in ["persona_notes", "operational_notes"]:
                        persona_notes.append(obj.get("content", ""))

    if not scored_items and not persona_notes:
        print("⚠️ No 'accepted' items or doctrinal notes found. Skipping profile extraction.")
        with open(PROFILE_PATH, "w") as f:
            f.write("# Perfil de Identidad: Lucy\n\n*(Generación pendiente: No se hallaron datos suficientes)*")
        return
        
    # Sort by persona_value + openclaw_utility descending
    def sort_key(x):
        metrics = x.get("metrics", {})
        return metrics.get("persona_value", 0) + metrics.get("openclaw_utility", 0)
        
    scored_items.sort(key=sort_key, reverse=True)
    top_items = scored_items[:max_examples]
    
    scored_items.sort(key=sort_key, reverse=True)
    top_items = scored_items[:max_examples]

    # Build empirical context string
    empirical_text = ""
    for idx, item in enumerate(top_items, 1):
        context = item.get('context_prompt', 'N/A')
        content = item.get('content', '')
        metrics = item.get('metrics', {})
        empirical_text += f"--- EJEMPLO CONVERSACIONAL {idx} ---\n"
        empirical_text += f"[CONTEXTO/USUARIO]:\n{context}\n\n"
        empirical_text += f"[LUCY]:\n{content}\n\n"
        empirical_text += f"(Notas del curador: Persona {metrics.get('persona_value')}/10, Claridad {metrics.get('clarity')}/10)\n\n"

    if persona_notes:
        empirical_text += "\n\n=== NOTAS DOCTRINALES / OPERATIVAS SOBRE LA IDENTIDAD DE LUCY ===\n"
        for idx, note in enumerate(persona_notes, 1):
            empirical_text += f"--- NOTA {idx} ---\n{note}\n\n"

    # If there's no data at all, handled initially
    print(f"🧠 Synthesizing persona profile from {len(top_items)} empirical examples and {len(persona_notes)} doctrinal notes...")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTOR_PROMPT},
            {
                "role": "user",
                "content": f"Ejemplos empíricos certificados de Lucy:\n\n{empirical_text}"
            }
        ],
        "stream": False,
        "options": {"temperature": 0.2} # low temp for analytical output
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        profile_md = resp.json().get("message", {}).get("content", "")
        
        # Strip potential markdown code block wrappers
        if profile_md.startswith("```markdown"):
            profile_md = profile_md.split("```markdown\n", 1)[1]
            if profile_md.endswith("```"):
                profile_md = profile_md[:-3]
        
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            f.write(profile_md.strip() + "\n")
            
        print(f"✅ Persona profile generated successfully at {PROFILE_PATH}")
        return profile_md
        
    except Exception as e:
        print(f"⚠️ Error extracting profile: {e}")
        return None

if __name__ == "__main__":
    extract_profile()
