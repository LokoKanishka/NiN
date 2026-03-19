# BitNin Data Flow Map

Mapa técnico del ciclo de vida del dato (Data Flow) en la Fase 29R. Ilustra cómo viaja el dato desde las fuentes externas crudas hasta su conversión en evidencia gobernable.

## 1. Fase de Ingestión y Construcción de Contexto

El `BitNinAnalyst` (orquestado por el `BitNinRuntimeRunner`) no busca en internet en tiempo real. Depende de datasets materializados.

* **Dataset de Mercado**: Barras Klines Binance (Local en `runtime/datasets/market/normalized/`). Aportan `close`, `returns`, `volume_anomaly`, calculando volatilidad histórica en `context.py`.
* **Dataset Narrativo (`v1-robust`)**: Heurística de GDELT normalizada (Local en `runtime/datasets/narrative/normalized/`). Aporta menciones de tópicos, entidades y una puntuación de `relevance_btc`.
* **Actividad de Indexado y Memoria Activa**: El motor recurre a Qdrant (vía `ActiveMemoryRetriever`) consumiendo la colección `bitnin_episodes` para inyectar recuerdos análogos al contexto del LLM.

## 2. Fase de Análisis e Inferencia

1. **Context Builder**: Mezcla el dataset de mercado as-of-date y la heurística narrativa de los últimos 7 días. Calcula `market_state` y extrae el `narrative_coverage_score` crudo.
2. **Retrieve**: Carga del RAG (Ollama embedding -> Qdrant) los top episodios.
3. **Composite Signal**: `builder.py` evalúa matemáticamente el soporte del mercado, la narrativa y la similitud del episodio para emitir una métrica convergente.
4. **Pre-LLM Guardrail**: Si el contexto es pobre (ej. `data_coverage_score < 0.75` o `narrative_coverage_score < 0.15`), ataja la ejecución y devuelve directo `insufficient_evidence` sin tocar Ollama.
5. **LLM Eval (Ollama)**: Si pasa el guardrail, se invocan los prompts versionados (`PROMPT_VERSION`) contra el host `localhost:11434`. Devuelve la hipótesis dominante, confidence y un _recommended_action_ (`long`, `short`, `no_trade`).
6. **Post-LLM Guardrail**: (`validate.py`) Castiga y rebaja salidas alcistas o bajistas a `no_trade` si la confianza direccional es `< 0.55` o faltan análogos fuertes. 
7. **Salida**: Se persiste `analysis_raw__...` (prompt + salida cruda), `analysis__...` (JSON normalizado y validado por esquema) y el `snapshot` local.

## 3. Fase Shadow y Ejecución en Seco

El pipeline pasa el output del analista al **Shadow Runner** (`bitnin-shadow`):
- Evalúa si el `recommended_action` es transaccional. En modo Shadow, crea un `trade_intent` figurativo almacenado en `runtime/shadow/intents/` (y snapshots correspondientes). 

Luego entra el **Exec Guard** (`bitnin-exec-guard`):
- Identifica la intención. Valida restricciones (que estemos en dry_run). Alimenta al manager e inscribe el `execution_record` (simulado) en `runtime/execution/results/`.

## 4. Fase de HITL (Validación Humana)

Si la intención (incluso en dry run) supera ciertos umbrales de materialidad, se inserta en el buzón humano:
- Pasa al **HITL Manager**.
- Se graba un `case` en `runtime/observability/history/hitl_state.json` (State Machine vivo).
- El sistema inyecta visibilidad pasiva recreando en el acto `hitl_inbox.md`.

## 5. Fase de Observabilidad Longitudinal y Trazabilidad

A medida que cientos de ciclos se acumulan:
1. El **Runner** recolecta todos los resultados de una ventana (`start_date` a `end_date`) y empuja el consolidado al componente de observabilidad, emitiendo un `batch_report__batch_*.json`.
2. El validador lee el batch, calcula medias vectoriales de convergencia y drift, y genera el `scorecard__batch_*.md`.
3. El supervisor compila un _health status_ en base a si los servicios (Ollama, n8n, Qdrant) respondieron correctamente y refresca continuamente `health_snapshot.json` y `.md`.

## 6. Integración Histórica y Cierres (Humanos Gobernantes)

- Al finalizar la jornada, `day-close` toma los inbox, states y briefings y empaqueta la jornada en `runtime/observability/history/daily_bundles/YYYY-MM-DD/`.
- Al finalizar la semana, `week-review` colecta todo lo compilado y lo junta en `weekly_reviews/YYYY-WW/` donde el veredicto final humano queda blindado en el Ledger, habilitando o rechazando la futura promoción de fase.
