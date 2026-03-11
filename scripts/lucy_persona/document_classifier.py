"""
NIN — Lucy Persona Distiller: Document Classifier Module

Reads raw ingested documents, splits them into logical chunks,
and uses Ollama to classify each chunk into one of:
[dialogue, persona_notes, operational_notes, noise]

Outputs to runtime/persona_lucy/parsed/classified_chunks.jsonl
"""

import os
import json
import requests
import re
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
RAW_DOCS_DIR = os.path.join(RUNTIME_DIR, "raw_docs")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
MANIFEST_PATH = os.path.join(RUNTIME_DIR, "source_manifest.json")
CLASSIFIED_CHUNKS_PATH = os.path.join(PARSED_DIR, "classified_chunks.jsonl")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

CLASSIFICATION_PROMPT = """Eres el clasificador de corpus del sistema NIN, especializado en la memoria histórica de Lucy.
Tu tarea es leer un fragmento (chunk) de un documento y clasificar su naturaleza estricta en UNA sola de estas 4 categorías:

1. "dialogue": Interacción directa y transcrita entre un humano (User/Diego) y Lucy. Tiene forma de charla, preguntas, respuestas, o ping-pong conversacional.
2. "persona_notes": Texto descriptivo, ensayístico o analítico que describe CÓMO es Lucy, cómo piensa, su tono, su estilo, su identidad, o reflexiones sobre su forma de ser. No es una charla, es teoría o biografía sobre ella.
3. "operational_notes": Instrucciones técnicas, reglas de sistema, prohibiciones, límites éticos, o mandatos de diseño sobre cómo debe funcionar Lucy o cómo está estructurada (ej. "Nodo Técnico", "Límite de intervención", "Prohibiciones Operativas").
4. "noise": Basura, metadatos puros, fechas sueltas sin contexto, o texto ilegible/irrelevante que no aporta valor para destilar personalidad ni reglas.

Debes analizar el texto y devolver un JSON estricto con esta estructura:
{
  "label": "dialogue|persona_notes|operational_notes|noise",
  "confidence": int (1-10),
  "reason": "breve justificación de por qué elegiste esa etiqueta"
}

Responde SOLO con el JSON válido.
"""

def load_manifest() -> list:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def split_into_chunks(text: str) -> list:
    """
    Splits text into chunks. 
    A double newline usually denotes a paragraph or block in Markdown/TXT.
    Avoids extremely tiny chunks.
    """
    raw_chunks = re.split(r'\n\s*\n', text)
    chunks = []
    buffer = ""
    for rc in raw_chunks:
        clump = rc.strip()
        if not clump:
            continue
        # If the chunk is very small, append it to buffer to avoid over-fragmentation
        if len(buffer) < 100 or len(clump) < 50:
            buffer += "\n\n" + clump if buffer else clump
        else:
            if buffer:
                chunks.append(buffer)
            buffer = clump
    if buffer:
        chunks.append(buffer)
    return chunks

def classify_chunk(chunk_text: str) -> dict:
    """Invokes Ollama to classify a single chunk."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {
                "role": "user",
                "content": f"Clasifica el siguiente bloque de texto:\n\n{chunk_text}\n\n---\nRetorna SOLO el JSON solicitado."
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
            
        data = json.loads(content.strip())
        return data
        
    except Exception as e:
        print(f"⚠️ Classification error: {e}")
        return {"label": "noise", "confidence": 1, "reason": "Error during classification"}

def process_all_documents():
    os.makedirs(PARSED_DIR, exist_ok=True)
    manifest = load_manifest()
    
    # Load previously classified to allow resumed processing
    already_classified = set()
    if os.path.exists(CLASSIFIED_CHUNKS_PATH):
        with open(CLASSIFIED_CHUNKS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    already_classified.add(obj.get("chunk_id"))

    print(f"📖 Found {len(manifest)} documents to classify chunks for...")
    
    with open(CLASSIFIED_CHUNKS_PATH, "a", encoding="utf-8") as out_f:
        for doc in manifest:
            doc_id = doc["doc_id"]
            filepath = os.path.join(BASE_DIR, "runtime", "persona_lucy", doc["internal_path"])
            
            if not os.path.exists(filepath):
                print(f"⚠️ Warning: File {filepath} not found on disk.")
                continue
                
            # Read textual content
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            chunks = split_into_chunks(content)
            print(f"   → Doc {doc_id}: Splitted into {len(chunks)} chunks.")
            
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                if chunk_id in already_classified:
                    continue
                    
                print(f"      ► Classifying {chunk_id}...", end=" ")
                start_t = time.time()
                result = classify_chunk(chunk_text)
                dt = time.time() - start_t
                
                label = result.get("label", "noise")
                confidence = result.get("confidence", 0)
                reason = result.get("reason", "")
                
                print(f"[{label.upper()} - {confidence}/10] ({dt:.1f}s)")
                
                output_obj = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "content": chunk_text,
                    "label": label,
                    "confidence": confidence,
                    "reason": reason
                }
                
                out_f.write(json.dumps(output_obj, ensure_ascii=False) + "\n")
                out_f.flush()

    print(f"\n✅ Classification complete. Chunks appended to {CLASSIFIED_CHUNKS_PATH}")

if __name__ == "__main__":
    process_all_documents()
