"""
NIN Bibliotecario — Catalog Schema
Esquema y utilidades para el catálogo bibliográfico de humanidades.
"""

import unicodedata
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_TYPES = ["primary", "secondary"]
VALID_SUBTYPES = [
    "obra_original", "traduccion", "edicion_critica", "comentario",
    "monografia", "articulo", "capitulo", "tesis", "compilacion", "otro"
]


@dataclass
class BibEntry:
    """A single bibliographic entry."""
    id: str = ""
    author: str = ""
    title: str = ""
    year: str = ""
    type: str = "secondary"  # primary | secondary
    subtype: str = "otro"
    language: str = ""
    source_url: str = ""
    identifier: str = ""       # DOI, ISBN, etc.
    identifier_type: str = ""  # "doi", "isbn", etc.
    edition: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BibEntry":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)


def normalize_text(text: str) -> str:
    """Normalizes text for deduplication: lowercase, strip accents, collapse whitespace."""
    if not text:
        return ""
    s = text.lower().strip()
    # Remove accents
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def dedup_key(entry: BibEntry) -> str:
    """
    Generates a deterministic deduplication key.
    Priority: DOI/ISBN > normalized(title + author + year)
    """
    if entry.identifier and entry.identifier_type in ("doi", "isbn"):
        return f"{entry.identifier_type}:{normalize_text(entry.identifier)}"
    return f"title:{normalize_text(entry.title)}|author:{normalize_text(entry.author)}|year:{entry.year.strip()}"


def deduplicate(entries: list[BibEntry]) -> list[BibEntry]:
    """
    Deduplicates bibliography entries deterministically.
    Returns a list with duplicates removed.
    """
    seen = {}
    result = []
    for entry in entries:
        key = dedup_key(entry)
        if key not in seen:
            seen[key] = True
            result.append(entry)
    return result


def classify_type(title: str, author: str, subject_author: str) -> str:
    """
    Simple heuristic to classify as primary or secondary.
    If the entry's author matches the subject author, it's primary.
    """
    if normalize_text(author) == normalize_text(subject_author):
        return "primary"
    return "secondary"


def catalog_to_json(entries: list[BibEntry]) -> list[dict]:
    """Converts a catalog list to JSON-serializable dicts."""
    return [e.to_dict() for e in entries]


def catalog_from_json(data: list[dict]) -> list[BibEntry]:
    """Restores catalog from JSON dicts."""
    return [BibEntry.from_dict(d) for d in data]
