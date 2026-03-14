# BitNin Episode Builder

Servicio local para construir episodios historicos reproducibles a partir de mercado + narrativa.

## Principio rector

Los episodios de BitNin son `market-first, narrative-augmented`.

- el mercado dispara o valida el episodio
- la narrativa lo enriquece
- no se crean episodios solo por ruido editorial

## Entradas

- dataset de mercado normalizado
- dataset narrativo normalizado

## Salidas

- candidatos/intermedios en `verticals/bitnin/runtime/datasets/episodes/raw/`
- episodios normalizados en `verticals/bitnin/runtime/datasets/episodes/normalized/`
- snapshots reproducibles en `verticals/bitnin/runtime/datasets/episodes/snapshots/`

## Triggers v0

- retorno absoluto en 1 barra sobre umbral
- volatilidad/regimen alto en rolling window
- volumen o quote volume anormal
- trigger narrativo reforzado, solo si hay evento relevante y señal de mercado compatible

## Esta fase no hace

- embeddings
- Qdrant
- analista
- shadow
- HITL
- ejecucion

## Ejemplo

```bash
python -m verticals.bitnin.services.bitnin_episode_builder.builder \
  --dataset-version episodes-v0 \
  --market-path verticals/bitnin/runtime/datasets/market/normalized/binance_klines__BTCUSDT__1d__market-v0-binance-1d.jsonl \
  --narrative-path verticals/bitnin/runtime/datasets/narrative/normalized/gdelt_doc_artlist__bitcoin__narrative-v0-gdelt.jsonl \
  --symbol BTCUSDT \
  --interval 1d
```
