"""
NIN Bibliotecario — Dossier Generator
Genera el dossier final académico a partir de los artefactos de la misión.
"""

import json
import os
from datetime import datetime
from . import mission_manager as mm


def generate_dossier(mission_id: str) -> str:
    """
    Assembles the final academic dossier from mission artifacts.
    Returns the dossier content as Markdown.
    """
    mission = mm.get_mission(mission_id)
    topic = mission.get("topic", "Sin tema")
    scope = mission.get("scope", {})

    # Load artifacts
    catalog_data = mm.load_artifact_json(mission_id, "catalog.json")
    curation_data = mm.load_artifact_json(mission_id, "curation.json")

    # Separate primary and secondary sources
    if isinstance(catalog_data, list):
        catalog = catalog_data
    else:
        catalog = catalog_data.get("entries", []) if isinstance(catalog_data, dict) else []

    primaries = [e for e in catalog if e.get("type") == "primary"]
    secondaries = [e for e in catalog if e.get("type") == "secondary"]

    # Build dossier
    lines = [
        f"# Dossier de Investigación Doctoral",
        f"## {topic}",
        "",
        f"**Misión:** `{mission_id}`",
        f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Estado:** {mission.get('status', 'N/A')}",
        f"**Generado por:** NIN Demonio Librero (Ollama 14B)",
        "",
        "---",
        "",
    ]

    # 1. Executive Summary
    lines.append("## 1. Resumen Ejecutivo")
    lines.append("")
    if curation_data.get("interpretive_axes"):
        axes_names = [a.get("axis", "") for a in curation_data["interpretive_axes"]]
        lines.append(
            f"Este dossier presenta un análisis estructurado del tema \"{topic}\", "
            f"organizado en torno a {len(axes_names)} ejes interpretativos: "
            f"{', '.join(axes_names)}. "
            f"Se identificaron {len(primaries)} fuentes primarias y {len(secondaries)} fuentes secundarias."
        )
    else:
        lines.append(f"Investigación sobre: {topic}. "
                     f"Catálogo: {len(primaries)} primarias, {len(secondaries)} secundarias.")
    lines.append("")

    # 2. Problem Delimitation
    lines.append("## 2. Delimitación del Problema")
    lines.append("")
    if scope.get("topic_refined"):
        lines.append(f"**Tema refinado:** {scope['topic_refined']}")
        lines.append("")
    if scope.get("suggested_focus"):
        lines.append("**Enfoques considerados:**")
        for f in scope["suggested_focus"]:
            lines.append(f"- {f}")
        lines.append("")

    # 3. Primary Sources
    lines.append("## 3. Fuentes Primarias")
    lines.append("")
    if primaries:
        lines.append("| # | Autor | Título | Año | Idioma | Subtipo |")
        lines.append("|:--|:------|:-------|:----|:-------|:--------|")
        for i, p in enumerate(primaries, 1):
            lines.append(
                f"| {i} | {p.get('author', '?')} | {p.get('title', '?')} | "
                f"{p.get('year', '?')} | {p.get('language', '?')} | {p.get('subtype', '?')} |"
            )
    else:
        lines.append("*No se identificaron fuentes primarias.*")
    lines.append("")

    # 4. Secondary Sources
    lines.append("## 4. Fuentes Secundarias")
    lines.append("")
    if secondaries:
        lines.append("| # | Autor | Título | Año | Tipo |")
        lines.append("|:--|:------|:-------|:----|:-----|")
        for i, s in enumerate(secondaries, 1):
            lines.append(
                f"| {i} | {s.get('author', '?')} | {s.get('title', '?')} | "
                f"{s.get('year', '?')} | {s.get('subtype', '?')} |"
            )
    else:
        lines.append("*No se identificaron fuentes secundarias.*")
    lines.append("")

    # 5. Interpretive Axes
    lines.append("## 5. Ejes Interpretativos")
    lines.append("")
    if curation_data.get("interpretive_axes"):
        for ax in curation_data["interpretive_axes"]:
            lines.append(f"### {ax.get('axis', 'Sin nombre')}")
            lines.append(f"{ax.get('description', '')}")
            if ax.get("key_sources"):
                lines.append(f"**Fuentes clave:** {', '.join(ax['key_sources'])}")
            lines.append("")
    else:
        lines.append("*Curación pendiente.*")
        lines.append("")

    # 6. Thesis Lines
    lines.append("## 6. Líneas de Tesis Propuestas")
    lines.append("")
    if curation_data.get("thesis_lines"):
        for i, th in enumerate(curation_data["thesis_lines"], 1):
            lines.append(f"### Tesis {i}: {th.get('thesis', '')}")
            lines.append(f"- **Justificación:** {th.get('justification', '')}")
            lines.append(f"- **Enfoque metodológico:** {th.get('approach', '')}")
            lines.append(f"- **Riesgo principal:** {th.get('risk', '')}")
            lines.append("")
    else:
        lines.append("*Curación pendiente.*")
        lines.append("")

    # 7. Risks and Gaps
    lines.append("## 7. Riesgos y Vacíos")
    lines.append("")
    if curation_data.get("risks_and_gaps"):
        for r in curation_data["risks_and_gaps"]:
            lines.append(f"- {r}")
    else:
        lines.append("*No identificados.*")
    lines.append("")

    # Conceptual Tensions
    if curation_data.get("conceptual_tensions"):
        lines.append("### Tensiones Conceptuales")
        lines.append("")
        for t in curation_data["conceptual_tensions"]:
            poles = " vs. ".join(t.get("poles", []))
            lines.append(f"- **{t.get('tension', '')}** ({poles})")
        lines.append("")

    # 8. Next Steps
    lines.append("## 8. Próximos Pasos")
    lines.append("")
    if curation_data.get("next_steps"):
        for i, s in enumerate(curation_data["next_steps"], 1):
            lines.append(f"{i}. {s}")
    else:
        lines.append("1. Validar el corpus con el director de tesis.")
        lines.append("2. Ampliar fuentes en idiomas faltantes.")
        lines.append("3. Seleccionar una línea de tesis y profundizar.")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Dossier generado por NIN Bibliotecario Doctoral MVP — {datetime.now().isoformat()}*")

    dossier_content = "\n".join(lines)

    # Save to mission directory
    mm.save_artifact(mission_id, "dossier.md", dossier_content)
    mm._log_event(mission_id, "DOSSIER_GENERATED", f"{len(lines)} lines")

    return dossier_content
