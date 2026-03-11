"""
NIN — Lucy Persona Distiller: OpenClaw Builder

Reads the persona profile and top examples to build the final
OpenClaw seed string (lucy_openclaw_seed.md) and curates
a jsonl bundle (lucy_examples_curated.jsonl).
"""

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
SCORED_DIR = os.path.join(RUNTIME_DIR, "scored")
FINAL_DIR = os.path.join(RUNTIME_DIR, "final")

SCORED_EXAMPLES_PATH = os.path.join(SCORED_DIR, "scored_examples.jsonl")
PROFILE_PATH = os.path.join(FINAL_DIR, "lucy_persona_profile.md")
OPENCLAW_SEED_PATH = os.path.join(FINAL_DIR, "lucy_openclaw_seed.md")
OPENCLAW_SEED_JSON_PATH = os.path.join(FINAL_DIR, "lucy_openclaw_seed.json")
CURATED_EXAMPLES_PATH = os.path.join(FINAL_DIR, "lucy_examples_curated.jsonl")


def build_seed(max_examples=5):
    """
    Constructs the OpenClaw system prompt bundle.
    """
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # 1. Load Profile
    profile_content = ""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            profile_content = f.read().strip()
    else:
        profile_content = "*(Perfil pendiente de generación)*"

    # 2. Get subset of examples oriented specifically to OpenClaw (openclaw_utility)
    curated_items = []
    if os.path.exists(SCORED_EXAMPLES_PATH):
        with open(SCORED_EXAMPLES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("status") == "accepted":
                            curated_items.append(data)
                    except json.JSONDecodeError:
                        pass
                        
    # Sort strictly by openclaw_utility
    def oc_sort_key(x):
        return x.get("metrics", {}).get("openclaw_utility", 0)
        
    curated_items.sort(key=oc_sort_key, reverse=True)
    top_examples = curated_items[:max_examples]
    
    print(f"📦 Assembling OpenClaw Seed with profile + top {len(top_examples)} canonical examples.")

    # 3. Save purely curated items to independent JSONL
    with open(CURATED_EXAMPLES_PATH, "w", encoding="utf-8") as f:
        for item in curated_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    # 4. Construct Markdown Seed
    lines = []
    lines.append("# SYSTEM PROMPT SEED: LUCY")
    lines.append("\n*Instrucciones del Sistema para configurar el personaje en OpenClaw.*")
    lines.append("\n---\n")
    
    lines.append("## IDENTIDAD BASE Y REGLAS")
    lines.append("Estás operando bajo la personalidad de **Lucy**.")
    lines.append("\n### Rasgos Centrales")
    # Instead of pulling the full giant profile, we inject it logically.
    # The profile already has the traits structured.
    lines.append(profile_content)
    
    lines.append("\n---\n")
    lines.append("## EJEMPLOS CANÓNICOS DE CONDUCTA (FEW-SHOT)")
    lines.append("Responde siempre respetando estrictamente el estilo demostrado en las siguientes interacciones:\n")
    
    if top_examples:
        for idx, ex in enumerate(top_examples, 1):
            lines.append(f"### Ejemplo {idx}")
            if ex.get("context_prompt"):
                lines.append(f"**Usuario:**\n{ex['context_prompt']}\n")
            lines.append(f"**Lucy:**\n{ex['content']}\n")
    else:
        lines.append("*(No hay ejemplos empíricos listos)*\n")

    seed_md = "\n".join(lines)
    
    with open(OPENCLAW_SEED_PATH, "w", encoding="utf-8") as f:
         f.write(seed_md)

    # 5. Optional JSON version for programmatic injection
    seed_json = {
        "name": "Lucy",
        "system_prompt": seed_md,
        "temperature": 0.3
    }
    with open(OPENCLAW_SEED_JSON_PATH, "w", encoding="utf-8") as f:
         json.dump(seed_json, f, indent=2, ensure_ascii=False)
         
    print(f"✅ OpenClaw bundle finalized at:\n  - {OPENCLAW_SEED_PATH}\n  - {CURATED_EXAMPLES_PATH}")


if __name__ == "__main__":
    build_seed()
