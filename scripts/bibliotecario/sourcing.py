"""
NIN Bibliotecario — Sourcing
Búsqueda bibliográfica usando SearXNG local y clasificación para humanidades.
"""

import json
import os
import requests
from dotenv import load_dotenv
from .catalog_schema import BibEntry, deduplicate, normalize_text

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SEARXNG_URL = "http://127.0.0.1:8080/search"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

CLASSIFICATION_PROMPT = """Eres un bibliotecario académico experto en humanidades.
Recibirás una lista de resultados de búsqueda web sobre un tema de investigación.
Tu tarea es extraer referencias bibliográficas válidas y clasificarlas.

Reglas CRÍTICAS de Clasificación:
1. Extrae SOLO referencias que sean REALES (autor, título, año verificables).
2. Clasifica "type" ESTRICTAMENTE como "primary" u "obra original" SOLO si es el texto original del autor estudiado. Enciclopedias (Stanford Encyclopedia of Philosophy, IEP, Wikipedia), diccionarios y comentarios son SIEMPRE "secondary".
3. Asigna un subtipo: obra_original, traduccion, edicion_critica, comentario, monografia, articulo, capitulo, tesis, compilacion, enciclopedia.
4. Asigna un "quality_tier" basado en la fuente:
   - "primaria": solo para obras originales/traducciones del autor (type="primary").
   - "academica_alta": ediciones académicas, Oxford, Cambridge, JSTOR, SEP (Stanford), IEP, revistas peer-reviewed.
   - "contextual": Wikipedia, Philopedia, blogs, sitios generales.
5. NO inventes referencias que no aparezcan en los resultados. Incluye DOI o ISBN si están presentes.

Responde SOLO con JSON válido, un array de objetos extactamente con esta estructura:
[
  {
    "author": "Nombre del autor",
    "title": "Título de la obra",
    "year": "año",
    "type": "primary|secondary",
    "subtype": "subtipo",
    "language": "código iso",
    "source_url": "url si hay",
    "identifier": "DOI o ISBN si hay",
    "identifier_type": "doi|isbn|",
    "edition": "edición si se conoce",
    "notes": "nota breve",
    "quality_tier": "primaria|academica_alta|contextual"
  }
]"""


def search_searxng(query: str, categories: str = "general", max_results: int = 10) -> list[dict]:
    """
    Searches using local SearXNG instance.
    Returns list of result dicts with title, url, content.
    """
    params = {
        "q": query,
        "format": "json",
        "categories": categories,
        "language": "es",
        "engines": "google,duckduckgo,wikipedia",
    }
    try:
        resp = requests.get(SEARXNG_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:max_results]
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in results
        ]
    except Exception as e:
        print(f"⚠️ Error buscando en SearXNG: {e}")
        return []


def classify_results(
    topic: str,
    subject_author: str,
    search_results: list[dict],
    timeout: int = 180,
) -> list[BibEntry]:
    """
    Uses Ollama 14B to classify search results into bibliography entries.
    """
    if not search_results:
        return []

    # Prepare the results for the LLM
    results_text = json.dumps(search_results, ensure_ascii=False, indent=2)

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Tema: {topic}\n"
                    f"Autor principal del tema: {subject_author}\n\n"
                    f"Resultados de búsqueda:\n{results_text}"
                ),
            },
        ],
        "stream": False,
        "options": {"temperature": 0.0},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        entries_data = json.loads(content)
        if not isinstance(entries_data, list):
            entries_data = [entries_data]

        entries = []
        for i, ed in enumerate(entries_data):
            entry = BibEntry.from_dict(ed)
            entry.id = f"cat_{i+1:03d}"
            entries.append(entry)

        return entries

    except Exception as e:
        print(f"⚠️ Error clasificando resultados: {e}")
        return []


def build_catalog(
    topic: str,
    subject_author: str,
    search_queries: list[str],
    max_sources: int = 25,
) -> list[BibEntry]:
    """
    Full sourcing pipeline:
    1. Search SearXNG with multiple queries
    2. Classify results with LLM
    3. Deduplicate
    4. Return catalog
    """
    all_results = []
    for query in search_queries:
        print(f"🔍 Buscando: {query}")
        results = search_searxng(query, max_results=8)
        all_results.extend(results)
        print(f"   → {len(results)} resultados")

    if not all_results:
        print("⚠️ No se encontraron resultados de búsqueda.")
        return []

    print(f"📚 Clasificando {len(all_results)} resultados con LLM...")
    entries = classify_results(topic, subject_author, all_results)

    print(f"🧹 Deduplicando {len(entries)} entradas...")
    entries = deduplicate(entries)

    # Re-index
    for i, entry in enumerate(entries):
        entry.id = f"cat_{i+1:03d}"

    # Trim to max
    if len(entries) > max_sources:
        entries = entries[:max_sources]

    primaries = [e for e in entries if e.type == "primary"]
    secondaries = [e for e in entries if e.type == "secondary"]
    print(f"✅ Catálogo: {len(primaries)} primarias, {len(secondaries)} secundarias")

    return entries
