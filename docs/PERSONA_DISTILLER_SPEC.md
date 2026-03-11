# Lucy Persona Distiller — Specifications

**Pipeline Name**: Lucy Persona Distiller
**Version**: 1.0.0-MVP
**Target System**: Local (Qwen 2.5 Coder 14B via Ollama)
**Output Target**: OpenClaw (via Markdown seed and JSONL bundles)

## 1. Directory Structure
All data processing must happen strictly inside `runtime/persona_lucy/` to avoid polluting the repo logic.
- `raw_docs/`: Source chat logs (`.md`, `.txt`, `.jsonl`).
- `parsed/`: Intermediate format (split by conversational turns).
- `clean/`: Filtered turns (noise removed).
- `scored/`: Outputs from the local LLM scoring passes.
- `final/`: Destilations (Markdown seed, curated examples, profiles, eval report).

## 2. Data Contracts

### 2.1 Parsed & Clean Turn (JSONL)
Each line represents a single distinct user or assistant utterance.
```json
{
  "doc_id": "string",
  "conversation_id": "string",
  "turn_index": "integer",
  "role": "user | assistant",
  "content": "string",
  "char_len": "integer",
  "parser_confidence": "float"
}
```

### 2.2 Scored Example (JSONL)
Each line represents an Assistant turn (often paired with the preceding User turn) evaluated by the LLM.
```json
{
  "doc_id": "string",
  "turn_index": "integer",
  "content": "string",
  "context_prompt": "string (optional)",
  "metrics": {
    "persona_value": "integer (1-10)",
    "style_quality": "integer (1-10)",
    "coherence": "integer (1-10)",
    "warmth": "integer (1-10)",
    "clarity": "integer (1-10)",
    "didactic_structure": "integer (1-10)",
    "privacy_risk": "integer (1-10)",
    "lora_utility": "integer (1-10)",
    "openclaw_utility": "integer (1-10)"
  },
  "rationale": "string",
  "status": "accepted | rejected | doubtful"
}
```

### 2.3 Persona Profile (`lucy_persona_profile.md`)
Narrative distillation of the accepted examples. Must include:
- General Voice and Tone
- Explanatory Style
- Ordering Mechanics (Didactics)
- Affective Traits (Warmth, Closeness)
- Firmness/Critical Traits
- Avoidances (What Lucy *doesn't* do)
- Known Pitfalls to avoid (LLMisms to reject)
- Core identity vectors

### 2.4 OpenClaw Seed (`lucy_openclaw_seed.md`)
The executable string bundle to paste into the System Prompt config of OpenClaw. Contains:
- Core System Prompt (The distilled essence)
- Boundary Rules
- Stylistic Rules (Do's and Don'ts)
- Curated canonical few-shot examples (drawn from accepted scores)
- Minimal seed memory (if any context must persist absolutely)

## 3. Rules of Engagement
- **No external APIs**: Force local Ollama usage.
- **No LORA output**: Focus purely on the Persona Profile and OpenClaw Seed. The accepted scores can later be fed into a LoRA pipeline manually if desired.
- **Privacy First**: Examples flagged with high `privacy_risk` during scoring must be forcefully routed to `lucy_rejected_examples.jsonl`.
