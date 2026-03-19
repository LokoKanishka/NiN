# BitNin Artifact Provenance Index

Índice central de Trazabilidad. Responde exhaustivamente a: _"¿Quién crea esto? ¿Dónde vive? ¿Qué pasa si lo borro? ¿Se mete en el backup?"_

## 1. Archivos Operativos (Runtime Vivo - Críticos)

| Artefacto / Archivo | Carpeta (`runtime/`) | Creador | Destructibilidad | Rol en Restore / Backup |
|-------------------|---|---|---|---|
| `hitl_state.json` | `observability/history/` | HITL Manager | **CRÍTICO** | Pieza fundamental del `.tar.gz`. Si se pierde, desaparece el 100% de la historia de los _case_ids_ y sus veredictos formales. |
| `operational_state.json` | `observability/history/` | Supervisor | Volátil, Borrable | Se regenera automáticamente tras unos sucesivos _ticks_. Controla latencia STALE pero no guarda Ledger. |
| `health_snapshot.json` | `observability/history/` | Observability / Health | Volátil, Borrable | Información de dashboards y consumos rápidos. Se sobrescribe en cada pulso de salud. No se backupea. |
| `longitudinal_history.json` | `observability/history/` | Observability / Reports | **CRÍTICO** | Compila la data macro-tendencial de las corridas. Guardado en backup. Evidencia longitudinal. |
| `weekly_review_state.json` | `observability/history/` | Operator CLI (`week-close`) | **CRÍTICO** | El Ledger inmutable de promoción de fase institucional. Salvado en backup prioritario. |

## 2. Archivos de Proyección de Secuencias (MD Dinámicos)

Markdown pensados exclusivamente para lectura por el humano a través del `cat`, consola o IDE. No poseen valor canónico de persistencia transaccional.

| Artefacto / Archivo | Carpeta | Origen de los Datos | Regla General |
|---|---|---|---|
| `hitl_inbox.md`, `hitl_archive.md` | `observability/history/` | `hitl_state.json` | Totalmente borrables. CLI los recrea si se dañan. |
| `hitl_briefing.md` | `observability/history/` | `hitl_state.json` | Totalmente borrable. |
| `health_snapshot.md` | `observability/history/` | `health_snapshot.json` | Totalmente borrable. |

## 3. Artefactos de Análisis / Shadow

Se generan como "Evidencia en Seco". Acumulativos, pesados.

| Artefacto / Archivo | Carpeta | Creador | Destructibilidad y Manejo |
|---|---|---|---|
| `analysis_raw_*.json` | `analyses/raw/` | BitNinAnalyst | Trazabilidad del prompt del LLM. Se purgan masivamente si no son incidentes. |
| `analysis_*.json` | `analyses/normalized/` | BitNinAnalyst | JSON validado por esquema. Es la salida que lee HITL. Se retiene en batch diarios. |
| `batch_report_*.json` | `observability/batches/` | BitNinRuntimeRunner | Consolidación diaria de salud, promedios y logs. Usado para el Week Review. Si se borra *después* del week loop, no se pierde historia importante. |
| `trade_intent_*.json` | `shadow/intents/` | ShadowRunner | Evidencia generada para simulación. Excluida forzosamente de GIT y Backups. |

## 4. Agrupadores de Evidencia (Daily Bundles / Week-Reviews)

Aglomera directorios enteros creados por el operador durante rutinas formales del cierre de ciclo.

| Subdirectorio | Carpeta Padre (`history/`) | Generador | Destino y Criticidad |
|---|---|---|---|
| `daily_bundles/YYYY-MM-DD/` | `observability/history/` | `day-close` (Operador) | Contiene la bitácora comprimida (`operator_journal.md`), los snapshots MD congelados. Es el empaquetado auditable humano. Enorme valor empírico `GA Shadow`. Está dentro del Backup Script. |
| `weekly_reviews/YYYY-WW/` | `observability/history/` | `week-review` (Operador) | Contiene los `weekly_scorecard.md` consolidados. Demuestra con firmas los KPIs. Extremo blindaje en backups. |

## Mapeo Estructural contra GIT

Ningún archivo del `/history/` está commiteado o trackeado nativamente al repositorio original; el control de fuentes estricto ignora los datasets simulados y el entorno JSON operativo (`.gitignore`), con la evidente prebenda de garantizar portabilidad Limpia de Código. Las migraciones se hacen combinando el `git clone` del Branch y la importación de un Recovery `.tar.gz` montado _encima_ del directorio restaurado.
