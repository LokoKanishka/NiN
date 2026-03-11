"""
NIN — Lucy Persona Distiller: Main Orchestrator

Links ingest, parser, cleaner, scorer, profile, builder, and evaluator 
to process a raw document through the full distillation pipeline.
"""

import os
import argparse
from ingest import ingest_document
from parser import parse_all
from cleaner import run_cleaner
from scorer import run_scorer
from profile_extractor import extract_profile
from openclaw_builder import build_seed
from evaluator import run_evaluator

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")

def run_pipeline(input_file: str = None, max_scores: int = 15):
    print("=" * 60)
    print("🔥 NIN LUCY PERSONA DISTILLER 🔥")
    print("=" * 60)
    
    # 1. Ingest
    print("\n[ FASE 1: INGESTA ]")
    if input_file:
        try:
            ingest_document(input_file)
        except Exception as e:
            print(f"❌ Aborting pipeline: {e}")
            return
    else:
        print("ℹ️ No new input file provided. Using existing raw_docs manifest.")

    # 2. Parse
    print("\n[ FASE 2: PARSEO ]")
    parse_all()

    # 3. Clean
    print("\n[ FASE 3: LIMPIEZA ]")
    run_cleaner()

    # 4. Score
    print("\n[ FASE 4: SCORING (Demonio Local) ]")
    run_scorer(max_items=max_scores)

    # 5. Profile
    print("\n[ FASE 5: EXTRACCIÓN PERFIL ]")
    extract_profile(max_examples=10)

    # 6. Builder
    print("\n[ FASE 6: OPENCLAW SEED ]")
    build_seed(max_examples=5)

    # 7. Evaluate
    print("\n[ FASE 7: EVALUACIÓN EMPÍRICA ]")
    run_evaluator()

    print("\n" + "=" * 60)
    print("✅ DISTILLATION PIPELINE COMLETE")
    print(f"📁 Output files are ready in: {os.path.join(RUNTIME_DIR, 'final')}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Lucy Persona Pipeline")
    parser.add_argument("--input", type=str, help="Path to initial raw chat log file (markdown/txt/jsonl). If omitted, processes existing manifest.", default=None)
    parser.add_argument("--score-limit", type=int, default=15, help="Limit how many turns are scored per run to save time.")
    
    args = parser.parse_args()
    
    run_pipeline(input_file=args.input, max_scores=args.score_limit)
