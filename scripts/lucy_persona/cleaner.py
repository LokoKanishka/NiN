"""
NIN — Lucy Persona Distiller: Cleaner Module

Takes structured turns from parsed_turns.jsonl, removes noise 
(short answers, non-conversational logs, markdown artifacts)
and outputs clean_turns.jsonl ready for LLM scoring.
"""

import os
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
CLEAN_DIR = os.path.join(RUNTIME_DIR, "clean")

PARSED_TURNS_PATH = os.path.join(PARSED_DIR, "parsed_turns.jsonl")
CLEAN_TURNS_PATH = os.path.join(CLEAN_DIR, "clean_turns.jsonl")

# Noise to strip
GARBAGE_PATTERNS = [
    r"^\[.*?\]",               # Log prefixes like [2026-03-10]
    r"====+",                  # Long separator lines
    r"^\*\*(?:User|Lucy|Assistant|Asistente).*\*\*\s*:?", # Residual bold headers
    r"^###\s+.*",              # Residual markdown headers
]


def clean_text(text: str) -> str:
    """Strips basic noise patterns from a turn."""
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        is_garbage = False
        for pattern in GARBAGE_PATTERNS:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                is_garbage = True
                break
        
        if not is_garbage:
            cleaned_lines.append(line)
            
    # remove leading/trailing whitespace but keep internal structure
    return "\n".join(cleaned_lines).strip()


def run_cleaner():
    """Reads parsed_turns, cleans them, and writes to clean_turns."""
    os.makedirs(CLEAN_DIR, exist_ok=True)
    
    if not os.path.exists(PARSED_TURNS_PATH):
        print(f"❌ Error: {PARSED_TURNS_PATH} not found. Run parser first.")
        return []

    clean_turns = []
    dropped_count = 0
    
    print(f"🧹 Starting cleaning pipeline on {PARSED_TURNS_PATH}...")
    
    with open(PARSED_TURNS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                turn = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            original_content = turn.get("content", "")
            role = turn.get("role", "unknown")
            
            cleaned_content = clean_text(original_content)
            
            # Drop logic
            # 1. Empty after cleaning
            if not cleaned_content:
                dropped_count += 1
                continue
                
            # 2. Too short (likely just "Ok", "Yes", useless for persona)
            if len(cleaned_content) < 15 and role == "assistant":
                dropped_count += 1
                continue
                
            # Update turn
            turn["content"] = cleaned_content
            turn["char_len"] = len(cleaned_content)
            
            clean_turns.append(turn)

    # Coalesce conversational flow if possible (pairing user + assistant)
    # We will just write them sequentially for now. The scorer can window them.
    with open(CLEAN_TURNS_PATH, "w", encoding="utf-8") as f:
        for t in clean_turns:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"✅ Cleaning complete. Kept {len(clean_turns)} turns, dropped {dropped_count} noisy or useless turns.")
    print(f"📁 Output saved to {CLEAN_TURNS_PATH}")
    
    return clean_turns


if __name__ == "__main__":
    run_cleaner()
