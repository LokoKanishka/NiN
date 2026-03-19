# BitNin Operator Command Map

Este mapa consolida las herramientas de línea de comandos (_CLI_) disponibles para el operador de BitNin, clasificadas por su propósito operativo cotidiano o estructural.

*(Regla de Invocación Segura: siempre ejecutar desde la raíz `/home/lucy-ubuntu/Escritorio/NIN` sin emplear `bash -lc` en automatizaciones).*

## 🩺 Salud y Monitoreo

### `bitnin-ctl status`
- **Qué hace**: Evalúa la condición general. Muestra salud del sistema, estatus del scheduler y tamaño del backlog.
- **Cuándo usarlo**: Al iniciar turno o tras sospecha de inactividad.
- **Artefactos**: Accede por lectura a `health_snapshot.md`, `hitl_state.json` y a systemd. No modifica nada.

### `bitnin-ctl doctor`
- **Qué hace**: Corre diagnóstico profundo. Detecta inconsistencias de permisos, binarios faltantes, y desconfiguración del entorno (ej: `bitnin_supervisor.lock` muerto, dependencias).
- **Cuándo usarlo**: Cuando el scheduler falle o tras migración.
- **Riesgos**: Ninguno (solo lectura).

### `bitnin-ctl briefing`
- **Qué hace**: Emite un resumen ejecutivo (_Briefing Diario_) listando qué casos HITL requieren atención primaria priorizada por _severity_.
- **Asociado**: Extrae de `hitl_briefing.md` actualizado en cada tick.

## 📥 HITL (Gestión de Casos)

Las decisiones de revisión (HITL) se manejan sobre `bitnin-ctl hitl`.

### `bitnin-ctl hitl review <case_id> [--decision stable|escalate|...]`
- **Qué hace**: Aplica un veredicto humano.
- **Riesgos**: Asienta irreversiblemente una decisión en el timeline de ese caso.
- **Artefactos**: Modifica el `hitl_state.json` y actualiza los buzones MD dinámicos (`hitl_inbox.md`, `hitl_archive.md`). 

## 🌙 Gobernanza Continua

### `bitnin-ctl day-close`
- **Qué hace**: Ritual Diario. Crea una bitácora con todas las acciones HITL hechas hoy, compila un _bundle_ (carpeta `daily_bundles/YYYY-MM-DD/`) y limpia el entorno día.
- **Cuándo usarlo**: Final de turno.
- **Advertencias**: Asegura que el trabajo del operador quedó asentado y consolidado. Fomenta auditoría limpia.

### `bitnin-ctl week-review`
- **Qué hace**: Extrae el `weekly_scorecard.md`, compila las 7 jornadas y agrupa KPI operativos, analíticos y de actividad humana en `weekly_reviews/YYYY-WW/`. 
- **Cuándo usarlo**: Cada Lunes (Rutina semanal).
- **Limitaciones**: Elabora evidencia en crudo; no muta el ledger por sí mismo.

### `bitnin-ctl week-close --week <YYYY-WW> --decision <stable> --note "..."`
- **Qué hace**: Cierre de ciclo. Toma el _week-review_ compilado, y sobre esa evaluación de scorecard, añade la resolución humana final de dicha semana al inmutable _Ledger_ (`weekly_review_state.json`).
- **Riesgos**: Cierra oficial y contablemente la evidencia cronológica. Necesaria (en dictámenes _stable_) para la promoción de fase.

## 🛠️ Scheduler y Setup 

### `scripts/scheduler_ctl.sh [status|install|restart]`
- **Qué hace**: Instalación y encendido de la tubería automática (`bitnin-shadow.timer` vía `systemd --user`).
- **Cuándo usarlo**: Cambios de host (`bootstrap`) o fallos críticos del timer.

### `scripts/ops_backup.sh` / `ops_restore.sh <archivo>`
- **Qué hace**: Mueve únicamente el **plano de gestión humana** e historial inmutable. `bitnin_state.json` no requiere backing, pero resoluciones y scorecards sí. Produce / extrae `.tar.gz`.
- **Riesgos `restore`**: Destruye estado volátil actual de `observability/history` en pos del volcado empírico restaurado. Usar solo en recuperación DR.
