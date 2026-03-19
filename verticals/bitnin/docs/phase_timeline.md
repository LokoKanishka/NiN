# BitNin Phase Timeline

Cronología consolidada de maduración del sistema BitNin.

## Fases Conceptuales
- **Fase 0-1**: Declaración de BitNin como Vertical oficial gobernable. Límite: Sin simuladores arbitrarios, solo _shadow-first_. Definición UTC y SSOT.
- **Fase 2**: Dataset de mercado base. Histórico reproducible y normalización.
- **Fase 3**: Baseline Narrativo (v1-robust). GDELT para candidatos narrativos, reconociendo que la narrativa da hipótesis, no verdad causal absoluta.
- **Fase 4**: Episodios (`bitnin_episode_builder`). Combinación de narrativa y mercado bajo la tesis _market-first_.
- **Fase 5**: RAG Memoria. Índices Qdrant estrictos sin vectores dummy, basados en Ollama/nomic-embed.
- **Fase 6**: Analista (`bitnin_analyst`). Operador no-ejecutor que describe y valida, emitiendo fallos explícitos (ej. `insufficient_evidence`).
- **Fase 7**: Backtester. Replay simulado tipo point-in-time que bloquea visibilidad futura (`as_of`).
- **Fase 8**: Shadow Mode. Operación local que graba intenciones futuras, bloquea por `exec-guard` y reporta trazabilidad en seco.
- **Fase 9**: HITL Base. Ingesta de revisiones humanas auditadas, expuestas como flujo de estados y controladas mediante timeline inmutable.

## Maduración Operativa y Resiliencia
- **Fase 10**: Observabilidad y Pipeline. Identificación estricta de _drift_ y degradaciones silenciosas a través de reportes y batches longitudinales.
- **Fase 12**: Monitoreo de desvíos, Scorecards estructurales, y _appending_ de historias de comportamiento para evidenciar calidad.
- **Fase 22**: CLI HITL (`bitnin_ctl hitl`). Eliminación de fragilidad Markdown al mutar decisiones. El estado se migra puramente a un State JSON y las vistas de Markdown pasan a ser dinámicas de _Solo Lectura_.
- **Fase 24**: Bitácora Ejecutiva (`day-close`). Adición del Ritual Diario, paquetización de decisiones y consolidación de bundles diarios.
- **Fase 25**: Entrypoints, Bootstrap y Respaldo. Normalización absoluta con `bootstrap.sh`, `scheduler_ctl.sh`, wrappers robustos y scripts de _Backup / Restore_ del plano humano.
- **Fase 26**: RC Shadow. _Disaster Recovery Drill_. Destrucción controlada y restauración verificada de todo el runtime de la máquina.
- **Fase 27**: GA Shadow. _Clean-room Deployment_. Certificación de independencia del host o _portabilidad absoluta_.
- **Fase 28**: Gobernanza, Gate a Pilot, y KPIs. Definición de métricas, incidencias tipificadas, _weekly-review_ y ledger cerrado dictando dictámenes periódicos.

## Fase Actual (En Curso)
- **Fase 29R**: _Ventana Real de Gobernanza_. Congelamiento de desarrollo arbitrario para acumular 4 semanas cronológicas reales (Sin simulaciones) que formen evidencia probatoria para promoción futura al estrato _Pilot_ y certifiquen desempeño auténtico sobre la métrica de éxito evaluada.
