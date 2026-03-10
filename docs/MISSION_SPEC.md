# NIN | Especificación de Misión (MISSION_SPEC)

**Estado:** VIGENTE
**Fecha:** 2026-03-10

---

## 1. Contrato JSON de Misión

Cada misión se persiste como `runtime/missions/<mission_id>/mission.json` con este esquema:

```json
{
  "mission_id": "bib_20260310_171500",
  "source": "telegram",
  "type": "investigacion_doctoral",
  "topic": "Aristóteles y el motor inmóvil",
  "scope": {
    "primary_corpus": ["Metafísica", "Física"],
    "secondary_corpus": ["comentarios", "monografías"],
    "focus": ["metafísico", "recepción"],
    "language_priority": ["es", "en", "el"],
    "max_sources": 30
  },
  "deliverables": ["catalog", "curation", "dossier"],
  "status": "QUEUED",
  "created_at": "2026-03-10T17:15:00-03:00",
  "updated_at": "2026-03-10T17:15:00-03:00",
  "artifacts": {
    "catalog": "catalog.json",
    "curation": "curation.json",
    "research_map": "research_map.md",
    "dossier": "dossier.md"
  }
}
```

## 2. Máquina de Estados

```
QUEUED → SCOPING → SOURCING → CORPUS_REVIEW → CURATING → DOSSIER → DONE
                                                                  ↘ FAILED
                                        (cualquier estado) → HIBERNATED
```

### Transiciones Válidas

| Desde | Hacia | Condición |
|:---|:---|:---|
| `QUEUED` | `SCOPING` | Misión aceptada, comienza delimitación |
| `SCOPING` | `SOURCING` | Scope aprobado por humano |
| `SCOPING` | `HIBERNATED` | Sin respuesta del humano (timeout) |
| `SOURCING` | `CORPUS_REVIEW` | Catálogo construido |
| `CORPUS_REVIEW` | `CURATING` | Corpus aprobado por humano |
| `CORPUS_REVIEW` | `SOURCING` | Humano pide ajustes |
| `CORPUS_REVIEW` | `HIBERNATED` | Sin respuesta (timeout) |
| `CURATING` | `DOSSIER` | Curación completada |
| `DOSSIER` | `DONE` | Dossier generado y entregado |
| *cualquiera* | `FAILED` | Error irrecuperable |
| *cualquiera* | `HIBERNATED` | Timeout o pausa voluntaria |
| `HIBERNATED` | *estado anterior* | Reanudación manual |

## 3. Estructura de Archivos por Misión

```
runtime/missions/<mission_id>/
├── mission.json          # Estado y metadata
├── catalog.json          # Catálogo bibliográfico
├── curation.json         # Resultado de curación LLM
├── research_map.md       # Mapa de investigación legible
├── dossier.md            # Dossier final
├── mission_log.jsonl     # Log de eventos
└── notes/                # Notas intermedias
```

## 4. Campos del Catálogo Bibliográfico

Cada entrada en `catalog.json` sigue este esquema:

```json
{
  "id": "cat_001",
  "author": "Aristóteles",
  "title": "Metafísica",
  "year": "-350",
  "type": "primary",
  "subtype": "obra_original",
  "language": "el",
  "source_url": "",
  "identifier": "",
  "identifier_type": "",
  "edition": "Edición Gredos (trad. T. Calvo Martínez)",
  "notes": ""
}
```

### Tipos válidos
- `primary`: obras del autor principal
- `secondary`: comentarios, monografías, artículos sobre el tema

### Subtipos válidos
- `obra_original`, `traduccion`, `edicion_critica`, `comentario`, `monografia`, `articulo`, `capitulo`, `tesis`, `compilacion`

---
**Certificado por:** Antigravity AI (Marzo 2026)
