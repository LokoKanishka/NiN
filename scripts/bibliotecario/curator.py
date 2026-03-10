"""
NIN Bibliotecario — Curator
Curación intelectual usando Ollama 14B como Demonio Librero.
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

CURATOR_SYSTEM_PROMPT = """Eres el Demonio Librero de NIN, curador intelectual doctoral para humanidades.
Recibirás una misión de investigación con su scope y catálogo bibliográfico.

Tu trabajo es producir una CURACIÓN INTELECTUAL estructurada, NO un resumen genérico.

Debes producir EXACTAMENTE este JSON:
{
  "interpretive_axes": [
    {"axis": "nombre del eje", "description": "explicación breve", "key_sources": ["fuentes clave"]}
  ],
  "conceptual_tensions": [
    {"tension": "descripción de la tensión", "poles": ["polo A", "polo B"]}
  ],
  "open_questions": ["preguntas abiertas relevantes"],
  "thesis_lines": [
    {
      "thesis": "enunciado de la tesis",
      "justification": "por qué es viable",
      "approach": "enfoque metodológico",
      "risk": "riesgo principal"
    }
  ],
  "risks_and_gaps": ["riesgos del enfoque general", "vacíos en la bibliografía"],
  "next_steps": ["pasos concretos siguientes"]
}

Reglas:
1. Propone entre 3 y 7 líneas de tesis, cada una DIFERENTE y ARGUMENTABLE.
2. Los ejes interpretativos deben ser académicamente relevantes.
3. Las tensiones conceptuales deben reflejar debates reales en humanidades.
4. NO inventes fuentes que no estén en el catálogo.
5. Sé riguroso pero propositivo: esto es para guiar una tesis doctoral.
6. Usa temperatura baja. Sé preciso."""


def curate(
    topic: str,
    scope: dict,
    catalog: list[dict],
    notes: str = "",
    timeout: int = 300,
) -> dict:
    """
    Runs the intellectual curation using Ollama 14B.
    Returns a structured curation dict.
    """
    # Build the user prompt with all context
    catalog_summary = json.dumps(catalog, ensure_ascii=False, indent=1)

    user_prompt = f"""MISIÓN DE INVESTIGACIÓN DOCTORAL

TEMA: {topic}

SCOPE:
{json.dumps(scope, ensure_ascii=False, indent=2)}

CATÁLOGO BIBLIOGRÁFICO ({len(catalog)} entradas):
{catalog_summary}

{'NOTAS ADICIONALES: ' + notes if notes else ''}

Produce tu curación intelectual completa en el formato JSON especificado."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": CURATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.1},
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

        curation = json.loads(content)
        return curation

    except requests.exceptions.ConnectionError:
        return {"error": "No se pudo conectar con Ollama. ¿Está corriendo?"}
    except json.JSONDecodeError as e:
        return {"error": f"Error parseando respuesta JSON: {e}", "raw_content": content}
    except Exception as e:
        return {"error": str(e)}


def generate_research_map(topic: str, curation: dict) -> str:
    """
    Generates a human-readable research map in Markdown from the curation.
    """
    lines = [
        f"# Mapa de Investigación: {topic}",
        "",
        f"*Generado por NIN Demonio Librero*",
        "",
    ]

    # Interpretive axes
    if curation.get("interpretive_axes"):
        lines.append("## Ejes Interpretativos")
        lines.append("")
        for ax in curation["interpretive_axes"]:
            lines.append(f"### {ax.get('axis', 'Sin nombre')}")
            lines.append(f"{ax.get('description', '')}")
            if ax.get("key_sources"):
                lines.append(f"**Fuentes clave:** {', '.join(ax['key_sources'])}")
            lines.append("")

    # Conceptual tensions
    if curation.get("conceptual_tensions"):
        lines.append("## Tensiones Conceptuales")
        lines.append("")
        for t in curation["conceptual_tensions"]:
            poles = " vs. ".join(t.get("poles", []))
            lines.append(f"- **{t.get('tension', '')}** ({poles})")
        lines.append("")

    # Open questions
    if curation.get("open_questions"):
        lines.append("## Preguntas Abiertas")
        lines.append("")
        for q in curation["open_questions"]:
            lines.append(f"- {q}")
        lines.append("")

    # Thesis lines
    if curation.get("thesis_lines"):
        lines.append("## Líneas de Tesis Propuestas")
        lines.append("")
        for i, th in enumerate(curation["thesis_lines"], 1):
            lines.append(f"### Tesis {i}: {th.get('thesis', '')}")
            lines.append(f"- **Justificación:** {th.get('justification', '')}")
            lines.append(f"- **Enfoque:** {th.get('approach', '')}")
            lines.append(f"- **Riesgo:** {th.get('risk', '')}")
            lines.append("")

    # Risks and gaps
    if curation.get("risks_and_gaps"):
        lines.append("## Riesgos y Vacíos")
        lines.append("")
        for r in curation["risks_and_gaps"]:
            lines.append(f"- {r}")
        lines.append("")

    # Next steps
    if curation.get("next_steps"):
        lines.append("## Próximos Pasos")
        lines.append("")
        for s in curation["next_steps"]:
            lines.append(f"1. {s}")
        lines.append("")

    return "\n".join(lines)
