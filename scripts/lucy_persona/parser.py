"""
NIN — Lucy Persona Distiller: Parser Module

Converts raw documents into structured conversational turns.
Supports JSONL, Markdown, and TXT with common delimiter heuristics.
Outputs to runtime/persona_lucy/parsed/parsed_turns.jsonl
"""

import os
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
RAW_DOCS_DIR = os.path.join(RUNTIME_DIR, "raw_docs")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
MANIFEST_PATH = os.path.join(RUNTIME_DIR, "source_manifest.json")
PARSED_TURNS_PATH = os.path.join(PARSED_DIR, "parsed_turns.jsonl")

# Heuristics for Markdown/TXT turning
USER_MARKERS = [
    r"^(?:\*\*)?User:?(?:\*\*)?",
    r"^###\s+User",
    r"^##\s+User",
    r"^(?:\*\*)?USUARIO:?(?:\*\*)?",
    r"^(?:\*\*)?Usuario:?(?:\*\*)?",
]
ASSISTANT_MARKERS = [
    r"^(?:\*\*)?Assistant:?(?:\*\*)?",
    r"^(?:\*\*)?Lucy:?(?:\*\*)?",
    r"^###\s+Assistant",
    r"^(?:\*\*)?Asistente:?(?:\*\*)?",
    r"^###\s+Lucy",
]


def load_manifest() -> list:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def parse_jsonl(filepath: str, doc_id: str) -> list:
    """Parses a pre-formatted JSONL chat log."""
    turns = []
    has_error = False
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                role = data.get("role", "").lower()
                content = data.get("content", "")
                if role in ["user", "assistant"] and content:
                    turns.append({
                        "doc_id": doc_id,
                        "conversation_id": f"conv_{doc_id}",
                        "turn_index": idx,
                        "role": role,
                        "content": content.strip(),
                        "char_len": len(content),
                        "parser_confidence": 1.0  # Perfect confidence for structured JSONL
                    })
            except json.JSONDecodeError:
                has_error = True
    
    if has_error:
         print(f"⚠️ Warning: Some lines in {filepath} were not valid JSON.")
    return turns


def is_marker(line: str, markers: list) -> bool:
    line_stripped = line.strip()
    for marker in markers:
        if re.match(marker, line_stripped, re.IGNORECASE):
            return True
    return False


def parse_text(filepath: str, doc_id: str) -> list:
    """Parses a generic markdown or text file using heuristics."""
    turns = []
    current_role = None
    current_content = []
    turn_index = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            # Detect User
            if is_marker(line_str, USER_MARKERS):
                # Flush previous turn
                if current_role and current_content:
                    content_joined = "\n".join(current_content).strip()
                    if content_joined:
                        turns.append({
                            "doc_id": doc_id,
                            "conversation_id": f"conv_{doc_id}",
                            "turn_index": turn_index,
                            "role": current_role,
                            "content": content_joined,
                            "char_len": len(content_joined),
                            "parser_confidence": 0.8
                        })
                        turn_index += 1
                current_role = "user"
                current_content = []
                # Don't add the marker itself to content
                continue
            
            # Detect Assistant
            elif is_marker(line_str, ASSISTANT_MARKERS):
                if current_role and current_content:
                    content_joined = "\n".join(current_content).strip()
                    if content_joined:
                        turns.append({
                            "doc_id": doc_id,
                            "conversation_id": f"conv_{doc_id}",
                            "turn_index": turn_index,
                            "role": current_role,
                            "content": content_joined,
                            "char_len": len(content_joined),
                            "parser_confidence": 0.8
                        })
                        turn_index += 1
                current_role = "assistant"
                current_content = []
                continue

            # If we are in a turn, buffer content
            if current_role:
                current_content.append(line.rstrip('\n'))

    # Flush last turn
    if current_role and current_content:
        content_joined = "\n".join(current_content).strip()
        if content_joined:
            turns.append({
                "doc_id": doc_id,
                "conversation_id": f"conv_{doc_id}",
                "turn_index": turn_index,
                "role": current_role,
                "content": content_joined,
                "char_len": len(content_joined),
                "parser_confidence": 0.8
            })

    # If heuristic completely failed and found 0 turns, wrap the whole doc
    # with lower confidence as an assistant payload (fallback)
    if not turns:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                turns.append({
                    "doc_id": doc_id,
                    "conversation_id": f"conv_{doc_id}",
                    "turn_index": 0,
                    "role": "unknown",  # We don't know who said what
                    "content": content,
                    "char_len": len(content),
                    "parser_confidence": 0.2
                })

    return turns


def parse_all():
    """Reads manifest, parses all raw docs, and dumps to parsed_turns.jsonl"""
    os.makedirs(PARSED_DIR, exist_ok=True)
    manifest = load_manifest()
    all_turns = []

    print(f"📖 Found {len(manifest)} documents to parse...")
    for doc in manifest:
        filepath = os.path.join(BASE_DIR, "runtime", "persona_lucy", doc["internal_path"])
        doc_id = doc["doc_id"]
        
        if not os.path.exists(filepath):
            print(f"⚠️ Warning: File {filepath} declared in manifest but not found on disk.")
            continue
            
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".jsonl":
            turns = parse_jsonl(filepath, doc_id)
        else:
            turns = parse_text(filepath, doc_id)
            
        print(f"   → Doc {doc_id}: Extracted {len(turns)} turns.")
        all_turns.extend(turns)

    # Dump all parsed turns
    # We overwrite the file to ensure idempotency across runs
    with open(PARSED_TURNS_PATH, "w", encoding="utf-8") as f:
        for turn in all_turns:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")

    print(f"✅ Parsing complete. {len(all_turns)} total turns written to {PARSED_TURNS_PATH}")
    return all_turns

if __name__ == "__main__":
    parse_all()
