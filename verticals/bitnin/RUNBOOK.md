# BitNin Operational Runbook - Shadow Mode

## 1. Introduction
This document describes the operations for BitNin in `shadow + dry_run` mode. BitNin is currently in an analytical observation phase, focused on validating its composite signal and causal reasoning without financial execution.

## 2. Daily Operations
The system is designed to run periodically via the supervisor.

### Installation (First Time setup)
To register BitNin as a background service on this host:
```bash
# 1. Create systemd user directory if it doesn't exist
mkdir -p ~/.config/systemd/user/

# 2. Copy unit files from the repository
cp verticals/bitnin/services/bitnin_observability/systemd/bitnin-shadow.service ~/.config/systemd/user/
cp verticals/bitnin/services/bitnin_observability/systemd/bitnin-shadow.timer ~/.config/systemd/user/

# 3. Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now bitnin-shadow.timer

# 4. Enable Linger (to survive logout/reboot)
loginctl enable-linger lucy-ubuntu
```

### Persistence & Session Management
BitNin is configured to run as a user service. To ensure it survives server reboots and user logouts, we use `loginctl enable-linger`. This allows the user's `systemd` manager to start at boot and stay running after the user logs out.

### Starting the Supervisor (Automated)
BitNin runs automatically via systemd. To manage the service:
```bash
# View if the timer is scheduled
systemctl --user list-timers bitnin-shadow.timer

# View service/timer status
systemctl --user status bitnin-shadow.timer
systemctl --user status bitnin-shadow.service

# View real-time logs (very useful for diagnostics)
journalctl --user -u bitnin-shadow.service -f

# Force immediate execution
systemctl --user start bitnin-shadow.service
```

### Checking System Health
Inspect the human-readable snapshot for a quick status overview:
`verticals/bitnin/runtime/observability/history/health_snapshot.md`

## 🕹️ Ritual de Cierre de Jornada
Para asegurar una bitácora profesional y auditable, el operador debe ejecutar el comando de cierre al finalizar su turno:

```bash
./bitnin_ctl.py day-close
```

**Este comando realiza:**
1. **Generación de Bitácora**: Crea `operator_journal.md` con todas las decisiones tomadas en las últimas 24h.
2. **Archivado de Bundle**: Mueve el briefing, la bitácora y el estado de salud a `runtime/observability/history/daily_bundles/YYYY-MM-DD/`.
3. **Resumen de Actividad**: Muestra en consola qué expedientes se cerraron y qué queda pendiente.

---

---

## 🛠️ Mantenimiento Institucional & Resiliencia
A partir de la Fase 25, BitNin cuenta con herramientas de infraestructura profesional.

### 1. Diagnóstico de Salud Técnica (Doctor)
Si algo no parece funcionar bien, corra el diagnóstico:
```bash
./bin/bitnin-ctl doctor
```

### 2. Gestión del Scheduler
Evite la configuración manual de systemd. Use el controlador oficial:
```bash
./scripts/scheduler_ctl.sh status      # Ver estado
./scripts/scheduler_ctl.sh restart     # Forzar reinicio
./scripts/scheduler_ctl.sh install     # Reinstalar units
```

### 3. Continuidad Operativa (Backup/Restore)
Para migrar o respaldar el plano de gestión humana (casos y estados):
- **Backup**: `./scripts/ops_backup.sh` (Genera un tarball en `backups/`)
- **Restore**: `./scripts/ops_restore.sh <archivo>`

### 4. Bootstrap (Reinstalación)
En un entorno nuevo o tras una limpieza de runtime:
```bash
./scripts/bootstrap.sh
```

---

## 🏛️ Gobernanza & Supervisión Semanal
BitNin opera bajo un marco de gobierno institucional que asegura la calidad y estabilidad del modo Shadow.

### 1. KPIs Oficiales
- **Operativos**: Uptime del scheduler (>98%) y éxito del backup.
- **Analíticos**: Cobertura narrativa y estabilidad de la señal compuesta.
- **Humanos**: Control del backlog HITL (< 5 casos).

