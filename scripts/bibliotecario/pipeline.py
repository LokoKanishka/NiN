"""
NIN Bibliotecario — Pipeline
Orquestador end-to-end de misiones de investigación doctoral.
Puede correr independiente de n8n para testing y demos.
"""

import json
import os
import sys

# Add parent to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from bibliotecario import mission_manager as mm
from bibliotecario.scoping import scope_topic
from bibliotecario.sourcing import build_catalog
from bibliotecario.catalog_schema import catalog_to_json, BibEntry
from bibliotecario.curator import curate, generate_research_map
from bibliotecario.dossier import generate_dossier
from bibliotecario.hitl import notify_mission_event, send_telegram


def run_mission(
    topic: str,
    auto_approve: bool = False,
    notify: bool = True,
    subject_author: str = "",
) -> str:
    """
    Runs a complete mission pipeline end-to-end.

    Args:
        topic: The research topic
        auto_approve: If True, skips HITL pauses (for testing)
        notify: If True, sends Telegram notifications
        subject_author: Main author for primary/secondary classification

    Returns:
        mission_id of the completed mission
    """

    # === 1. CREATE MISSION ===
    print(f"\n{'='*60}")
    print(f"🆕 CREANDO MISIÓN: {topic}")
    print(f"{'='*60}\n")

    mission = mm.create_mission(topic=topic, source="pipeline")
    mission_id = mission["mission_id"]

    if notify:
        notify_mission_event(mission_id, "created", f"Tema: {topic}")

    # === 2. SCOPING ===
    print(f"\n🔬 SCOPING: Delimitando alcance...")
    mm.update_status(mission_id, "SCOPING")

    scope = scope_topic(topic)

    if scope.get("error"):
        print(f"⚠️ Scoping con advertencia: {scope['error']}")

    mm.update_scope(mission_id, scope)
    mm.save_artifact_json(mission_id, "scope.json", scope)

    print(f"   Tema refinado: {scope.get('topic_refined', topic)}")
    print(f"   Corpus primario: {scope.get('primary_corpus', [])}")
    print(f"   Queries: {scope.get('search_queries', [])}")

    if not auto_approve:
        from bibliotecario.hitl import request_scoping_review
        request_scoping_review(mission_id, scope)
        print(f"\n⏸️  Esperando aprobación del scope en Telegram...")
        print(f"   Usa: /aprobar {mission_id}")
        return mission_id  # Will resume when approved via Telegram

    # === 3. SOURCING ===
    print(f"\n🔍 SOURCING: Buscando bibliografía...")
    mm.update_status(mission_id, "SOURCING")

    if notify:
        notify_mission_event(mission_id, "sourcing", "Buscando bibliografía...")

    search_queries = scope.get("search_queries", [topic])
    max_sources = scope.get("max_sources", 25)

    # Determine subject author from topic if not provided
    if not subject_author:
        # Simple heuristic: first word that looks like a proper name
        words = topic.split()
        subject_author = words[0] if words else ""

    catalog_entries = build_catalog(
        topic=topic,
        subject_author=subject_author,
        search_queries=search_queries,
        max_sources=max_sources,
    )

    # Save catalog
    catalog_dicts = catalog_to_json(catalog_entries)
    mm.save_artifact_json(mission_id, "catalog.json", catalog_dicts)

    print(f"   Catálogo: {len(catalog_entries)} entradas guardadas")

    # === 4. CORPUS REVIEW ===
    print(f"\n📚 CORPUS REVIEW")
    mm.update_status(mission_id, "CORPUS_REVIEW")

    if not auto_approve:
        from bibliotecario.hitl import request_corpus_review
        request_corpus_review(mission_id, catalog_dicts)
        print(f"\n⏸️  Esperando aprobación del corpus en Telegram...")
        print(f"   Usa: /aprobar {mission_id}")
        return mission_id

    # === 5. CURATING ===
    print(f"\n🧠 CURATING: Curación intelectual del Demonio...")
    mm.update_status(mission_id, "CURATING")

    if notify:
        notify_mission_event(mission_id, "curating", "El Demonio está curando...")

    curation = curate(
        topic=topic,
        scope=scope,
        catalog=catalog_dicts,
    )

    mm.save_artifact_json(mission_id, "curation.json", curation)

    # Generate research map
    research_map = generate_research_map(topic, curation)
    mm.save_artifact(mission_id, "research_map.md", research_map)

    if curation.get("thesis_lines"):
        print(f"   Líneas de tesis: {len(curation['thesis_lines'])}")
    if curation.get("error"):
        print(f"⚠️ Curación con error: {curation['error']}")

    # === 6. DOSSIER ===
    print(f"\n📋 DOSSIER: Generando dossier final...")
    mm.update_status(mission_id, "DOSSIER")

    dossier = generate_dossier(mission_id)
    print(f"   Dossier generado: {len(dossier.splitlines())} líneas")

    # === 7. DONE ===
    mm.update_status(mission_id, "DONE")

    if notify:
        notify_mission_event(
            mission_id, "done",
            f"✅ Misión completada. Dossier disponible en runtime/missions/{mission_id}/dossier.md"
        )

    print(f"\n{'='*60}")
    print(f"✅ MISIÓN COMPLETADA: {mission_id}")
    print(f"   📁 runtime/missions/{mission_id}/")
    print(f"{'='*60}\n")

    return mission_id


