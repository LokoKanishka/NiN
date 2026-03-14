# BitNin Memory Indexer

Servicio local para indexar eventos y episodios de BitNin en Qdrant con embeddings reales.

## Principios

- embeddings reales, nunca vectores dummy
- dimension medida en tiempo de ejecucion
- upsert idempotente por id estable
- payloads filtrables
- retrieval semantico con filtros

## Collections

- `bitnin_episodes`
- `bitnin_events`

## Embedding medido

- modelo verificado: `nomic-embed-text:latest`
- dimension real medida en esta fase: `768`
- medicion hecha por llamada real a Ollama antes de crear collections

## Que se embebe

### Episodios

- `summary_local`
- firma textual derivada de mercado y narrativa

### Eventos

- `title`
- `summary_local`

No se embebe JSON completo ni artefacto crudo.

## Que se guarda localmente

- export tecnico de embedding probe y collections
- logs de indexacion
- queries de verificacion/retrieval

## Entorno observado

- Ollama vivo en `http://127.0.0.1:11434`
- Qdrant accesible en `http://127.0.0.1:6333`

El SSOT de NiN menciona `6335`, pero en esta fase la verificacion real se hizo contra `6333` porque es el endpoint vivo accesible.

## Ejemplo

```bash
python -m verticals.bitnin.services.bitnin_memory_indexer.indexer \
  --episodes-path verticals/bitnin/runtime/datasets/episodes/normalized/episodes__BTCUSDT__1d__episodes-v0-real.jsonl \
  --events-path verticals/bitnin/runtime/datasets/narrative/normalized/gdelt_doc_artlist__bitcoin__narrative-v0-gdelt.jsonl \
  --dataset-version memory-v0
```

```bash
python -m verticals.bitnin.services.bitnin_memory_indexer.retrieve \
  --collection bitnin_episodes \
  --query "high volatility bitcoin selloff with geopolitics"
```
