# BitNin Architecture Map

## Mapa Estructural del Sistema

### 1. El Analista (`bitnin_analyst`)
- **Rol**: Evalúa el mercado contra la memoria RAG para emitir `analysis_output` con una Señal Compuesta.
- **Relaciones**: Consume de `bitnin_active_memory`, asiste pasivamente sin tomar acciones de ejecución.

### 2. Memoria Activa (`bitnin_active_memory` / Qdrant)
- **Rol**: Subsistema de retrieval (`localhost:6333`).
- **Artefactos**: Colección `bitnin_episodes` (Vectores reales Nomic-Embed de dimensión 768). Base esencial del modelo RAG local para analogías históricas.

### 3. Señal Compuesta
- **Rol**: La métrica sintética de convergencia que combina inputs de mercado vs. soporte narrativo.
- **Validación**: Sometida a monitoreo para evitar devaluación silenciosa y _drift_ narrativo histórico.

### 4. Supervisor (`bitnin_supervisor`)
- **Rol**: Orquestador resiliente gestionado por `systemd`. Mantiene freshness, asegura la continuidad y ejecuta el pipeline _shielded_ mediante `bitnin_supervisor.lock`.

### 5. Observabilidad (`observability`)
- **Rol**: Genera el diagnóstico analítico longitudinal.
- **Artefactos**: Detecta `DEGRADATION` y `DRIFT`. Genera _Batch Reports_ diarios y el _Health Snapshot_.

### 6. HITL (Human in the Loop)
- **Rol**: Actúa como atajador final de intenciones bloqueadas (`bitnin-exec-guard`). Requiere revisión manual y registra en timeline inmutable dictámenes como `approved`, `rejected` o `escalated`.

### 7. Consola Operativa (`bitnin-ctl`)
- **Rol**: El _entrypoint_ canónico único del operador humano. Wrapper absoluto para evitar fallos de PYTHONPATH.
- **Interacción**: Expone herramientas de cierre, lectura de salud y revisión periódica.

### 8. Scheduler
- **Rol**: Cron de sistema operativo independiente del IDE/sesión (`systemd --user bitnin-shadow.timer`). Otorga determinismo y ejecución de fondo.
- **Relación**: Ejecuta el `supervisor`.

### 9. Backup / Restore
- **Rol**: scripts (`ops_backup.sh`, `ops_restore.sh`) para migrar o asegurar los casos humanos, logs de observabilidad y ledger. Base de la declaración de portabilidad.

### 10. Gobernanza
- **Rol**: Infraestructura estricta de revisión semanal. Archiva _weekly_scorecards.md_, _ledgers_ emite fallos de promoción o contención de fase, evitando que BitNin sea promovido a _Pilot_ sin evidencias cronológicas irrefutables (Semana corriente: 29R).
