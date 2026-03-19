# BitNin Runtime Map

La estructura de `runtime/` separa drásticamente lo persistente de lo volátil y de lo auditable (Evidencia).

## 🗂️ Niveles de Runtime

### `runtime/datasets/`
- **Qué vive aquí**: Series de Klines binance, extractos GDELT y metadatos base. 
- **Rol**: Fuente empírica para el Backtester y Episodes. 
- **Estabilidad**: Fija. Solo crece lateralmente bajo nuevos versionados de dataset (ej. `v1-robust`).

### `runtime/shadow/`
- **Qué vive aquí**: Simulaciones de `exec-guard` y validaciones previas de portafolio inofensivo.
- **Riesgo**: Ninguno. Borrable.

### `runtime/observability/scorecards/` & `batches/`
- **Qué vive aquí**: La memoria de degradación y score continuo. Registros crudos `.json` de pipeline y MDs consolidados que reflejan el *State of Accuracy* (cobertura, composite signals, penalizaciones por _drift_). 
- **Rol**: Archivo de comportamiento.
- **Regla**: Conservar para trazabilidad prolongada, aunque purgar _batches_ antiguos asumiendo que el scorecard retuvo la síntesis, es admisible.

---

## 🔎 El Corazón Operativo (`runtime/observability/history/`)

Es el directorio con mayor movimiento de I/O en todo el vertical. Contiene las banderas y proyecciones dinámicas de salud.

### Estado Vivo (Aislado de Git)
- `operational_state.json`: Memoria del Supervisor para resumes limpios (`STALE`, etc).
- `hitl_state.json`: El _State Machine_ real conteniendo todos los historiales, notas operativas y resoluciones de casos HITL. Es la **fuente de verdad canónica**.
- `health_snapshot.json` / `.md`: Semáforo para consumo de dashboards y humanos. Recalcado dinámicamente.
- `bitnin_supervisor.lock`: Prevención de colisiones concurrentes.  

### Evidencia Histórica (Consolidada)
- `daily_bundles/YYYY-MM-DD/`: Directorio donde el _Ritual de Cierre Diario_ vuelca los briefing cerrados del día y `operator_journal.md`. Queda intocable.
- `weekly_reviews/YYYY-WW/` y `weekly_review_state.json`: Ledger auditable de promociones de fase con scorecards congelados.
- `longitudinal_history.json`: Aglutina datos de tendencia que alimentan detecciones de pérdida de certeza o degradación a semanas vista.

### Proyecciones (Solo Lectura, recreables)
- `hitl_inbox.md`, `hitl_archive.md`, `hitl_briefing.md`, `hitl_digest.md`: Archivos en markdown que el sistema recrea fielmente tras cada iteración. No interactuar directamente con ellos para intentar forzar estados manuales; usar la Consola `bitnin-ctl`.

## 🧹 Qué se puede borrar / Qué Backup proteger
1. **Borrables ("Clean-slate")**: `*.lock`, `health_snapshot.*`, `hitl_inbox.md` (y derivados MD proyectados). 
2. **Protegido y Backup Necesario**: `hitl_state.json`, `weekly_review_state.json`, `longitudinal_history.json` y los subdirectorios `daily_bundles/` y `weekly_reviews/`. Esto conforma el 100% de la base sobre qué se restaura.
