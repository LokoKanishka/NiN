"""
NIN — Lucy Persona Distiller: Relational Extractor Module

Reads runtime/persona_lucy/parsed/classified_chunks.jsonl
Extracts relational traces ONLY from chunks labeled as "reported_interaction".
Uses Ollama to generate a structured analysis of Lucy's behavior/relationship with Diego.

Outputs to runtime/persona_lucy/parsed/relational_traces.jsonl
"""

import os
import json
import requests
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
CLASSIFIED_CHUNKS_PATH = os.path.join(PARSED_DIR, "classified_chunks.jsonl")
RELATIONAL_TRACES_PATH = os.path.join(PARSED_DIR, "relational_traces.jsonl")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

RELATIONAL_EXTRACTION_PROMPT = """Eres el clasificador de vínculos del sistema NIN, especializado en cómo Lucy interactúa con su usuario Diego.
Tu tarea es leer un fragmento de bitácora (interacción reportada) y extraer las "trazas relacionales".

Debes extraer y resumir, estrictamente en un JSON, los siguientes campos basados SOLO en el texto:
- "observed_user_need": Qué parece necesitar o pedir Diego según este fragmento (ej. contención, debate, ajuste técnico).
- "lucy_response_pattern": Cuál es el patrón o hábito de respuesta de Lucy (ej. interrumpe, escucha, confronta).
- "relational_signal": Qué tipo de vínculo se observa (ej. paridad, dependencia técnica, co-creación, afectivo).
- "tone_adjustment": Cómo ajusta el tono para responderle.
- "abstraction_preference": Preferencia de nivel de abstracción (alto, medio, bajo, liminal).
- "quote": Breve cita del fragmento original que resume esta dinámica.

Si un campo no aplica o no se menciona, pon "No especificado".

Responde SOLO con un JSON válido de esta estructura:
{
  "observed_user_need": "...",
  "lucy_response_pattern": "...",
  "relational_signal": "...",
  "tone_adjustment": "...",
  "abstraction_preference": "...",
  "quote": "..."
}
"""

def extract_trace(chunk_text: str) -> dict:
    """Invokes Ollama to extract relational traces from a single chunk."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": RELATIONAL_EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": f"Extrae las trazas relacionales del siguiente fragmento de bitácora:\n\n{chunk_text}\n\n---\nRetorna SOLO el JSON solicitado."
            }
        ],
        "stream": False,
        "options": {"temperature": 0.2}
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
            
        data = json.loads(content.strip())
        return data
        
    except Exception as e:
        print(f"⚠️ Extraction error: {e}")
        return {
            "observed_user_need": "Error",
            "lucy_response_pattern": "Error",
            "relational_signal": "Error",
            "tone_adjustment": "Error",
            "abstraction_preference": "Error",
            "quote": "Error"
        }

def process_relational_traces():
    if not os.path.exists(CLASSIFIED_CHUNKS_PATH):
        print(f"❌ Error: {CLASSIFIED_CHUNKS_PATH} not found. Run document_classifier.py first.")
        return []

    print("📖 Reading classified chunks for reported interactions...")
    
    traces = []
    
    with open(CLASSIFIED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            
            is_reported = chunk.get("label") == "reported_interaction"
            is_operational = chunk.get("label") == "operational_notes"
            content = chunk.get("content", "").lower()
            
            # If it's operational but mentions the relationship/Diego, we scan it too
            contains_relational_keywords = any(kw in content for kw in ["diego", "vínculo", "relación", "afectivo", "interacción"])
            
            if not is_reported and not (is_operational and contains_relational_keywords):
                continue
                
            chunk_id = chunk.get("chunk_id", "unknown")
            print(f"   ► Extracting traces from {chunk_id}...", end=" ")
            
            start_t = time.time()
            extracted = extract_trace(chunk.get("content", ""))
            dt = time.time() - start_t
            
            # Construct final trace
            trace_obj = {
                "trace_id": f"trace_{chunk_id}",
                "source_doc": chunk.get("doc_id", "unknown"),
                "chunk_id": chunk_id,
                "observed_user_need": extracted.get("observed_user_need", ""),
                "lucy_response_pattern": extracted.get("lucy_response_pattern", ""),
                "relational_signal": extracted.get("relational_signal", ""),
                "tone_adjustment": extracted.get("tone_adjustment", ""),
                "abstraction_preference": extracted.get("abstraction_preference", ""),
                "quote": extracted.get("quote", "")
            }
            
            traces.append(trace_obj)
            print(f"[Done - {dt:.1f}s]")

    # We will overwrite relational_traces.jsonl for complete freshness during full runs
    with open(RELATIONAL_TRACES_PATH, "w", encoding="utf-8") as out_f:
        for t in traces:
            out_f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"\n✅ Relational trace extraction complete. {len(traces)} traces saved to {RELATIONAL_TRACES_PATH}")
    return traces

if __name__ == "__main__":
    process_relational_traces()
