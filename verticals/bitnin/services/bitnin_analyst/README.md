# BitNin Analyst

Servicio local para construir analisis estructurados sobre estado actual + memoria RAG de BitNin.

## Principios

- no ejecuta nada
- produce JSON estricto y validado
- usa memoria RAG real, no "memoria interna"
- puede concluir `no_trade` o `insufficient_evidence`
- persiste raw, normalized y snapshot reproducible

## Flujo

1. arma contexto actual desde mercado, narrativa y policy vigente
2. consulta Qdrant para recuperar episodios y eventos analogos
3. construye prompt versionado
4. llama a Ollama con modelo explicito
5. valida la salida contra `analysis_output.schema.json`
6. aplica guardrails cognitivos y persiste artefactos

## Modelo y prompt

- modelo por defecto: `qwen2.5:14b`
- prompt version: `bitnin-analyst-v0`

## Guardrails

El analista baja a `recommended_action = no_trade` o `final_status = insufficient_evidence` si ocurre alguna de estas condiciones:

- `data_coverage_score < 0.75`
- menos de 2 episodios analogos utiles
- score del mejor analogo por debajo de `0.5`
- `narrative_coverage_score < 0.2`
- salida del modelo mal parseada o inconsistente

## Ejemplo

```bash
python -m verticals.bitnin.services.bitnin_analyst.builder \
  --symbol BTCUSDT \
  --interval 1d
```
