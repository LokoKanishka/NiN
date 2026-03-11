"""
NIN — Lucy Persona Distiller: Ingest Module

Handles the ingestion of raw documents (.md, .txt, .jsonl),
copies them to runtime/persona_lucy/raw_docs/ and updates
source_manifest.json with traceability metadata.
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
try:
    import docx
except ImportError:
    docx = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime", "persona_lucy")
RAW_DOCS_DIR = os.path.join(RUNTIME_DIR, "raw_docs")
MANIFEST_PATH = os.path.join(RUNTIME_DIR, "source_manifest.json")


def _get_file_hash(filepath: str) -> str:
    """Returns the SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()


def load_manifest() -> list:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_manifest(manifest: list):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def ingest_document(source_filepath: str, name_override: str = None) -> dict:
    """
    Ingests a document into the persona pipeline.
    """
    if not os.path.exists(source_filepath):
        raise FileNotFoundError(f"Source file not found: {source_filepath}")

    # Ensure directories exist
    os.makedirs(RAW_DOCS_DIR, exist_ok=True)

    filename = os.path.basename(source_filepath)
    name = name_override if name_override else filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".txt", ".md", ".jsonl", ".docx"]:
        print(f"⚠️ Warning: Non-standard extension '{ext}' ingested.")

    file_size = os.path.getsize(source_filepath)
    file_hash = _get_file_hash(source_filepath)

    # Check if already ingested
    manifest = load_manifest()
    for entry in manifest:
        if entry["hash"] == file_hash:
            print(f"ℹ️ File '{filename}' is already ingested as '{entry['doc_id']}'. Skipping.")
            return entry

    # Generate internal doc_id
    doc_id = f"doc_{file_hash[:8]}"
    
    if ext == ".docx":
        if docx is None:
            raise ImportError("python-docx is required to ingest .docx files. Install it with pip install python-docx")
        
        print(f"📄 Converting DOCX '{filename}' to TXT...")
        doc = docx.Document(source_filepath)
        text = "\n".join([p.text for p in doc.paragraphs])
        
        dest_filename = f"{doc_id}.txt"
        dest_path = os.path.join(RAW_DOCS_DIR, dest_filename)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        file_size = os.path.getsize(dest_path) 
    else:
        dest_filename = f"{doc_id}{ext}"
        dest_path = os.path.join(RAW_DOCS_DIR, dest_filename)
        shutil.copy2(source_filepath, dest_path)

    doc_metadata = {
        "doc_id": doc_id,
        "name": name,
        "original_filename": filename,
        "internal_path": f"raw_docs/{dest_filename}",
        "size_bytes": file_size,
        "hash": file_hash,
        "ingested_at": datetime.now().isoformat()
    }

    manifest.append(doc_metadata)
    save_manifest(manifest)

    print(f"✅ Successfully ingested '{name}' -> {doc_id}")
    return doc_metadata


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest files for Persona Distiller")
    parser.add_argument("filepath", help="Path to the file to ingest")
    parser.add_argument("--name", help="Optional internal name for the document")
    
    args = parser.parse_args()
    try:
        ingest_document(args.filepath, args.name)
    except Exception as e:
        print(f"❌ Error: {e}")
