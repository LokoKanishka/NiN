# BitNin Dataset Builder

Servicio local para construir el primer dataset versionado de mercado de BitNin.

## Esta fase usa

- `Blockchain.com Charts API` para una serie diaria canonica inicial de BTC.
- `Binance klines` via `https://data-api.binance.vision` para barras OHLCV de detalle.

## Produce

- artefacto crudo por corrida en `verticals/bitnin/runtime/datasets/market/raw/`
- dataset normalizado en `verticals/bitnin/runtime/datasets/market/normalized/`
- snapshot reproducible en `verticals/bitnin/runtime/datasets/market/snapshots/`
- log estructurado de corrida en `verticals/bitnin/runtime/logs/`

## No produce

- narrativa
- episodios
- embeddings
- indexado en Qdrant
- analisis
- shadow
- ejecucion financiera

## Contrato

La salida normalizada respeta `verticals/bitnin/SCHEMAS/market_bar.schema.json`.

Para esta fase se habilitaron solo cuatro opcionales justificados:

- `ingested_at`
- `quote_volume`
- `trade_count`
- `checksum`

## Modos

- `full`: bootstrap o rebuild completo
- `incremental`: carga existente + fetch desde el siguiente `open_time`

## Ejemplos

```bash
python -m verticals.bitnin.services.bitnin_dataset_builder.builder blockchain \
  --dataset-version market-v0-blockchain \
  --mode full \
  --symbol BTCUSD \
  --timespan all
```

```bash
python -m verticals.bitnin.services.bitnin_dataset_builder.builder binance \
  --dataset-version market-v0-binance-4h \
  --mode full \
  --symbol BTCUSDT \
  --interval 4h \
  --start 2025-01-01T00:00:00Z
```

## Salida esperada

El CLI imprime un resumen JSON con:

- cantidad de registros
- paths de `raw`, `normalized`, `snapshot`
- path del log
- resumen de validacion

## Pendiente para fases siguientes

- fuentes narrativas
- fusion mercado + narrativa
- episodios
- retrieval / Qdrant
- analista
- shadow / HITL
