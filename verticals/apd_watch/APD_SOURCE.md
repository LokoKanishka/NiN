# APD Source Design (Fundacional)

Fecha: 2026-04-06
Estado: diseño operativo mínimo read-only (fixture-first)

## Objetivo

Definir el contrato de lectura de la fuente APD de forma estable, trazable y read-only.

## Reglas iniciales

- Captura exclusivamente observacional (sin login automatizado de acciones, sin escritura).
- Snapshot diario como unidad mínima auditable.
- Identificador estable derivado de campos visibles canónicos + fingerprint.
- Deduplicación por `stable_id` + `source_snapshot_date`.

## Contrato de datos (Tramo 2)

### `offer_raw`

- Schema: `verticals/apd_watch/schemas/offer_raw.schema.json`
- Campos mínimos requeridos:
  - `source`
  - `source_snapshot_date`
  - `captured_at_utc`
  - `source_url` (o `null` si no existe)
  - `raw_payload`

### `offer_normalized`

- Schema: `verticals/apd_watch/schemas/offer_normalized.schema.json`
- Campos mínimos requeridos:
  - `stable_id`
  - `source`
  - `source_snapshot_date`
  - `captured_at_utc`
  - `code`
  - `cargo_materia`
  - `district`
  - `level_modality`
  - `school`
  - `status`
  - `closing_at`
  - `fingerprint`
  - `source_url`
  - `normalized_at_utc`

## Campos esperados de observación (sujeto a validación posterior)

- código de oferta (si existe)
- cargo/materia
- distrito
- nivel/modalidad
- establecimiento/escuela
- estado de oferta
- fecha/hora de cierre
- URL de detalle o referencia de origen

## Eventos de ciclo de vida a contemplar

- oferta nueva,
- oferta repetida,
- oferta anulada,
- oferta vencida,
- cambio de estado,
- cambio de cierre.

## Contrato de snapshot y manifests

Rutas read-only de esta vertical:

- Raw diario: `verticals/apd_watch/runtime/snapshots/apd_raw_YYYYMMDD.json`
- Manifest raw: `verticals/apd_watch/runtime/snapshots/apd_raw_manifest_YYYYMMDD.json`
- Normalized diario: `verticals/apd_watch/runtime/normalized/apd_normalized_YYYYMMDD.json`
- Manifest normalized: `verticals/apd_watch/runtime/normalized/apd_normalized_manifest_YYYYMMDD.json`

Campos mínimos del manifest:

- `source`
- `source_snapshot_date`
- `created_at_utc`
- `offers_count`
- `aggregate_hash`

## Implementación local mínima (sin scraping productivo)

Script operativo de esta fase:

- `verticals/apd_watch/tools/snapshot_pipeline.py`

Entrada inicial:

- Fixture JSON (`verticals/apd_watch/tests/fixtures/apd_offers_sample.json`) o input manual compatible.

Salida:

- `offer_raw[]`
- `offer_normalized[]`
- manifests raw/normalized

## Cómo se generan `stable_id` y `fingerprint`

- `stable_id`: hash SHA-256 truncado (24 hex) sobre combinación canónica de:
  - `source`, `code`, `cargo_materia`, `district`, `level_modality`, `school`
  - normalizados en minúscula, sin tildes y con espacios colapsados.
- `fingerprint`: hash SHA-256 completo sobre:
  - `stable_id`, `status`, `closing_at`
  - también normalizados canónicamente.

## Decisiones de fase

- Esta fase implementa un pipeline mínimo reproducible con fixture para cerrar contrato de captura.
- Sigue fuera de alcance la cobertura completa del portal APD y cualquier automatización de login/escritura.