### 2. Ritual de Revisión Semanal
Cada lunes (o al inicio de la semana operativa), el operador debe capturar el paquete semanal sin inventar ni simular evidencia:

1. **Generar Paquete**: Ejecutar `./bin/bitnin-ctl week-review`. Este comando generará una carpeta en `verticals/bitnin/runtime/observability/history/weekly_reviews/YYYY-WW/` con toda la evidencia real.
2. **Revisar Evidencias**: Leer `weekly_scorecard.md`, el número real de incidentes y el backlog.
3. **Completar Nota**: Editar `pilot_readiness_week_note.md` generado en el paquete y marcar el veredicto real (`stable`, `watch`, o `investigate`). Añadir observaciones cualitativas, **pero nunca inventar métricas**.
4. **Cerrar la Semana**: Asentar la decisión formalmente en el ledger inmutable:
   ```bash
   ./bin/bitnin-ctl week-close --week YYYY-WW --decision stable --note "Todo normal, backlog en cero."
   ```
   *Esto generará un registro en `weekly_review_state.json` y actualizará `weekly_review_history.md`.*
5. **IMPORTANTE**: Este ritual archiva el estado actual y asienta el ledger, pero **no** habilita Pilot automáticamente. Se requieren 4 cierres exitosos (decisión `stable`) consecutivos.

### 3. Promotion Gate (Hacia Pilot)
La promoción a fase Pilot requiere 4 semanas consecutivas de "Salud Verde" y cumplimiento total de KPIs operativos.

---

### Internal State
The internal state is kept in `operational_state.json` (ignored by git) to ensure no runtime noise contaminates the repository.

## 3. Interpreting Alerts
... (keeping previous alerts) ...

## 5. Maintenance & Clean Runtime
- **Git Hygiene:** Never force-add `operational_state.json` or `*.lock` files to git.
- **Housekeeping:** Batch reports in `runtime/observability/batches/` can be archived or deleted periodically. Scorecards in `scorecards/` should be kept for audit.
- **Snapshot Monitoring:** `health_snapshot.md` is the primary source of truth for humans; if it reports `DEGRADED`, check the scorecards for details.

### 🔴 DEGRADATION (Narrative)
**Meaning:** The analyst has access to very few narrative events (< 0.2 score).
**Action:** Check if the GDELT pipeline is stuck or if the `normalized` dataset path is correctly configured.

### 🔴 DEGRADATION (Memory)
**Meaning:** No active memories are being retrieved from Qdrant.
**Action:** Verify Qdrant service is running at `http://localhost:6333` and that the `bitnin_episodes` collection has points.

### 🟡 DRIFT
**Meaning:** A sudden shift in metric distributions (e.g., a 50% drop in narrative support compared to yesterday).
**Action:** Review the latest scorecard in `verticals/bitnin/runtime/observability/scorecards/` to identify the source of the shift.

## 4. Recovery & Resume
The supervisor uses a lockfile (`bitnin_supervisor.lock`) to prevent concurrent runs.

### If a run fails:
1. Check logs for the specific `as_of` date that crashed.
2. The supervisor will automatically attempt to resume from the last successful date on the next invocation.
3. If a stale lock exists after a crash, the supervisor will remove it automatically.

### Incident Response (Stale Process)
If BitNin fails to process or stays "STALE":
1. **Check Freshness**: If `health_snapshot.md` shows `STALE`, the timer might be dead or the process hung.
2. **Check Dead Locks**: If the service fails to start with "Execution blocked", check for stale locks. The supervisor handles most cases, but manual cleanup can be done:
   ```bash
   rm verticals/bitnin/runtime/observability/history/bitnin_supervisor.lock
   ```
3. **Journal Audit**: Use `journalctl --user -u bitnin-shadow.service -n 100`.

## 5. Safety Guardrails
- **NEVER** disable `shadow_mode` or `dry_run` flags.
- BitNin has no access to private keys or API keys for trading.
- All "orders" generated are for audit purposes only and are archived in `runtime/shadow/`.
