# BitNin Recovery Map

BitNin está certificado bajo portabilidad `Clean-Room Deployment` y recuperación de desastres (`Disaster Recovery Drill` — RC Shadow Fase 26).

## 🛡️ Topología de Supervivencia

### 1. Reconstrucción Clean-Room (Bootstrap)
- **Operación**: `./scripts/bootstrap.sh`
- **Qué hace**: Asegura y recompila las instalaciones de dependencias, permisos ejecutables y el `virtual environment` interno (`.venv/`) ignorando qué host lo esté encendiendo. Prepara las carpetas de log y state que `.gitignore` excluyó intencionadamente o impidió crear durante el clonado.

### 2. Reconexión de Timer (Scheduler Install)
- **Operación**: `./scripts/scheduler_ctl.sh install` 
- **Qué hace**: Copia al host en `~/.config/systemd/user/` los archvos de timer y units que habilitarán el supervisor automático. Corre el `daemon-reload` y reconecta el cron del subsistema tras migración. (Incluye requerimiento de loginctl `linger`).

### 3. Recuperación del Plano Humano (Restore)
- **Operación**: `./scripts/ops_restore.sh <backup_tarball>`
- **Qué Hace**: Un backup previamente extraído con `ops_backup.sh` contiene la médula inmaterial de auditorías (`hitl_state.json`, `ledgers`, `daily_bundles`).
- **Límite**: La restauración asume la desaparición absoluta de la carpeta de observability en el host dañado e implanta las decisiones humanas rescatadas, reintegra la historia longitudinal y le dice de inmediato al `hitl_inbox.md` y `health.md` en qué estado quedó antes del evento desastroso.

### 4. Post-Recuperación y Puesta a Cero (Diagnóstico Doctor)
- **Operación**: `./bin/bitnin-ctl doctor`
- **Qué hace**: Evalúa si los pasos 1, 2 y 3 no colisionan. Asegura que el PATH no esté sucio por shells en `.profile`, valida los permisos, la conexión del timer re-instalado y que los _State JSONs_ leídos por el restore tengan parseo válido.

## 🏁 Alcance Certificado
La certificación que permite llamar a esta fase `GA-SHADOW` no infiere exactitud predictiva de su Señal Compuesta (`composite signal`); solo confiere garantía contundente de su **continuidad determinista operativa**. 

El sistema probó sobrevivir por sus propios medios sin reconstrucciones manuales esotéricas o scripts a medida y _admitió ser trasladado a otro host Linux sin pérdida de control logístico humano_.
