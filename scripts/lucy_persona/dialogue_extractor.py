"""
NIN — Lucy Persona Distiller: Dialogue Extractor Module

Reads runtime/persona_lucy/parsed/classified_chunks.jsonl
Extracts conversational turns (user/assistant) ONLY from chunks
labeled as "direct_dialogue".

Outputs to runtime/persona_lucy/parsed/parsed_turns.jsonl
"""

import os
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
PARSED_DIR = os.path.join(RUNTIME_DIR, "parsed")
CLASSIFIED_CHUNKS_PATH = os.path.join(PARSED_DIR, "classified_chunks.jsonl")
PARSED_TURNS_PATH = os.path.join(PARSED_DIR, "parsed_turns.jsonl")

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


def is_marker(line: str, markers: list) -> bool:
    line_stripped = line.strip()
    for marker in markers:
        if re.match(marker, line_stripped, re.IGNORECASE):
            return True
    return False

def parse_chunk_text(text: str, doc_id: str, chunk_id: str, turn_index_start: int) -> list:
    """Parses a generic text block using heuristics."""
    turns = []
    current_role = None
    current_content = []
    turn_index = turn_index_start

    for line in text.splitlines():
        line_str = line.strip()
        # Detect User
        if is_marker(line_str, USER_MARKERS):
            if current_role and current_content:
                content_joined = "\n".join(current_content).strip()
                if content_joined:
                    turns.append({
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
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
            continue
        
        # Detect Assistant
        elif is_marker(line_str, ASSISTANT_MARKERS):
            if current_role and current_content:
                content_joined = "\n".join(current_content).strip()
                if content_joined:
                    turns.append({
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
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

        # Buffered content
        if current_role:
            current_content.append(line.rstrip('\n'))

    # Flush last turn
    if current_role and current_content:
        content_joined = "\n".join(current_content).strip()
        if content_joined:
            turns.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "conversation_id": f"conv_{doc_id}",
                "turn_index": turn_index,
                "role": current_role,
                "content": content_joined,
                "char_len": len(content_joined),
                "parser_confidence": 0.8
            })

    # If heuristic failed completely and found 0 turns, wrap the whole chunk
    # with lower confidence as an assistant payload IF IT CONTAINS DIALOGUE
    if not turns:
        content = text.strip()
        if content:
            turns.append({
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "conversation_id": f"conv_{doc_id}",
                "turn_index": turn_index_start,
                "role": "unknown",
                "content": content,
                "char_len": len(content),
                "parser_confidence": 0.2
            })

    return turns

def extract_dialogue_turns():
    if not os.path.exists(CLASSIFIED_CHUNKS_PATH):
        print(f"❌ Error: {CLASSIFIED_CHUNKS_PATH} not found. Run document_classifier.py first.")
        return []

    all_turns = []
    turn_counter = 0

    print("📖 Reading classified chunks...")
    with open(CLASSIFIED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            
            # ONLY Process 'direct_dialogue' chunks!
            if chunk.get("label") != "direct_dialogue":
                continue
            
            turns = parse_chunk_text(
                text=chunk.get("content", ""),
                doc_id=chunk.get("doc_id", "unknown"),
                chunk_id=chunk.get("chunk_id", "unknown"),
                turn_index_start=turn_counter
            )
            
            all_turns.extend(turns)
            turn_counter += len(turns)

    # Dump all parsed turns
    with open(PARSED_TURNS_PATH, "w", encoding="utf-8") as f:
        for turn in all_turns:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")

    print(f"✅ Extraction complete. {len(all_turns)} total dialogue turns written to {PARSED_TURNS_PATH}")
    return all_turns

if __name__ == "__main__":
    extract_dialogue_turns()
