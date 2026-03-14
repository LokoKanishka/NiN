# BitNin Narrative Builder

Servicio local para discovery narrativo estructurado de BitNin.

## Esta fase usa

- `GDELT DOC 2.0 API` como fuente base de discovery de candidatos narrativos.

## Produce

- raw de discovery en `verticals/bitnin/runtime/datasets/narrative/raw/`
- eventos normalizados en `verticals/bitnin/runtime/datasets/narrative/normalized/`
- snapshots reproducibles en `verticals/bitnin/runtime/datasets/narrative/snapshots/`
- logs de corrida en `verticals/bitnin/runtime/logs/`

## Esta capa no hace

- inferencia causal fuerte
- episodios
- embeddings
- indexado en Qdrant
- analista
- shadow
- HITL

## Regla de retencion

Se guarda:

- metadata de GDELT
- URL
- titulo
- resumen local propio
- tags, entidades y scores internos

No se guarda:

- HTML completo
- cuerpo completo del medio externo
- scraping masivo de texto restricto

## Contrato

La salida normalizada respeta `verticals/bitnin/SCHEMAS/narrative_event.schema.json`.

Campos opcionales usados en esta fase:

- `source_type`
- `region`
- `confidence_source`
- `relevance_btc`
- `retention_mode`
- `ingested_at`

## Ejemplo

```bash
python -m verticals.bitnin.services.bitnin_narrative_builder.builder gdelt \
  --dataset-version narrative-v0-gdelt \
  --mode full \
  --query bitcoin \
  --timespan 1d \
  --maxrecords 20
```

## Principio de salida

Los eventos normalizados son candidatos narrativos estructurados con confianza y tags iniciales. No representan verdad causal absoluta.
