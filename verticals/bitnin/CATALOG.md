# BitNin Catalog

Estado general: `planned`
Fecha: 2026-03-13

Este catalogo define workflows esperados de la vertical BitNin. Ninguno existe todavia como workflow oficial en runtime.

| Slug | Proposito | Inputs | Outputs | Estado inicial | Autoridad esperada |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `bitnin_ingest_market` | Ingestar barras y series de mercado versionadas. | fuentes de mercado, rango temporal, intervalo, dataset_version | `market_bar` normalizado, manifest de lote, logs | `planned` | workflow autoritativo de ingest de mercado en `bitnin-control` |
| `bitnin_ingest_narrative` | Ingestar eventos narrativos y metadata de fuentes abiertas. | fuentes narrativas, ventanas temporales, filtros tematicos, dataset_version | `narrative_event` normalizado, manifest de lote, logs | `planned` | workflow autoritativo de ingest narrativo en `bitnin-control` |
| `bitnin_build_episodes` | Construir episodios historicos combinando mercado y narrativa. | market bars, narrative events, reglas de ventana | `episode`, indices intermedios, logs | `planned` | workflow autoritativo de episodios en `bitnin-control` |
| `bitnin_embed_index` | Generar embeddings e indexar episodios/eventos en Qdrant. | episodios, eventos, metadata de embedding, dataset_version | puntos indexados, manifest de indexado, logs | `planned` | workflow autoritativo de RAG/indexado en `bitnin-control` |
| `bitnin_active_memory` | Extraer e indexar recuerdos operativos en Qdrant. | artefactos de runtime, collection qdrant | memoria operativa indexada | `active` | service de memoria activa |
| `bitnin_analyst_tick` | Ejecutar el analista estructurado con memoria activa y Señal Compuesta. | episodios, narrativa, memoria activa | `analysis_output` enriquecido con `composite_signal` | `active` | analyst `v3-compuesta` |
| `bitnin_shadow_tick` | Convertir analisis en intencion no ejecutable y registrar shadow outcome. | `analysis_output`, parametros de shadow, reloj UTC | `trade_intent`, `execution_record` en modo shadow, logs | `planned` | workflow autoritativo de shadow en `bitnin-exec-guard` |
| `bitnin_hitl_approval` | Solicitar y registrar aprobaciones humanas para intenciones futuras. | `trade_intent`, canal de aprobacion, actor | `approval`, estado de intencion, logs | `planned` | workflow autoritativo de HITL en `bitnin-exec-guard` |
| `bitnin_exec_bridge` | Encapsular cualquier puente de ejecucion futura detras de guardrails. | `trade_intent` aprobado, contexto de riesgo, modo de ejecucion | `execution_record`, resultado referenciado, logs | `planned` | unico workflow posible de paso hacia ejecucion, bloqueado en v1 |
| `bitnin_daily_report` | Emitir resumen diario auditable de datasets, episodios y decisiones. | artefactos del dia, metricas de cobertura, logs | reporte Markdown/JSON, referencias de replay | `planned` | workflow autoritativo de auditoria y replay |
| `bitnin_observability` | Salud, Auditoría y Replay de misiones | logs de workflows, estado de servicios | reportes de salud, métricas, logs de auditoría | `planned` | workflow autoritativo de observabilidad en `bitnin-control` |
| `bitnin_batch_runner` | Ejecutar múltiples ciclos secuenciales con trazabilidad. | `batch_size`, `interval_seconds`, `symbol` | Reporte de lote, artefactos versionados por `run_id`, logs | `active` | runner oficial de estabilidad en `bitnin-runtime-runner` |
| `bitnin_observability_scorecard` | Generar alertas y scorecard longitudinal de métricas de calidad y degradación. | `batch_report` JSON | `scorecard` Markdown y Alertas de stdout | `active` | validador en `bitnin-observability` |
| `bitnin_run_shadow_pipeline` | Orquestar barrido histórico continuo y evaluar scorecards de estabilidad. | `start_date`, `end_date`, `symbol` | Batch report, Scorecard y Múltiples ejecuciones puras shadow | `active` | script `run_shadow_pipeline.py` |
| `bitnin_supervisor` | Orquestador resiliente con persistencia host-level (linger) y chequeo de freshness. | `operational_state`, `health_snapshot` | Snapshot humano, alertas de staleness, logs unificados | `active` | supervisor en `bitnin-control` (Phase 16 verified) |
| `bitnin_hitl_manager` | Analizador de scorecards para priorización humana y bandeja de entrada. | `batch_report` JSON | `hitl_inbox` Markdown, `hitl_digest` Markdown, alertas de prioridad | `active` | componente de revisión en `bitnin-hitl` |
| `hitl_state.json` | Persistencia de decisiones humanas y trazabilidad de estados. | JSON de estados | N/A | `active` | runtime/observability/history |
| `RUNBOOK.md` | Guía operacional para humanos. | N/A | N/A | `active` | Documento de referencia |
## Notas de gobierno

- `bitnin_exec_bridge` no habilita trading real en v1. Su existencia en este catalogo solo reserva el nombre y el limite de autoridad.
- Cualquier workflow real de esta tabla debera registrarse luego en `library/catalog.db`.
- Solo puede existir una autoridad activa por slug funcional dentro de la vertical.
- En Fase 9 existen artefactos locales no activos en `verticals/bitnin/workflows/bitnin_hitl_request.json` y `verticals/bitnin/workflows/bitnin_hitl_decision.json`. Siguen fuera de `library/catalog.db` hasta revision explicita.