def resume_mission(mission_id: str, auto_approve: bool = False) -> str:
    """
    Resumes a paused or hibernated mission from its current state.
    """
    mission = mm.get_mission(mission_id)
    status = mission["status"]
    topic = mission["topic"]

    print(f"\n🔄 Resumiendo misión {mission_id} desde estado {status}")

    if status == "HIBERNATED":
        # Resume from where it was
        # Check what artifacts exist to determine the right state
        if mm.load_artifact(mission_id, "curation.json"):
            mm.update_status(mission_id, "DOSSIER")
            return resume_mission(mission_id, auto_approve)
        elif mm.load_artifact(mission_id, "catalog.json"):
            mm.update_status(mission_id, "CORPUS_REVIEW")
            return resume_mission(mission_id, auto_approve)
        elif mm.load_artifact(mission_id, "scope.json"):
            mm.update_status(mission_id, "SCOPING")
            return resume_mission(mission_id, auto_approve)
        else:
            mm.update_status(mission_id, "QUEUED")
            return run_mission(topic, auto_approve)

    elif status == "SCOPING":
        # Scope approved, continue to sourcing
        scope = mm.load_artifact_json(mission_id, "scope.json")
        mm.update_status(mission_id, "SOURCING")

        search_queries = scope.get("search_queries", [topic])
        max_sources = scope.get("max_sources", 25)

        catalog_entries = build_catalog(
            topic=topic,
            subject_author=topic.split()[0] if topic else "",
            search_queries=search_queries,
            max_sources=max_sources,
        )
        catalog_dicts = catalog_to_json(catalog_entries)
        mm.save_artifact_json(mission_id, "catalog.json", catalog_dicts)

        mm.update_status(mission_id, "CORPUS_REVIEW")

        if not auto_approve:
            from bibliotecario.hitl import request_corpus_review
            request_corpus_review(mission_id, catalog_dicts)
            return mission_id

        return resume_mission(mission_id, auto_approve)

    elif status == "CORPUS_REVIEW":
        # Corpus approved, curate
        scope = mm.load_artifact_json(mission_id, "scope.json") or mission.get("scope", {})
        catalog_dicts = mm.load_artifact_json(mission_id, "catalog.json")

        mm.update_status(mission_id, "CURATING")
        curation = curate(topic=topic, scope=scope, catalog=catalog_dicts)
        mm.save_artifact_json(mission_id, "curation.json", curation)

        research_map = generate_research_map(topic, curation)
        mm.save_artifact(mission_id, "research_map.md", research_map)

        mm.update_status(mission_id, "DOSSIER")
        generate_dossier(mission_id)

        mm.update_status(mission_id, "DONE")
        notify_mission_event(mission_id, "done", "Misión completada.")
        return mission_id

    elif status == "SOURCING":
        mm.update_status(mission_id, "CORPUS_REVIEW")
        return resume_mission(mission_id, auto_approve)

    elif status == "CURATING":
        mm.update_status(mission_id, "DOSSIER")
        generate_dossier(mission_id)
        mm.update_status(mission_id, "DONE")
        return mission_id

    elif status == "DOSSIER":
        generate_dossier(mission_id)
        mm.update_status(mission_id, "DONE")
        return mission_id

    else:
        print(f"⚠️ Estado inesperado: {status}")
        return mission_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NIN Bibliotecario Pipeline")
    parser.add_argument("topic", nargs="?", default="Aristóteles y el motor inmóvil",
                        help="Research topic")
    parser.add_argument("--auto", action="store_true", help="Auto-approve all pauses")
    parser.add_argument("--no-notify", action="store_true", help="Disable Telegram notifications")
    parser.add_argument("--resume", type=str, help="Resume a mission by ID")
    parser.add_argument("--subject-author", type=str, default="", help="Main subject author")

    args = parser.parse_args()

    if args.resume:
        resume_mission(args.resume, auto_approve=args.auto)
    else:
        run_mission(
            topic=args.topic,
            auto_approve=args.auto,
            notify=not args.no_notify,
            subject_author=args.subject_author or "",
        )
