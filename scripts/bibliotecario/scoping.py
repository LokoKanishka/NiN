"""
NIN Bibliotecario — Scoping
Delimitación del alcance de una misión de investigación doctoral.
Usa Ollama 14B para convertir un tema libre en un scope gobernable.
"""

import json
import os
import requests
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
load_dotenv(os.path.join(BASE_DIR, ".env"))

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:14b-instruct-q8_0"

SCOPING_SYSTEM_PROMPT = """Eres un asesor doctoral experto en humanidades y filosofía.
Tu tarea es recibir un tema de investigación y producir un SCOPE estructurado.

Reglas:
1. Identifica el corpus primario: obras originales del autor principal.
2. Identifica el corpus secundario: comentarios, monografías, artículos clave.
3. Sugiere enfoques posibles: filológico, metafísico, ético, político, recepción, comparativo.
4. Sugiere idiomas prioritarios para las fuentes.
5. Propone un límite razonable de fuentes para un corpus gobernable (15-30).
6. NO inventes autores ni obras que no existan.

Responde SOLO con JSON válido, sin explicaciones fuera del JSON:
{
  "topic_refined": "tema refinado en una oración",
  "primary_corpus": ["lista de obras primarias clave"],
  "secondary_themes": ["temas secundarios a investigar"],
  "suggested_focus": ["enfoques sugeridos"],
  "language_priority": ["códigos de idioma: es, en, el, la, de, fr, it"],
  "max_sources": 25,
  "search_queries": ["3-5 queries de búsqueda óptimas para encontrar bibliografía"]
}"""


def scope_topic(topic: str, timeout: int = 120) -> dict:
    """
    Uses Ollama 14B to convert a free-text topic into a structured scope.
    Returns a scope dict.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SCOPING_SYSTEM_PROMPT},
            {"role": "user", "content": f"Tema de investigación doctoral: {topic}"},
        ],
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")

        # Extract JSON from response (handle possible markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        scope = json.loads(content)
        return scope

    except requests.exceptions.ConnectionError:
        return {
            "error": "No se pudo conectar con Ollama. ¿Está corriendo?",
            "topic_refined": topic,
            "primary_corpus": [],
            "secondary_themes": [],
            "suggested_focus": [],
            "language_priority": ["es", "en"],
            "max_sources": 20,
            "search_queries": [topic],
        }
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "error": f"Error parseando respuesta de Ollama: {e}",
            "topic_refined": topic,
            "primary_corpus": [],
            "secondary_themes": [],
            "suggested_focus": [],
            "language_priority": ["es", "en"],
            "max_sources": 20,
            "search_queries": [topic],
        }
    except Exception as e:
        return {
            "error": str(e),
            "topic_refined": topic,
            "primary_corpus": [],
            "secondary_themes": [],
            "suggested_focus": [],
            "language_priority": ["es", "en"],
            "max_sources": 20,
            "search_queries": [topic],
        }
