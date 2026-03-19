# BitNin Failure Modes Catalog

Catálogo técnico de modos de falla reales y/o plausibles, organizados por capa de abstracción. Este documento evidencia vulnerabilidades empíricas de la plataforma y su tratamiento actual (o su condición de "riesgo abierto"). Las clasificaciones se condicen con la lógica de validación interna.

## 1. Capa de Análisis e Inferencia (Analyst / AI)

### `F-AN-01: llm_timeout_or_crash`
- **Síntoma Visible**: Ollama service is unreachable o LLM no responde a tiempo. Devuelve error estructural desde `builder.py`.
- **Impacto**: `analyst` aborta el llamado al LLM. El wrapper (si es el Supervisor) captura la excepción y emite forzosamente una salida nula (`llm_failure:OllamaUnreachable` o similar).
- **Detección actual**: Visibilidad inmediata en el `health_snapshot.json` (`Ollama: DOWN / UNREACHABLE`). Se captura en los _Batch Reports_ como fallos de ejecución.
- **Mitigación Módulo**: El analista no crashea sin retorno; asume una decisión simulada de `no_trade` forzada.
- **Riesgo**: El pipeline asimila el error _demasiado_ pacíficamente y puede generar Batch Reports vacíos.

### `F-AN-02: validation_schema_violation`
- **Síntoma Visible**: El LLM emite una salida con llaves malformadas o un `recommended_action` apócrifo (ej. `"action": "maybe"`).
- **Impacto**: `AnalysisOutputValidator` rechaza la salida.
- **Detección actual**: Falla la corrida y lanza un JSON Exception con errores de esquema. Visible en logs en vivo del runtime runner.
- **Mitigación**: `BasicValidatorFallback` previene la propagación de alucinación del dictamen. Se pierde el _run_.

## 2. Capa de Observabilidad y Recuperación (Memoria RAG)

### `F-OBS-01: qdrant_unreachable`
- **Síntoma Visible**: Active Memory Retrieval falla por desconexión de Qdrant.
- **Impacto**: `active_memory` devuelve lisa y llanamente `[]`. _El analista no crashea_, sino que infiere que no hay RAG disponible (esto está explícitamente contenido en `builder.py` mediante un `except Exception`).
- **Detección**: `qdrant_url` aparece `DOWN` en el snapshot.
- **Mitigación**: El analista opera con ceguera de memoria, asumiendo `mem_score = 0.0`. Por consiguiente, la Señal de Convergencia cae trágicamente, siendo imposible obtener un proxy `HIGH` o direccional alcista. Mitigación conservadora pero funcional.

### `F-OBS-02: narrative_coverage_collapse`
- **Síntoma Visible**: El pipeline GDELT normalizado en `datasets/narrative/` dejó de actualizarse o falló n8n silenciosamente.
- **Impacto**: `narrative_coverage_score < 0.15`.
- **Detección**: Pre-LLM Guardrail corta y bloquea operaciones de inmediato, arrojando `narrative_coverage_critically_low`.
- **Mitigación**: `builder.py` activa salvaguarda y lo transforma en `no_trade`.
- **Riesgo Abierto**: Si n8n (o el worker de pipeline externo) falla pero el _scheduler_ sigue vivo, se enmascara un error _upstream_ bajo un dictamen repetitivo del LLM de `insufficient_evidence`. Solo detectable si un humano inspecciona el drift de salud con `doctor`.

## 3. Capa de Operatividad y Concurrencia (Supervisor / Execution)

### `F-OPS-01: zombie_lock_file`
- **Síntoma Visible**: `bitnin_supervisor.lock` permanece en el directorio tras una muerte sucia del proceso.
- **Impacto**: El `bitnin-shadow.timer` dispara sucesivas ejecuciones (`tick`), pero el supervisor muere inmediatamente bloqueado `LOCK BUSY`.
- **Detección**: El `health_snapshot.md` marca un estatus de `STALE_DATA` y/o un retraso mayor al _tick_ estimado.
- **Mitigación**: El humano requiere la consola y dispara `bitnin-ctl doctor`, la cual remueve el lock muerto.
- **Riesgo**: Operación nula garantizada sin supervisión humana. Esta falla invalida el Uptime de automatización y penaliza duramente para un Promotion Gate.

### `F-OPS-02: execution_guard_leak` (Riesgo Teórico Severo)
- **Síntoma Visible**: Intentos financieros filtrados a infraestructura conectada.
- **Impacto**: Operación no autorizada de fondos bajo fase inapropiada (`29R`).
- **Detección**: En el sistema existente (v1), las variables de simulación de `exec-guard` operan con interfaces "mock" locales a directorios JSON (eg. `runtime/execution/`).
- **Mitigación**: Si esta capa de persistencia simulada cambiase accidentalmente sus punteros reales... el blindaje desaparece. No hay salvaguardas explícitamente duras (A nivel SO) bloqueando HTTP out a un exchange real, solo una flag de código. No certificado bajo auditoría externa.

## 4. Capa de Gobernanza Analógica (HITL)

### `F-GOV-01: hitl_case_expiry`
- **Síntoma Visible**: `hitl_inbox.md` se rebalsa de colas sin resolver porque el humano abandonó su puesto.
- **Impacto**: Los status migran a `EXPIRED` progresivamente.
- **Mitigación**: El caso cesa. El scorecard agrupa fallos de operatividad humana degradando la confiabilidad institucional. A nivel software, es equivalente a `rejected` (no trade occur).

### `F-GOV-02: ledger_corruption`
- **Síntoma Visible**: `weekly_review_state.json` mal parseado por edición humana manual ajena al CLI.
- **Impacto**: Imposibilidad de restaurar _Week Review_ con fidelidad temporal.
- **Detección**: Script falla la parseo o el _doctor_ advierte inconsistencias.
- **Mitigación**: Ejecutar un restore canónico extraído del empaquetado `ops_restore.sh`.
