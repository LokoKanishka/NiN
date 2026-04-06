# APD Source Design (Fundacional)

Fecha: 2026-04-06
Estado: diseño inicial (sin scraping operativo aún)

## Objetivo

Definir el contrato de lectura de la fuente APD de forma estable, trazable y read-only.

## Reglas iniciales

- Captura exclusivamente observacional (sin login automatizado de acciones, sin escritura).
- Snapshot diario como unidad mínima auditable.
- Identificador estable derivado de campos visibles canónicos + fingerprint.
- Deduplicación por `stable_id` + `source_snapshot_date`.

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

## Decisiones de fase

- Esta fase no implementa extracción final; solo deja contrato y límites.
- La validación de estructura observable del portal APD se ejecuta en el siguiente tramo.
